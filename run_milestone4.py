from pathlib import Path
import json
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "california_wildfire_1984_2023.csv"
MODEL_DIR = ROOT / "data" / "model_ready"
REPORT_DIR = ROOT / "reports"
VISUALS_DIR = ROOT / "visuals"
for folder in [MODEL_DIR, REPORT_DIR, VISUALS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
CV_SPLITS = 5
NUMERIC_FEATURES = [
    "PRECIPITATION",
    "MAX_TEMP",
    "MIN_TEMP",
    "AVG_WIND_SPEED",
    "YEAR",
    "TEMP_RANGE",
    "WIND_TEMP_RATIO",
    "MONTH",
    "PREVIOUS_7D_PRECIPITATION",
    "PREVIOUS_7D_AVG_WIND_SPEED",
    "DAY_OF_YEAR",
]
CATEGORICAL_FEATURES = ["SEASON"]
TARGET = "FIRE_START_DAY"


def make_preprocessor():
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_models():
    definitions = {
        "Majority baseline": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=3,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "Histogram Gradient Boosting": HistGradientBoostingClassifier(
            max_iter=250,
            learning_rate=0.08,
            l2_regularization=1.0,
            random_state=RANDOM_STATE,
        ),
    }
    return {
        name: Pipeline(
            [("preprocess", make_preprocessor()), ("classifier", estimator)]
        )
        for name, estimator in definitions.items()
    }


def calculate_metrics(y_true, y_pred, y_prob):
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
    }


