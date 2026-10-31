# Wildfire Project — Milestones 3–4

## Main dataset
The project now uses the California Weather and Fire Prediction Dataset (1984–2025), a daily weather/fire-label dataset released on Zenodo under CC BY 4.0. The downloaded source has 14,988 rows and 14 fields. This is approximately 60 times the 244-row Algerian dataset supplied with the earlier project. The old Algerian CSVs and notebook are preserved in `legacy/`.

**Label-coverage decision:** all 366 dates in 2024 and all 12 dates in 2025 are labeled as no fire start. Because that abrupt all-zero period may indicate incomplete target coverage, it is excluded from the primary EDA and modeling preparation. The analysis window has 14,610 rows (1984-01-01 through 2023-12-31), including 4,971 positive labels. Three values in average wind speed and the corresponding wind/temperature ratio are missing; they are retained and imputed by the training-only pipeline.

## Deliverables
- `notebooks/01_eda_wildfire.ipynb`: data audit, visualizations, correlations, insights, caveats.
- `notebooks/02_preprocessing_wildfire.ipynb`: reproducible chronological split, fit-on-train preprocessing, readiness checks.
- `run_milestone3.py`: one-file script that regenerates the analysis plots, model-ready split, pipeline, and audit report.
- `run_milestone4.py`: reproducible model comparison, five-fold expanding time-series validation, selected-model holdout evaluation, predictions, and permutation-importance diagnostics.
- `notebooks/03_model_training_and_evaluation.ipynb`: guided notebook for running and reviewing the Milestone 4 model pipeline.
- `data/processed/california_wildfire_1984_2023.csv`: analysis-window source rows before imputation.
- `data/model_ready/`: numeric `X_train`/`X_test`, separate targets and dates, and the fitted preprocessing pipeline.
- `visuals/`: source-based plots used in the notebooks and presentation.
- `reports/preprocessing_audit.json`: split and readiness metrics.
- `reports/model_comparison_cv.csv` and `reports/model_cv_folds.csv`: per-model and per-fold chronological validation results.
- `reports/final_model_metrics.json`: selected model, held-out test metrics, class rates, and confusion matrix.
- `reports/selected_model_permutation_importance.csv`: test-sample diagnostic of feature relevance (not causal effects).
- `presentation/`: milestone summary slide deck (HTML, with PDF export if available).

## Split and features
Rows are sorted by date. The first 80% (11,688 days, 1984–2015) are training data; the final 20% (2,922 days, 2016–2023) are held out. The split is chronological, with no date overlap. Numeric missing values are median-imputed and standardized using training rows only. `SEASON` is one-hot encoded. `DATE` is excluded from model inputs, and `FIRE_START_DAY` is kept as the target.

The target denotes a fire start recorded on the same date, and the model includes weather recorded on that same date. It is therefore a historical same-day classification exercise, not a proven operational early-warning system. A source audit also found that the supplied `LAGGED_PRECIPITATION` and `LAGGED_AVG_WIND_SPEED` match rolling summaries that include the current day; the Milestone 4 model rebuilds these two features from preceding rows only. Positive-label rates differ between train and test, so temporal distribution shift remains a major limitation.

## Milestone 4 model comparison
Four classifiers are compared: a majority-class baseline, balanced Logistic Regression, balanced Random Forest, and Histogram Gradient Boosting. All preprocessing is fitted inside each pipeline and each validation fold uses only earlier dates than its validation period. Five expanding-window folds are run on the training period (1984–2015). The candidate with the highest mean Average Precision is selected, with the baseline included in the comparison; this CV score is a selection score and may be optimistic. The 2016–2023 holdout is then used for one final performance report. Accuracy is reported alongside balanced accuracy, precision, recall, F1, ROC AUC, and Average Precision. The decision threshold is a prespecified 0.5 and is not tuned on the holdout. Classifier scores are not calibrated probabilities. Permutation importance is an exploratory post-selection diagnostic, not a causal finding or a reason to iterate on the same test set.

## Run
From the project root, run `python run_milestone3.py` to regenerate preprocessing/EDA outputs, then `python run_milestone4.py` to train and evaluate the model candidates. Alternatively, open the notebooks in Jupyter and run them in order. Required libraries: pandas, numpy, matplotlib, seaborn, scikit-learn, joblib, nbformat. The notebooks discover the project root from the current folder.

## Source and attribution
Yavas, Cemil Emre; Kadlec, Christopher; Kim, Jongyeop; Chen, Lei. *California Weather and Fire Prediction Dataset (1984–2025) with Engineered Features*. Zenodo (2025). DOI: https://doi.org/10.5281/zenodo.14712845. License: Creative Commons Attribution 4.0 International. The record describes weather sourced from NOAA Climate Data Online and wildfire incidents from CAL FIRE.
