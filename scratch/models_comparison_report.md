# BTC-USD 4-Model Performance Comparison Study

Generated on: 2026-07-05 01:36:36 UTC
Asset: BTC-USD
Last Close Price: $63,144.01

## 1. Test Performance Metrics (Evaluation Set)

| Model Name | Test RMSE | Test MAPE (%) | Directional Accuracy (%) |
| :--- | :---: | :---: | :---: |
| **XGBoost** | $1999.88 | 1.66% | 51.38% |
| **LSTM** | $1916.71 | 1.58% | 48.87% |
| **Linear Regression (Ridge)** | $1981.44 | 1.64% | 51.88% |
| **PatchTST (Multivariate Simulation)** | $1932.48 | 1.60% | 47.59% |

## 2. Next Day Prediction Forecasts

| Model Name | Predicted Close Price | Expected Price Change | Sentiment Recommendation |
| :--- | :---: | :---: | :---: |
| **XGBoost** | $63,915.488 | +1.22% | **BULLISH (LONG)** |
| **LSTM** | $63,177.681 | +0.05% | **BULLISH (LONG)** |
| **Linear Regression (Ridge)** | $63,317.562 | +0.27% | **BULLISH (LONG)** |
| **PatchTST (Multivariate Simulation)** | $63,058.748 | -0.14% | **BEARISH (SHORT)** |

---
*Note: Evaluated on 80% train / 20% test split of historical data. PatchTST is trained on 13 multivariate indicators.*
