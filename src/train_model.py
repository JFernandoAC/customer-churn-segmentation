"""Train two churn models, compare them, and save the best one.

Every training run is recorded in MLflow (parameters, metrics, plots, model)
so we can compare experiments later with `mlflow ui`.
"""
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, average_precision_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from xgboost import XGBClassifier

from build_features import FEATURE_COLUMNS, FEATURES_PATH

MODEL_PATH = Path("models/churn_model.joblib")
TEST_PATH = Path("data/processed/test_set.csv")

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("churn-prediction")


def make_models():
    # Logistic regression is the simple baseline. It works best when the
    # inputs are not skewed and are on the same scale, hence log1p + scaler.
    logistic = make_pipeline(
        FunctionTransformer(np.log1p),
        StandardScaler(),
        LogisticRegression(max_iter=1000),
    )
    # XGBoost builds many small decision trees, each one fixing the errors of
    # the previous ones. Trees do not care about scale, so no preprocessing.
    xgboost = XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    return {"logistic_regression": logistic, "xgboost": xgboost}


def evaluate(model, X_test, y_test):
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    return {
        "test_roc_auc": roc_auc_score(y_test, probabilities),
        "test_pr_auc": average_precision_score(y_test, probabilities),
        "test_precision": precision_score(y_test, predictions),
        "test_recall": recall_score(y_test, predictions),
        "test_f1": f1_score(y_test, predictions),
    }


def save_confusion_matrix(model, X_test, y_test, name):
    path = Path(f"reports/figures/confusion_matrix_{name}.png")
    ConfusionMatrixDisplay.from_estimator(model, X_test, y_test,
                                          display_labels=["Stays", "Churns"], cmap="Blues")
    plt.title(name)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    return path


def main():
    data = pd.read_csv(FEATURES_PATH, index_col="customer_id")
    X = data[FEATURE_COLUMNS].astype(float)  # the API also receives floats
    y = data["churned"]

    # stratify=y keeps the same churn rate in train and test.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)
    # Saved so explain_model.py explains the model on the same unseen customers.
    X_test.assign(churned=y_test).to_csv(TEST_PATH)

    results = {}
    for name, model in make_models().items():
        with mlflow.start_run(run_name=name):
            # Cross-validation: train 5 times on 4/5 of the training data and
            # score on the remaining 1/5. More reliable than a single split.
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
            model.fit(X_train, y_train)
            metrics = evaluate(model, X_test, y_test)
            metrics["cv_roc_auc"] = cv_scores.mean()

            if name == "xgboost":
                mlflow.log_params(model.get_params())
            mlflow.log_param("model", name)
            mlflow.log_metrics(metrics)
            mlflow.log_artifact(save_confusion_matrix(model, X_test, y_test, name))
            # "pickle" is the same format joblib uses below. MLflow's default
            # (skops) refuses XGBoost objects unless we list them as trusted.
            mlflow.sklearn.log_model(model, name="model", serialization_format="pickle",
                                     input_example=X_test.head(3))

        results[name] = (model, metrics)
        print(f"{name}: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))

    # Pick the winner by cross-validation, not by the test set: the test set is
    # only for reporting, otherwise we would be tuning to it.
    best_name = max(results, key=lambda name: results[name][1]["cv_roc_auc"])
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(results[best_name][0], MODEL_PATH)
    print(f"Best model: {best_name}. Saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
