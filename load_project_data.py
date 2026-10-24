from pathlib import Path
import pandas as pd

# This helper loads the original source data and the analysis-window dataset.
ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "raw" / "CA_Weather_Fire_Dataset_1984-2025.csv"
ANALYSIS_PATH = ROOT / "data" / "processed" / "california_wildfire_1984_2023.csv"

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1200)

raw_df = pd.read_csv(RAW_PATH, parse_dates=["DATE"])
analysis_df = pd.read_csv(ANALYSIS_PATH, parse_dates=["DATE"])

print(f"Raw source: {raw_df.shape[0]:,} rows x {raw_df.shape[1]} columns")
print(f"Analysis window: {analysis_df.shape[0]:,} rows x {analysis_df.shape[1]} columns")
print(f"Analysis dates: {analysis_df['DATE'].min().date()} to {analysis_df['DATE'].max().date()}")
print("Analysis target distribution:")
print(analysis_df["FIRE_START_DAY"].value_counts(dropna=False))
print("\nMissing values in analysis window:")
print(analysis_df.isna().sum().sort_values(ascending=False).head())

# Start exploring with analysis_df.head() or use the prepared X_train/y_train
# files under data/model_ready/ for the leak-free chronological split.
