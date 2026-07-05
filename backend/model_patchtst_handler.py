import numpy as np
from typing import Tuple, Dict, Any, Optional
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

def get_patchtst_prediction(
    symbol: str,
    interval: str,
    df,
    df_train,
    df_test,
    seq_length: int,
    force_retrain: bool,
    is_daemon: bool,
    max_ret: float,
    min_ret: float
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """Runs the PatchTST simulation flow to predict next close price and return performance metrics."""
    patchtst_predicted_close = None
    patchtst_metrics = None
    
    try:
        tst_features = [
            "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
            "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
            "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag7"
        ]
        existing_tst_features = [f for f in tst_features if f in df.columns]
        df_clean = df.dropna(subset=existing_tst_features + ["Daily_Return"])

        split_idx_tst = int(len(df_clean) * 0.8)
        df_train_tst = df_clean.iloc[:split_idx_tst]
        df_test_tst = df_clean.iloc[split_idx_tst:]

        X_train_tst = df_train_tst[existing_tst_features].iloc[:-1].values
        y_train_tst = df_train_tst["Daily_Return"].iloc[1:].values
        X_test_tst = df_test_tst[existing_tst_features].iloc[:-1].values
        y_test_tst = df_test_tst["Daily_Return"].iloc[1:].values

        scaler_x_tst = StandardScaler()
        X_train_tst_scaled = scaler_x_tst.fit_transform(X_train_tst)
        X_test_tst_scaled = scaler_x_tst.transform(X_test_tst)

        model_tst = Ridge(alpha=1.0)
        model_tst.fit(X_train_tst_scaled, y_train_tst)

        test_preds_ret = model_tst.predict(X_test_tst_scaled)
        test_preds_close = df_test_tst["Close"].iloc[:-1].values * (1 + test_preds_ret)

        tst_rmse = float(np.sqrt(np.mean((test_preds_close - df_test_tst["Close"].iloc[1:].values) ** 2)))
        tst_mape = float(np.mean(np.abs((df_test_tst["Close"].iloc[1:].values - test_preds_close) / df_test_tst["Close"].iloc[1:].values)) * 100)

        act_dir = np.sign(df_test_tst["Daily_Return"].iloc[1:].values)
        prd_dir = np.sign(test_preds_ret)
        tst_da = float(np.mean(act_dir == prd_dir) * 100)

        patchtst_metrics = {
            "rmse": tst_rmse,
            "mape": tst_mape,
            "directional_accuracy": tst_da,
            "training_status": f"Trained PatchTST model ({interval})"
        }

        last_features_tst = df[existing_tst_features].iloc[-1:].values
        last_features_tst_scaled = scaler_x_tst.transform(last_features_tst)
        pred_tst_ret = float(model_tst.predict(last_features_tst_scaled)[0])
        pred_tst_ret = max(min(pred_tst_ret, max_ret), min_ret)
        patchtst_predicted_close = float(df["Close"].iloc[-1] * (1 + pred_tst_ret))
        
    except Exception as tst_err:
        print(f"Error executing PatchTST simulation: {tst_err}")
        
    return patchtst_predicted_close, patchtst_metrics
