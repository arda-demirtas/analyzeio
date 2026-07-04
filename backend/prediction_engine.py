import numpy as np
import pandas as pd
import tensorflow as tf
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from typing import Tuple, Dict, Any, Optional

from backend.config import FEATURES

def prepare_lstm_data(
    df: pd.DataFrame, 
    seq_length: int, 
    scaler_x: Optional[MinMaxScaler] = None, 
    scaler_y: Optional[MinMaxScaler] = None
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler, MinMaxScaler]:
    """
    Scales the data and creates sequences for LSTM training.
    Features: RSI, MACD, MACD_Signal, MACD_Hist, Open, Close, Volume, High, Low, BB_Upper, BB_Lower, BB_Width, EMA_20, EMA_50, ATR, Daily_Return
    Target: Daily_Return
    """
    features = FEATURES
    feature_data = df[features].values
    target_data = df[["Daily_Return"]].values
    
    # Normalize features and target separately
    if scaler_x is None:
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaled_x = scaler_x.fit_transform(feature_data)
    else:
        scaled_x = scaler_x.transform(feature_data)
        
    if scaler_y is None:
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        scaled_y = scaler_y.fit_transform(target_data)
    else:
        scaled_y = scaler_y.transform(target_data)
    
    x_seq, y_val = [], []
    for i in range(seq_length, len(scaled_x)):
        x_seq.append(scaled_x[i-seq_length:i])
        y_val.append(scaled_y[i])
        
    return np.array(x_seq), np.array(y_val), scaler_x, scaler_y

def train_lstm_model(
    x_train: np.ndarray, 
    y_train: np.ndarray, 
    seq_length: int, 
    validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None
) -> tf.keras.Model:
    """Creates and trains an LSTM model with Dropout regularization."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
        tf.keras.layers.LSTM(units=50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(units=25, activation="relu"),
        tf.keras.layers.Dense(units=1)
    ])
    
    model.compile(optimizer="adam", loss="mean_squared_error")
    
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
    scaler_y: MinMaxScaler, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates LSTM predictions on a test set.
    Computes RMSE, MAPE, and Directional Accuracy.
    """
    if len(x_test) == 0:
        return {"rmse": 0.0, "mape": 0.0, "directional_accuracy": 0.0}
        
    scaled_preds = model.predict(x_test, verbose=0)
    preds_returns = scaler_y.inverse_transform(scaled_preds).flatten()
    actual_returns = scaler_y.inverse_transform(y_test).flatten()
    
    # Reconstruct absolute close prices from return predictions
    actual_prices = df_test["Close"].values[seq_length:]
    prev_prices = df_test["Close"].values[seq_length-1:-1]
    
    preds = prev_prices * (1 + preds_returns)
    actuals = actual_prices
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    
    # Calculate MAPE
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-10))) * 100
    
    # Calculate Directional Accuracy using returns directly
    correct_directions = 0
    total_comparisons = len(preds_returns)
    
    for i in range(total_comparisons):
        actual_up = actual_returns[i] > 0
        pred_up = preds_returns[i] > 0
        if actual_up == pred_up:
            correct_directions += 1
            
    dir_acc = (correct_directions / total_comparisons * 100) if total_comparisons > 0 else 50.0
    
    return {
        "rmse": float(rmse),
        "mape": float(mape),
        "directional_accuracy": float(dir_acc)
    }

def evaluate_xgb_performance(
    model: xgb.XGBRegressor, 
    x_test: np.ndarray, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates XGBoost predictions on a test set.
    Computes RMSE, MAPE, and Directional Accuracy.
    """
    if len(x_test) == 0:
        return {"rmse": 0.0, "mape": 0.0, "directional_accuracy": 0.0}
        
    preds_returns = model.predict(x_test).flatten()
    actual_prices = df_test["Close"].values[seq_length:]
    prev_prices = df_test["Close"].values[seq_length-1:-1]
    actual_returns = df_test["Daily_Return"].values[seq_length:]
    
    preds = prev_prices * (1 + preds_returns)
    actuals = actual_prices
    
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-10))) * 100
    
    correct_directions = 0
    total_comparisons = len(preds_returns)
    
    for i in range(total_comparisons):
        actual_up = actual_returns[i] > 0
        pred_up = preds_returns[i] > 0
        if actual_up == pred_up:
            correct_directions += 1
            
    dir_acc = (correct_directions / total_comparisons * 100) if total_comparisons > 0 else 50.0
    
    return {
        "rmse": float(rmse),
        "mape": float(mape),
        "directional_accuracy": float(dir_acc)
    }

def train_lr_model(x_train: np.ndarray, y_train: np.ndarray) -> LinearRegression:
    """Trains a simple Linear Regression model."""
    model = LinearRegression()
    model.fit(x_train, y_train)
    return model

def evaluate_lr_performance(
    model: LinearRegression, 
    x_test: np.ndarray, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates Linear Regression predictions on a test set.
    Computes RMSE, MAPE, and Directional Accuracy.
    """
    if len(x_test) == 0:
        return {"rmse": 0.0, "mape": 0.0, "directional_accuracy": 0.0}
        
    preds_returns = model.predict(x_test).flatten()
    actual_prices = df_test["Close"].values[seq_length:]
    prev_prices = df_test["Close"].values[seq_length-1:-1]
    actual_returns = df_test["Daily_Return"].values[seq_length:]
    
    preds = prev_prices * (1 + preds_returns)
    actuals = actual_prices
    
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-10))) * 100
    
    correct_directions = 0
    total_comparisons = len(preds_returns)
    
    for i in range(total_comparisons):
        actual_up = actual_returns[i] > 0
        pred_up = preds_returns[i] > 0
        if actual_up == pred_up:
            correct_directions += 1
            
    dir_acc = (correct_directions / total_comparisons * 100) if total_comparisons > 0 else 50.0
    
    return {
        "rmse": float(rmse),
        "mape": float(mape),
        "directional_accuracy": float(dir_acc)
    }

