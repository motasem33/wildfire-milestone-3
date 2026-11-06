# Wildfire Analysis Dashboard

An Arabic Flask dashboard for the California wildfire classification project. It uses the project's real analysis dataset, cross-validation report, selected-model holdout predictions, and feature-importance report.

## Run locally

From the project root, install the project requirements and start Flask:

```bash
python -m pip install -r requirements.txt
python webapp/app.py
```

Open `http://127.0.0.1:5000` in a browser. The analysis files under `data/processed`, `data/model_ready`, and `reports` must exist first. The root README documents how to regenerate them.

## Dashboard features

- Filter descriptive summaries by year interval and season.
- Review yearly, seasonal, and temperature-bin label patterns.
- Preview and download the filtered observations as CSV.
- Compare model Average Precision across the five expanding chronological folds.
- Review final holdout metrics and explore how a decision threshold changes the confusion matrix.
- Inspect permutation importance, with explicit causal and forecast-scope caveats.

The threshold slider is a sensitivity demonstration on the saved holdout predictions. Do not use it to select a final decision threshold and then report performance on that same holdout.

## Data and scope

The model evaluates historical same-day fire-start labels using daily weather. This is not a validated early-warning service. See the root README for the data source, license, coverage decision, model design, and limitations.
