from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "california_wildfire_1984_2023.csv"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "model_ready" / "test_predictions.csv"
METRICS_PATH = PROJECT_ROOT / "reports" / "final_model_metrics.json"
COMPARISON_PATH = PROJECT_ROOT / "reports" / "model_comparison_cv.csv"
IMPORTANCE_PATH = PROJECT_ROOT / "reports" / "selected_model_permutation_importance.csv"

WEBAPP_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(WEBAPP_DIR / "templates"),
    static_folder=str(WEBAPP_DIR / "static"),
)
app.json.ensure_ascii = False


def load_project_data() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
    frame = frame.sort_values("DATE").reset_index(drop=True)
    frame["FIRE_START_DAY"] = (
        frame["FIRE_START_DAY"].astype(str).str.lower()
        .map({"true": 1, "false": 0, "1": 1, "0": 0}).fillna(0).astype(int)
    )
    return frame


def load_predictions() -> pd.DataFrame:
    frame = pd.read_csv(PREDICTIONS_PATH, parse_dates=["DATE"])
    frame["actual_FIRE_START_DAY"] = pd.to_numeric(frame["actual_FIRE_START_DAY"], errors="coerce").fillna(0).astype(int)
    frame["predicted_score"] = pd.to_numeric(frame["predicted_score"], errors="coerce").fillna(0.0)
    return frame


DATA = load_project_data()
PREDICTIONS = load_predictions()
METRICS = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
COMPARISON = pd.read_csv(COMPARISON_PATH)
IMPORTANCE = pd.read_csv(IMPORTANCE_PATH).sort_values("importance_mean", ascending=False)


def filtered_data(args) -> pd.DataFrame:
    start_year = int(args.get("from_year", DATA["DATE"].dt.year.min()))
    end_year = int(args.get("to_year", DATA["DATE"].dt.year.max()))
    start_year = max(int(DATA["DATE"].dt.year.min()), min(start_year, int(DATA["DATE"].dt.year.max())))
    end_year = max(start_year, min(end_year, int(DATA["DATE"].dt.year.max())))
    mask = DATA["DATE"].dt.year.between(start_year, end_year)
    season = args.get("season", "all")
    if season and season.lower() != "all":
        mask &= DATA["SEASON"].astype(str).str.lower() == season.lower()
    return DATA.loc[mask].copy()


def rate_table(frame: pd.DataFrame, column: str, order: list[str] | None = None):
    grouped = frame.groupby(column, dropna=False)["FIRE_START_DAY"].agg(["sum", "count"])
    grouped["rate"] = np.where(grouped["count"] > 0, grouped["sum"] / grouped["count"] * 100, 0)
    grouped = grouped.reset_index()
    if order:
        grouped[column] = pd.Categorical(grouped[column], categories=order, ordered=True)
        grouped = grouped.sort_values(column)
    return [
        {"label": str(row[column]), "rate": round(float(row["rate"]), 2), "events": int(row["sum"]), "days": int(row["count"])}
        for _, row in grouped.iterrows()
    ]


def threshold_summary(threshold: float) -> dict:
    y = PREDICTIONS["actual_FIRE_START_DAY"].to_numpy(dtype=int)
    scores = PREDICTIONS["predicted_score"].to_numpy(dtype=float)
    pred = (scores >= threshold).astype(int)
    tp = int(((y == 1) & (pred == 1)).sum())
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(y) if len(y) else 0.0
    return {
        "threshold": round(float(threshold), 2),
        "accuracy": round(accuracy * 100, 1),
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1": round(f1 * 100, 1),
        "matrix": [[tn, fp], [fn, tp]],
        "positives": int(y.sum()),
        "negatives": int((y == 0).sum()),
    }


@app.get("/")
def index():
    return render_template(
        "index.html",
        min_year=int(DATA["DATE"].dt.year.min()),
        max_year=int(DATA["DATE"].dt.year.max()),
        total_days=len(DATA),
        project_root=PROJECT_ROOT.name,
    )


@app.get("/api/overview")
def overview():
    frame = filtered_data(request.args)
    if frame.empty:
        return jsonify({"error": "No observations match the selected filters."}), 400
    yearly = frame.assign(YEAR=frame["DATE"].dt.year).groupby("YEAR")["FIRE_START_DAY"].agg(["sum", "count"])
    seasons = rate_table(frame, "SEASON", ["Winter", "Spring", "Summer", "Fall"])
    temperature = frame.dropna(subset=["MAX_TEMP"]).copy()
    temperature["TEMP_BAND"] = pd.cut(
        temperature["MAX_TEMP"],
        bins=[-np.inf, 65, 70, 75, np.inf],
        labels=["<65°F", "65–70°F", "70–75°F", ">75°F"],
        right=False,
    )
    temps = rate_table(temperature, "TEMP_BAND", ["<65°F", "65–70°F", "70–75°F", ">75°F"])
    events = int(frame["FIRE_START_DAY"].sum())
    return jsonify({
        "kpis": {
            "days": int(len(frame)),
            "events": events,
            "rate": round(events / len(frame) * 100, 1),
            "from": frame["DATE"].min().strftime("%Y-%m-%d"),
            "to": frame["DATE"].max().strftime("%Y-%m-%d"),
        },
        "yearly": [
            {"year": int(year), "events": int(row["sum"]), "rate": round(float(row["sum"] / row["count"] * 100), 2)}
            for year, row in yearly.iterrows()
        ],
        "seasons": seasons,
        "temperature": temps,
        "preview": frame[["DATE", "MAX_TEMP", "MIN_TEMP", "AVG_WIND_SPEED", "PRECIPITATION", "SEASON", "FIRE_START_DAY"]]
            .tail(10).iloc[::-1].assign(DATE=lambda x: x["DATE"].dt.strftime("%Y-%m-%d"), FIRE_START_DAY=lambda x: x["FIRE_START_DAY"].map({1: "Fire start", 0: "No recorded start"}))
            .replace({np.nan: None}).to_dict(orient="records"),
    })


@app.get("/api/models")
def models():
    rows = COMPARISON.sort_values("cv_average_precision_mean", ascending=False).to_dict(orient="records")
    return jsonify({"selected": METRICS["selected_model"], "folds": METRICS["cross_validation_splits"], "rows": rows})


@app.get("/api/test")
def test_results():
    result = dict(METRICS)
    result["threshold_view"] = threshold_summary(0.5)
    result["feature_importance"] = [
        {"feature": str(row["feature"]), "importance": round(float(row["importance_mean"]), 4), "std": round(float(row["importance_std"]), 4)}
        for _, row in IMPORTANCE.head(10).iterrows()
    ]
    return jsonify(result)


@app.get("/api/threshold")
def threshold():
    try:
        value = float(request.args.get("value", 0.5))
    except (TypeError, ValueError):
        value = 0.5
    value = min(0.95, max(0.05, value))
    return jsonify(threshold_summary(value))


@app.get("/download/filtered.csv")
def download_filtered():
    frame = filtered_data(request.args)
    output = BytesIO(frame.to_csv(index=False).encode("utf-8-sig"))
    return send_file(output, as_attachment=True, download_name="wildfire_analysis_filtered.csv", mimetype="text/csv")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "analysis_rows": len(DATA), "test_rows": len(PREDICTIONS)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
