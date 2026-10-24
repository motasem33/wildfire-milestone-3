# Wildfire Project — Milestone 3

## Main dataset
The project now uses the California Weather and Fire Prediction Dataset (1984–2025), a daily weather/fire-label dataset released on Zenodo under CC BY 4.0. The downloaded source has 14,988 rows and 14 fields. This is approximately 60 times the 244-row Algerian dataset supplied with the earlier project. The old Algerian CSVs and notebook are preserved in `legacy/`.

**Label-coverage decision:** all 366 dates in 2024 and all 12 dates in 2025 are labeled as no fire start. Because that abrupt all-zero period may indicate incomplete target coverage, it is excluded from the primary EDA and modeling preparation. The analysis window has 14,610 rows (1984-01-01 through 2023-12-31), including 4,971 positive labels. Three values in average wind speed and the corresponding wind/temperature ratio are missing; they are retained and imputed by the training-only pipeline.

## Deliverables
- `notebooks/01_eda_wildfire.ipynb`: data audit, visualizations, correlations, insights, caveats.
- `notebooks/02_preprocessing_wildfire.ipynb`: reproducible chronological split, fit-on-train preprocessing, readiness checks.
- `run_milestone3.py`: one-file script that regenerates the analysis plots, model-ready split, pipeline, and audit report.
- `data/processed/california_wildfire_1984_2023.csv`: analysis-window source rows before imputation.
- `data/model_ready/`: numeric `X_train`/`X_test`, separate targets and dates, and the fitted preprocessing pipeline.
- `visuals/`: source-based plots used in the notebooks and presentation.
- `reports/preprocessing_audit.json`: split and readiness metrics.
- `presentation/`: milestone summary slide deck (HTML, with PDF export if available).

## Split and features
Rows are sorted by date. The first 80% (11,688 days, 1984–2015) are training data; the final 20% (2,922 days, 2016–2023) are held out. The split is chronological, with no date overlap. Numeric missing values are median-imputed and standardized using training rows only. `SEASON` is one-hot encoded. `DATE` is excluded from model inputs, and `FIRE_START_DAY` is kept as the target.

The target denotes a fire start recorded on the same date, so this is a historical classification preparation task, not a proven early-warning system. Same-day weather can be contemporaneous with an event. In addition, positive-label rates differ between train and test; temporal distribution shift should be reported in the next milestone. No model is trained for Milestone 3.

## Run
From the project root, run `python run_milestone3.py` to regenerate the outputs, or open the notebooks in Jupyter. Required libraries: pandas, numpy, matplotlib, seaborn, scikit-learn, joblib, nbformat. The notebooks discover the project root from the current folder.

## Source and attribution
Yavas, Cemil Emre; Kadlec, Christopher; Kim, Jongyeop; Chen, Lei. *California Weather and Fire Prediction Dataset (1984–2025) with Engineered Features*. Zenodo (2025). DOI: https://doi.org/10.5281/zenodo.14712845. License: Creative Commons Attribution 4.0 International. The record describes weather sourced from NOAA Climate Data Online and wildfire incidents from CAL FIRE.
