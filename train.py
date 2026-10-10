import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)

print("Synthesizing multi-tenant corporate telemetry...")

np.random.seed(42)
dates = pd.date_range(start="2023-01-06", end="2025-12-26", freq="W-FRI")

# 1. Google Enterprise Data (Cloud, Hardware, Ads, Workspace)
records_google = []
for node in [1, 2, 3, 4]:
    base = 45000 + (node * 12000)
    for dt in dates:
        month = dt.month
        week = dt.isocalendar().week
        is_holiday = 1 if week in [47, 51] else 0
        seasonal = 1.0 + 0.15 * np.sin(2 * np.pi * (month / 12.0))
        sales = (base * seasonal * (1.25 if is_holiday else 1.0)) + np.random.normal(0, 1500)
        records_google.append({
            "Date": dt, "Store": node, "Dept": node, 
            "Weekly_Sales": round(max(5000.0, sales), 2), "IsHoliday": is_holiday
        })

df_google = pd.DataFrame(records_google)
df_google['Date'] = pd.to_datetime(df_google['Date'])
df_google['Month'] = df_google['Date'].dt.month
df_google['Week'] = df_google['Date'].dt.isocalendar().week.astype(int)
df_google['Lag_1'] = df_google.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(1)
df_google['Lag_4'] = df_google.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(4)
df_google['Rolling_Mean_4'] = df_google.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(1).rolling(4).mean()
df_google = df_google.dropna().reset_index(drop=True)
df_google.to_csv("data/google_sales.csv", index=False)

# 2. Meta Enterprise Data (Ad Revenue, Reality Labs, AI Servers)
records_meta = []
for node in [1, 2, 3]:
    base = 65000 + (node * 18000)
    for dt in dates:
        month = dt.month
        week = dt.isocalendar().week
        is_holiday = 1 if week in [46, 47, 50, 51] else 0
        seasonal = 1.0 + 0.22 * np.sin(2 * np.pi * (month / 12.0))
        sales = (base * seasonal * (1.30 if is_holiday else 1.0)) + np.random.normal(0, 2000)
        records_meta.append({
            "Date": dt, "Store": node, "Dept": node, 
            "Weekly_Sales": round(max(8000.0, sales), 2), "IsHoliday": is_holiday
        })

df_meta = pd.DataFrame(records_meta)
df_meta['Date'] = pd.to_datetime(df_meta['Date'])
df_meta['Month'] = df_meta['Date'].dt.month
df_meta['Week'] = df_meta['Date'].dt.isocalendar().week.astype(int)
df_meta['Lag_1'] = df_meta.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(1)
df_meta['Lag_4'] = df_meta.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(4)
df_meta['Rolling_Mean_4'] = df_meta.groupby(['Store', 'Dept'])['Weekly_Sales'].shift(1).rolling(4).mean()
df_meta = df_meta.dropna().reset_index(drop=True)
df_meta.to_csv("data/meta_sales.csv", index=False)

# 3. Train Model on Pooled Data
combined = pd.concat([df_google, df_meta], ignore_index=True)
features = ['Store', 'Dept', 'Month', 'Week', 'IsHoliday', 'Lag_1', 'Lag_4', 'Rolling_Mean_4']
X = combined[features]
y = combined['Weekly_Sales']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, "models/sales_model.pkl")
print("Saved models/sales_model.pkl and multi-tenant datasets.")