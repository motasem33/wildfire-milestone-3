from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "raw" / "CA_Weather_Fire_Dataset_1984-2025.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "data" / "model_ready"
VISUALS_DIR = ROOT / "visuals"
REPORTS_DIR = ROOT / "reports"

for directory in [PROCESSED_DIR, MODEL_DIR, VISUALS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(RAW_PATH, parse_dates=["DATE"])
raw = raw.sort_values("DATE").reset_index(drop=True)
df = raw.loc[raw["YEAR"] <= 2023].copy().reset_index(drop=True)
df.to_csv(PROCESSED_DIR / "california_wildfire_1984_2023.csv", index=False)

season_order = ["Winter", "Spring", "Summer", "Fall"]
season = df.groupby("SEASON")["FIRE_START_DAY"].agg(["mean", "sum", "count"]).reindex(season_order)
yearly = df.groupby("YEAR")["FIRE_START_DAY"].agg(["sum", "mean"])

sns.set_theme(style="whitegrid", context="talk")
fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
axes[0].bar(season.index, season["mean"] * 100, color=["#90a4ae", "#6e9e78", "#e19a4b", "#c96a4c"])
axes[0].set_title("Recorded fire-start days by season")
axes[0].set_ylabel("Days labeled fire start (%)")
axes[0].set_xlabel("Season")
axes[0].tick_params(axis="x", rotation=15)
axes[1].plot(yearly.index, yearly["sum"], color="#bf553b", linewidth=2)
axes[1].set_title("Fire-start days recorded per year")
axes[1].set_ylabel("Days labeled fire start")
axes[1].set_xlabel("Year")
axes[1].set_xlim(1984, 2023)
fig.suptitle("California wildfire dataset · 1984–2023", fontsize=18, fontweight="bold")
fig.tight_layout()
fig.savefig(VISUALS_DIR / "season_and_year.png", dpi=170, bbox_inches="tight")
plt.close(fig)

temp = df.dropna(subset=["MAX_TEMP"]).copy()
temp["MAX_TEMP_QUARTILE"] = pd.qcut(temp["MAX_TEMP"], 4, duplicates="drop")
temp_rate = temp.groupby("MAX_TEMP_QUARTILE", observed=True)["FIRE_START_DAY"].mean() * 100
fig, ax = plt.subplots(figsize=(9, 5.3))
bars = ax.bar([f"Q{i + 1}\\n{interval.left:.0f}–{interval.right:.0f}°F" for i, interval in enumerate(temp_rate.index)], temp_rate.values, color=["#9bb2be", "#86a28e", "#e1b35e", "#cb6648"])
ax.set_ylabel("Days labeled fire start (%)")
ax.set_title("Fire-start label rate across maximum-temperature quartiles")
ax.set_xlabel("Maximum temperature quartile")
for bar, value in zip(bars, temp_rate.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{value:.1f}%", ha="center", fontsize=11)
fig.tight_layout()
fig.savefig(VISUALS_DIR / "fire_rate_by_temperature.png", dpi=170, bbox_inches="tight")
plt.close(fig)

numeric_data = df.select_dtypes(include="number").copy()
numeric_data["FIRE_START_DAY"] = df["FIRE_START_DAY"].astype(int)
correlations = numeric_data.corr(numeric_only=True)
fig, ax = plt.subplots(figsize=(11, 8))
sns.heatmap(correlations, cmap="vlag", center=0, annot=True, fmt=".2f", square=True, linewidths=0.35, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title("Numeric-feature correlation matrix · 1984–2023", pad=14)
fig.tight_layout()
fig.savefig(VISUALS_DIR / "correlation_heatmap.png", dpi=170, bbox_inches="tight")
plt.close(fig)

missing = df.isna().sum().sort_values(ascending=False)
missing = missing[missing > 0]
fig, ax = plt.subplots(figsize=(8, 4))
if len(missing):
    ax.bar(missing.index, missing.values, color="#ca6a4d")
ax.set_title("Missing values in the analysis window")
ax.set_ylabel("Missing rows")
ax.tick_params(axis="x", rotation=25)
fig.tight_layout()
fig.savefig(VISUALS_DIR / "missing_values.png", dpi=160, bbox_inches="tight")
plt.close(fig)

numeric_features = ["PRECIPITATION", "MAX_TEMP", "MIN_TEMP", "AVG_WIND_SPEED", "YEAR", "TEMP_RANGE", "WIND_TEMP_RATIO", "MONTH", "LAGGED_PRECIPITATION", "LAGGED_AVG_WIND_SPEED", "DAY_OF_YEAR"]
categorical_features = ["SEASON"]
target = "FIRE_START_DAY"
cut = int(len(df) * 0.80)
train = df.iloc[:cut].copy()
test = df.iloc[cut:].copy()

try:
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
except TypeError:
    encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric_features),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", encoder)]), categorical_features),
    ],
    remainder="drop",
    verbose_feature_names_out=False,
)

preprocessor.fit(train[numeric_features + categorical_features])
feature_names = preprocessor.get_feature_names_out().tolist()
x_train = pd.DataFrame(preprocessor.transform(train[numeric_features + categorical_features]), columns=feature_names)
x_test = pd.DataFrame(preprocessor.transform(test[numeric_features + categorical_features]), columns=feature_names)
y_train = train[target].astype(int).reset_index(drop=True)
y_test = test[target].astype(int).reset_index(drop=True)

x_train.to_csv(MODEL_DIR / "X_train.csv", index=False)
x_test.to_csv(MODEL_DIR / "X_test.csv", index=False)
y_train.rename(target).to_csv(MODEL_DIR / "y_train.csv", index=False)
y_test.rename(target).to_csv(MODEL_DIR / "y_test.csv", index=False)
train[["DATE"]].to_csv(MODEL_DIR / "train_dates.csv", index=False)
test[["DATE"]].to_csv(MODEL_DIR / "test_dates.csv", index=False)
joblib.dump(preprocessor, MODEL_DIR / "preprocessing_pipeline.joblib")

assert train["DATE"].max() < test["DATE"].min()
assert set(train["DATE"]).isdisjoint(set(test["DATE"]))
assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in x_train.dtypes)
assert x_train.isna().sum().sum() == 0
assert x_test.isna().sum().sum() == 0
assert np.isfinite(x_train.to_numpy()).all()
assert np.isfinite(x_test.to_numpy()).all()

audit = {
    "source_rows": int(len(raw)),
    "analysis_rows": int(len(df)),
    "excluded_rows": int(len(raw) - len(df)),
    "analysis_start": str(df["DATE"].min().date()),
    "analysis_end": str(df["DATE"].max().date()),
    "split_date": str(test["DATE"].min().date()),
    "train_rows": int(len(train)),
    "test_rows": int(len(test)),
    "train_positive": int(y_train.sum()),
    "test_positive": int(y_test.sum()),
    "train_positive_rate": float(y_train.mean()),
    "test_positive_rate": float(y_test.mean()),
    "features": feature_names,
    "train_missing_after_transform": int(x_train.isna().sum().sum()),
    "test_missing_after_transform": int(x_test.isna().sum().sum()),
}
(REPORTS_DIR / "preprocessing_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(json.dumps(audit, indent=2))
print(f"\nتم حفظ النتائج في: {ROOT}")