def run():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing analysis data: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
    df = df.sort_values("DATE").reset_index(drop=True)
    df["PREVIOUS_7D_PRECIPITATION"] = df["PRECIPITATION"].shift(1).rolling(7, min_periods=1).sum()
    df["PREVIOUS_7D_AVG_WIND_SPEED"] = df["AVG_WIND_SPEED"].shift(1).rolling(7, min_periods=1).mean()
    cut = int(len(df) * 0.80)
    train = df.iloc[:cut].copy()
    test = df.iloc[cut:].copy()
    X_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    X_test = test[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train[TARGET].astype(int)
    y_test = test[TARGET].astype(int)

    if train["DATE"].max() >= test["DATE"].min():
        raise ValueError("The chronological training/test split is invalid.")
    if y_train.nunique() != 2 or y_test.nunique() != 2:
        raise ValueError("Both target classes must occur in training and test sets.")

    X_train.to_csv(MODEL_DIR / "milestone4_X_train.csv", index=False)
    X_test.to_csv(MODEL_DIR / "milestone4_X_test.csv", index=False)

    cv = TimeSeriesSplit(n_splits=CV_SPLITS)
    scoring = {
        "accuracy": "accuracy",
        "balanced_accuracy": "balanced_accuracy",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "average_precision": "average_precision",
    }
    models = make_models()
    rows = []
    fold_rows = []
    fitted_cv_models = {}

    for name, pipeline in models.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cv_result = cross_validate(
                pipeline,
                X_train,
                y_train,
                cv=cv,
                scoring=scoring,
                n_jobs=1,
                return_estimator=True,
                error_score="raise",
            )
        fitted_cv_models[name] = cv_result["estimator"][-1]
        row = {"model": name}
        for metric in scoring:
            values = cv_result[f"test_{metric}"]
            row[f"cv_{metric}_mean"] = float(np.mean(values))
            row[f"cv_{metric}_std"] = float(np.std(values, ddof=1))
        rows.append(row)
        for fold_index in range(CV_SPLITS):
            train_idx, validation_idx = list(TimeSeriesSplit(n_splits=CV_SPLITS).split(X_train))[fold_index]
            fold_rows.append(
                {
                    "model": name,
                    "fold": fold_index + 1,
                    "train_start": str(train.iloc[train_idx[0]]["DATE"].date()),
                    "train_end": str(train.iloc[train_idx[-1]]["DATE"].date()),
                    "validation_start": str(train.iloc[validation_idx[0]]["DATE"].date()),
                    "validation_end": str(train.iloc[validation_idx[-1]]["DATE"].date()),
                    "accuracy": float(cv_result["test_accuracy"][fold_index]),
                    "balanced_accuracy": float(cv_result["test_balanced_accuracy"][fold_index]),
                    "f1": float(cv_result["test_f1"][fold_index]),
                    "roc_auc": float(cv_result["test_roc_auc"][fold_index]),
                    "average_precision": float(cv_result["test_average_precision"][fold_index]),
                }
            )

    comparison = pd.DataFrame(rows).sort_values(
        ["cv_average_precision_mean", "cv_balanced_accuracy_mean"], ascending=False
    )
    comparison.to_csv(REPORT_DIR / "model_comparison_cv.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(REPORT_DIR / "model_cv_folds.csv", index=False)

    winner_name = str(comparison.iloc[0]["model"])
    final_model = clone(models[winner_name])
    final_model.fit(X_train, y_train)
    y_probability = final_model.predict_proba(X_test)[:, 1]
    y_prediction = (y_probability >= 0.5).astype(int)
    test_metrics = calculate_metrics(y_test, y_prediction, y_probability)
    matrix = confusion_matrix(y_test, y_prediction, labels=[0, 1])
    report = classification_report(
        y_test,
        y_prediction,
        labels=[0, 1],
        target_names=["No recorded fire start", "Recorded fire start"],
        output_dict=True,
        zero_division=0,
    )

    test_predictions = pd.DataFrame(
        {
            "DATE": test["DATE"].dt.strftime("%Y-%m-%d"),
            "actual_FIRE_START_DAY": y_test.to_numpy(),
            "predicted_FIRE_START_DAY": y_prediction,
            "predicted_score": y_probability,
        }
    )
    test_predictions.to_csv(MODEL_DIR / "test_predictions.csv", index=False)
    joblib.dump(final_model, MODEL_DIR / "selected_model.joblib")
    (MODEL_DIR / "selected_model_name.txt").write_text(winner_name + "\n", encoding="utf-8")

    metrics_payload = {
        "selection_rule": "Highest mean time-series cross-validation average precision across all candidates, including the majority baseline. The winning CV score is a selection score, not an unbiased estimate.",
        "decision_threshold": 0.5,
        "threshold_note": "Prespecified default cutoff; precision, recall, F1, and confusion matrix are threshold-dependent.",
        "score_note": "Classifier scores are not calibrated fire-risk probabilities.",
        "test_use_note": "Final test metrics are reported once after selection. Permutation importance is an exploratory post-selection diagnostic and must not be used to revise the model against this same test set.",
        "selected_model": winner_name,
        "training_rows": int(len(train)),
        "training_period": [str(train["DATE"].min().date()), str(train["DATE"].max().date())],
        "test_rows": int(len(test)),
        "test_period": [str(test["DATE"].min().date()), str(test["DATE"].max().date())],
        "positive_rate_train": float(y_train.mean()),
        "positive_rate_test": float(y_test.mean()),
        "positive_rate_change_percentage_points": float((y_test.mean() - y_train.mean()) * 100),
        "test_metrics": test_metrics,
        "confusion_matrix_labels_0_1": matrix.tolist(),
        "classification_report": report,
        "cross_validation_splits": CV_SPLITS,
    }
    (REPORT_DIR / "final_model_metrics.json").write_text(
        json.dumps(metrics_payload, indent=2), encoding="utf-8"
    )

    feature_names = X_test.columns.to_list()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        permutation = permutation_importance(
            final_model,
            X_test,
            y_test,
            scoring="average_precision",
            n_repeats=5,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance_mean": permutation.importances_mean,
            "importance_std": permutation.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    importance.to_csv(REPORT_DIR / "selected_model_permutation_importance.csv", index=False)

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(11, 6))
    plotted = comparison.sort_values("cv_average_precision_mean")
    ax.barh(
        plotted["model"],
        plotted["cv_average_precision_mean"],
        xerr=plotted["cv_average_precision_std"],
        color=["#aebbc2" if name == "Majority baseline" else "#bd644a" if name == winner_name else "#738c83" for name in plotted["model"]],
        capsize=4,
    )
    ax.set_xlabel("Mean Average Precision (5 chronological folds)")
    ax.set_title("Fair model comparison on training data")
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(VISUALS_DIR / "model_comparison_cv.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Predicted no fire", "Predicted fire"],
        yticklabels=["Actual no fire", "Actual fire"],
        ax=ax,
    )
    ax.set_title(f"Held-out test confusion matrix\n{winner_name}")
    ax.set_xlabel("Prediction")
    ax.set_ylabel("Observed label")
    fig.tight_layout()
    fig.savefig(VISUALS_DIR / "final_model_confusion_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    top = importance.head(10).sort_values("importance_mean")
    ax.barh(top["feature"], top["importance_mean"], xerr=top["importance_std"], color="#bd644a", capsize=3)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Decrease in held-out average precision after shuffling")
    ax.set_title("Permutation importance for the selected model")
    fig.tight_layout()
    fig.savefig(VISUALS_DIR / "selected_model_feature_importance.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "selected_model": winner_name,
        "selection_cv_average_precision": float(comparison.iloc[0]["cv_average_precision_mean"]),
        "selection_cv_average_precision_std": float(comparison.iloc[0]["cv_average_precision_std"]),
        "test_metrics": test_metrics,
        "train_positive_rate": float(y_train.mean()),
        "test_positive_rate": float(y_test.mean()),
        "confusion_matrix": matrix.tolist(),
        "top_features": importance.head(5).to_dict(orient="records"),
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run()
