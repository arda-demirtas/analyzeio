import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import StandardScaler

# Ensure print outputs are encoded correctly for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set python path to find backend modules
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data

# Filtered/recommended features (relative indicators only, raw price levels removed)
RECOMMENDED_FEATURES = [
    "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
    "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
    "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag7"
]

print("TensorFlow Version:", tf.__version__)
print("Using Recommended Features:", RECOMMENDED_FEATURES)

# ----------------------------------------------------
# 1. Custom PatchTST Model with Channel Independence
# ----------------------------------------------------

class MultivariatePatchTSTModel(Model):
    def __init__(self, seq_len, num_features, patch_len, stride, d_model, num_heads, num_layers, ff_dim, dropout=0.1):
        super(MultivariatePatchTSTModel, self).__init__()
        self.seq_len = seq_len
        self.num_features = num_features
        self.patch_len = patch_len
        self.stride = stride
        self.d_model = d_model
        
        # Number of patches calculation
        self.num_patches = (seq_len - patch_len) // stride + 1
        
        # Patch projection layer (shared across channels)
        self.patch_proj = layers.Dense(d_model)
        
        # Position embedding (shared across channels)
        self.pos_emb = self.add_weight(
            name="pos_emb",
            shape=(1, self.num_patches, d_model),
            initializer="random_normal",
            trainable=True
        )
        
        # Transformer Encoder Blocks (shared weights across channels)
        self.enc_blocks = []
        for _ in range(num_layers):
            self.enc_blocks.append({
                "mha": layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model // num_heads),
                "norm1": layers.LayerNormalization(epsilon=1e-6),
                "drop1": layers.Dropout(dropout),
                "ffn1": layers.Dense(ff_dim, activation="gelu"),
                "ffn2": layers.Dense(d_model),
                "norm2": layers.LayerNormalization(epsilon=1e-6),
                "drop2": layers.Dropout(dropout)
            })
            
        # Output prediction head
        self.flatten = layers.Flatten()
        self.dropout_head = layers.Dropout(dropout)
        self.head = layers.Dense(1) # Predict next day percentage return

    def call(self, x, training=False):
        batch_size = tf.shape(x)[0]
        
        # Channel Independence
        # (batch, seq_len, M) -> (batch, M, seq_len) -> (batch * M, seq_len, 1)
        x_trans = tf.transpose(x, perm=[0, 2, 1])
        x_flat_channel = tf.reshape(x_trans, [batch_size * self.num_features, self.seq_len, 1])
        
        # Patching
        patches = []
        for i in range(self.num_patches):
            start = i * self.stride
            end = start + self.patch_len
            patches.append(x_flat_channel[:, start:end, 0])
        
        x_patched = tf.stack(patches, axis=1) # (batch * M, num_patches, patch_len)
        
        # Projection & Position Embedding
        x_proj = self.patch_proj(x_patched) # (batch * M, num_patches, d_model)
        x_proj = x_proj + self.pos_emb
        
        # Transformer Encoder
        enc_out = x_proj
        for block in self.enc_blocks:
            attn_out = block["mha"](enc_out, enc_out, training=training)
            attn_out = block["drop1"](attn_out, training=training)
            x1 = block["norm1"](enc_out + attn_out)
            
            ffn_out = block["ffn1"](x1)
            ffn_out = block["ffn2"](ffn_out)
            ffn_out = block["drop2"](ffn_out, training=training)
            enc_out = block["norm2"](x1 + ffn_out)
            
        # Reshape back to channels -> (batch, M, num_patches, d_model)
        enc_out_trans = tf.reshape(enc_out, [batch_size, self.num_features, self.num_patches, self.d_model])
        
        # Flatten and Head
        flat = self.flatten(enc_out_trans)
        flat = self.dropout_head(flat, training=training)
        pred = self.head(flat) # (batch, 1) -> predicts next day Daily_Return
        return pred

# ----------------------------------------------------
# 2. Fetch and Prepare BTC-USD Data
# ----------------------------------------------------

print("\nFetching BTC-USD historical data & computing indicators...")
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")
print(f"Data fetched and processed: {len(df)} rows.")

# Extract 13 recommended feature columns
features_data = df[RECOMMENDED_FEATURES].values
close_prices = df["Close"].values.reshape(-1, 1)
daily_returns = df["Daily_Return"].values.reshape(-1, 1)

# Sequence length configuration
seq_len = 64
patch_len = 16
stride = 8

