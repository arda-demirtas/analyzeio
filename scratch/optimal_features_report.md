# Optimal Features Selection Study for BTC-USD (XGBoost, LSTM, Linear Regression)

## 1. Average Model Performance by Feature Combination
*Sorted by Lowest Average RMSE*

| Rank | Combination Name | Features Count | Avg RMSE | Avg MAPE (%) | Avg Directional Accuracy (%) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **1_Current_2_feats** | 2 | $1963.78 | 1.63% | 51.13% |
| 2 | **2_Trend_Momentum_5_feats** | 5 | $2017.00 | 1.70% | 48.62% |
| 3 | **3_Volatility_Volume_4_feats** | 4 | $2075.61 | 1.75% | 47.70% |
| 4 | **5_Technical_Oscillators_10_feats** | 10 | $2120.25 | 1.78% | 49.87% |
| 5 | **6_Balanced_Subset_6_feats** | 6 | $2149.20 | 1.79% | 49.71% |
| 6 | **4_Full_Multivariate_10_feats** | 10 | $2171.79 | 1.83% | 48.29% |

## 2. Detailed Model Breakdown

| Combination Name | XGBoost RMSE / DA | LSTM RMSE / DA | Linear Reg RMSE / DA |
| :--- | :---: | :---: | :---: |
| 1_Current_2_feats | $1988.27 / 53.63% | $1921.63 / 47.87% | $1981.44 / 51.88% |
| 2_Trend_Momentum_5_feats | $2039.84 / 50.13% | $1930.44 / 45.61% | $2080.74 / 50.13% |
| 3_Volatility_Volume_4_feats | $2209.79 / 50.13% | $1928.81 / 44.11% | $2088.24 / 48.87% |
| 5_Technical_Oscillators_10_feats | $1996.28 / 50.13% | $2001.96 / 47.87% | $2362.52 / 51.63% |
| 6_Balanced_Subset_6_feats | $2065.58 / 50.88% | $1965.25 / 44.86% | $2416.77 / 53.38% |
| 4_Full_Multivariate_10_feats | $2081.76 / 46.37% | $2016.14 / 45.61% | $2417.46 / 52.88% |
