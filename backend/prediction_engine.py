import numpy as np
import pandas as pd
import tensorflow as tf
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression, Ridge
from typing import Tuple, Dict, Any, Optional

from backend.config import FEATURES

def prepare_lstm_data(
    df: pd.DataFrame, 
    seq_length: int, 
    scaler_x: Optional[MinMaxScaler] = None, 
    scaler_y: Optional[MinMaxScaler] = None
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler, Optional[MinMaxScaler]]:
    """
    Scales the data and creates sequences for LSTM training.
    Features: RSI, MACD, MACD_Signal, MACD_Hist, Open, Close, Volume, High, Low, BB_Upper, BB_Lower, BB_Width, EMA_20, EMA_50, ATR, Daily_Return
    Target: Binary direction (1 if return > 0, else 0)
    """
    features = FEATURES
    feature_data = df[features].values
    target_data = (df["Daily_Return"] > 0).astype(int).values
    
    # Normalize features only
    if scaler_x is None:
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaled_x = scaler_x.fit_transform(feature_data)
    else:
        scaled_x = scaler_x.transform(feature_data)
        
    scaled_y = target_data
    
    x_seq, y_val = [], []
    for i in range(seq_length, len(scaled_x)):
        x_seq.append(scaled_x[i-seq_length:i])
        y_val.append(scaled_y[i])
        
    return np.array(x_seq), np.array(y_val), scaler_x, None

def train_lstm_model(
    x_train: np.ndarray, 
    y_train: np.ndarray, 
    seq_length: int, 
    validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
) -> tf.keras.Model:
    """Creates and trains an LSTM model for binary classification."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
        tf.keras.layers.LSTM(units=50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(units=25, activation="relu"),
        tf.keras.layers.Dense(units=1, activation="sigmoid")
    ])
    
    model.compile(optimizer="adam", loss="binary_crossentropy")
    
    callbacks = []
    if validation_data is not None:
        callbacks.append(tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=7,
            restore_best_weights=True
        ))
        epochs = 80
    else:
        epochs = 30
        
    model.fit(
        x_train, 
        y_train, 
        epochs=epochs, 
        batch_size=32, 
        validation_data=validation_data, 
        callbacks=callbacks, 
        verbose=0
    )
    return model

def evaluate_model_performance(
    model: tf.keras.Model, 
    x_test: np.ndarray, 
    y_test: np.ndarray, 
    scaler_y: Any, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates LSTM predictions on a test set.
    Computes Log-Loss and Directional Accuracy.
    """
    if len(x_test) == 0 or len(y_test) == 0:
        return {"logloss": 9.99, "directional_accuracy": 50.0}
        
    probs = model.predict(x_test, verbose=0).flatten()
    probs = np.clip(probs, 1e-15, 1 - 1e-15)
    
    logloss = -np.mean(y_test * np.log(probs) + (1 - y_test) * np.log(1 - probs))
    preds_dir = (probs >= 0.5).astype(int)
    correct_directions = np.sum(preds_dir == y_test)
    dir_acc = (correct_directions / len(y_test) * 100) if len(y_test) > 0 else 50.0
    
    return {
        "logloss": float(logloss),
        "directional_accuracy": float(dir_acc)
    }

def evaluate_xgb_performance(
    model: Any, 
    x_test: np.ndarray, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates XGBoost predictions on a test set.
    Computes Log-Loss and Directional Accuracy.
    """
    actual_returns = df_test["Daily_Return"].values[seq_length:]
    y_test = (actual_returns > 0).astype(int)
    
    if len(x_test) == 0 or len(y_test) == 0:
        return {"logloss": 9.99, "directional_accuracy": 50.0}
        
    try:
        probs = model.predict_proba(x_test)[:, 1]
    except Exception:
        probs = np.zeros(len(x_test)) + 0.5
        
    probs = np.clip(probs, 1e-15, 1 - 1e-15)
    
    logloss = -np.mean(y_test * np.log(probs) + (1 - y_test) * np.log(1 - probs))
    preds_dir = (probs >= 0.5).astype(int)
    correct_directions = np.sum(preds_dir == y_test)
    dir_acc = (correct_directions / len(y_test) * 100) if len(y_test) > 0 else 50.0
    
    return {
        "logloss": float(logloss),
        "directional_accuracy": float(dir_acc)
    }

def train_lr_model(x_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """Trains a stable Logistic Regression model."""
    if not np.array_equal(y_train, y_train.astype(bool)):
        y_train = (y_train > 0).astype(int)
    model = LogisticRegression(C=0.01, random_state=42)
    model.fit(x_train, y_train)
    return model

def evaluate_lr_performance(
    model: Any, 
    x_test: np.ndarray, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates Logistic Regression predictions on a test set.
    Computes Log-Loss and Directional Accuracy.
    """
    actual_returns = df_test["Daily_Return"].values[seq_length:]
    y_test = (actual_returns > 0).astype(int)
    
    if len(x_test) == 0 or len(y_test) == 0:
        return {"logloss": 9.99, "directional_accuracy": 50.0}
        
    try:
        probs = model.predict_proba(x_test)[:, 1]
    except Exception:
        probs = np.zeros(len(x_test)) + 0.5
        
    probs = np.clip(probs, 1e-15, 1 - 1e-15)
    
    logloss = -np.mean(y_test * np.log(probs) + (1 - y_test) * np.log(1 - probs))
    preds_dir = (probs >= 0.5).astype(int)
    correct_directions = np.sum(preds_dir == y_test)
    dir_acc = (correct_directions / len(y_test) * 100) if len(y_test) > 0 else 50.0
    
    return {
        "logloss": float(logloss),
        "directional_accuracy": float(dir_acc)
    }