# Create sequences
X, y_return, y_close_target, prev_close_val = [], [], [], []
for i in range(seq_len, len(df)):
    X.append(features_data[i - seq_len : i])
    # Target is next day's Daily_Return
    y_return.append(daily_returns[i][0])
    # Target actual close price (for evaluation)
    y_close_target.append(close_prices[i][0])
    # Previous day's close (to reconstruct actual close price from return)
    prev_close_val.append(close_prices[i-1][0])

X = np.array(X) # (N, seq_len, 13)
y_return = np.array(y_return).reshape(-1, 1) # (N, 1)
y_close_target = np.array(y_close_target).reshape(-1, 1) # (N, 1)
prev_close_val = np.array(prev_close_val).reshape(-1, 1) # (N, 1)

# Split into Train and Test sets (80% - 20%)
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_return_train, y_return_test = y_return[:split_idx], y_return[split_idx:]
y_close_test, prev_close_test = y_close_target[split_idx:], prev_close_val[split_idx:]

# Scalers
scaler_x = StandardScaler()
scaler_y = StandardScaler()

# Fit and transform
X_train_shape = X_train.shape
X_test_shape = X_test.shape

X_train_scaled = scaler_x.fit_transform(X_train.reshape(-1, 13)).reshape(X_train_shape)
X_test_scaled = scaler_x.transform(X_test.reshape(-1, 13)).reshape(X_test_shape)

y_return_train_scaled = scaler_y.fit_transform(y_return_train)
y_return_test_scaled = scaler_y.transform(y_return_test)

print(f"X_train shape: {X_train_scaled.shape}, y_return_train shape: {y_return_train_scaled.shape}")
print(f"X_test shape: {X_test_scaled.shape}, y_return_test shape: {y_return_test_scaled.shape}")

# ----------------------------------------------------
# 3. Model Training
# ----------------------------------------------------

# Instantiate custom Multivariate PatchTST model
model = MultivariatePatchTSTModel(
    seq_len=seq_len,
    num_features=len(RECOMMENDED_FEATURES),
    patch_len=patch_len,
    stride=stride,
    d_model=32,
    num_heads=4,
    num_layers=2,
    ff_dim=64,
    dropout=0.1
)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="mse"
)

print("\nTraining Recommended-Indicator PatchTST Model for 15 epochs...")
model.fit(
    X_train_scaled, y_return_train_scaled,
    epochs=15,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)

# ----------------------------------------------------
# 4. Evaluation and Prediction
# ----------------------------------------------------

print("\nEvaluating model on test set...")
preds_return_scaled = model.predict(X_test_scaled)
preds_return = scaler_y.inverse_transform(preds_return_scaled)

# Reconstruct predicted Close Prices: Close_t = Close_{t-1} * (1 + Return_t)
preds_close = prev_close_test * (1 + preds_return)

# Metrics on reconstructed Close Prices
rmse = np.sqrt(np.mean((preds_close - y_close_test) ** 2))
mape = np.mean(np.abs((y_close_test - preds_close) / y_close_test)) * 100

# Directional Accuracy (DA) on predicted close direction
actual_direction = np.sign(y_close_test[1:] - y_close_test[:-1])
pred_direction = np.sign(preds_close[1:] - y_close_test[:-1])
directional_accuracy = np.mean(actual_direction == pred_direction) * 100

print("\n--- Optimized PatchTST Test Performance Results ---")
print(f"Test RMSE: {rmse:.2f}")
print(f"Test MAPE: {mape:.2f}%")
print(f"Directional Accuracy: {directional_accuracy:.2f}%")

# Generate next close prediction
last_seq = features_data[-seq_len:]
last_seq_scaled = scaler_x.transform(last_seq.reshape(-1, 13)).reshape(1, seq_len, 13)
next_return_scaled = model.predict(last_seq_scaled)
next_return = scaler_y.inverse_transform(next_return_scaled)[0][0]

last_actual_price = close_prices[-1][0]
next_pred = last_actual_price * (1 + next_return)
price_diff = next_pred - last_actual_price
pct_change = next_return * 100

print("\n--- Next Close Prediction (BTC-USD) ---")
print(f"Last Actual Price: ${last_actual_price:.2f}")
print(f"Optimized PatchTST Predicted Next Close Price: ${next_pred:.2f}")
print(f"Expected Price Change: ${price_diff:+.2f} ({pct_change:+.2f}%)")
print(f"Market Sentiment Recommendation: {'BULLISH (LONG)' if pct_change >= 0 else 'BEARISH (SHORT)'}")
