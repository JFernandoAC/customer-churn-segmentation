"""Score every current customer with the churn model and save it for Power BI.

Training used a cutoff 90 days before the end of the data. Here we use the
last day of the data as "today" and predict who will churn in the NEXT 90 days.
"""
import joblib
import pandas as pd

from build_features import (FEATURE_COLUMNS, MAX_RECENCY_DAYS, build_features,
                            load_transactions)
from db import get_engine
from train_model import MODEL_PATH


def risk_level(probability):
    if probability >= 0.7:
        return "High"
    if probability >= 0.4:
        return "Medium"
    return "Low"


def main():
    engine = get_engine()
    model = joblib.load(MODEL_PATH)
    purchases, cancellations = load_transactions(engine)

    today = purchases["invoice_date"].max().normalize() + pd.Timedelta(days=1)
    features = build_features(purchases, cancellations, today)
    features = features[features["recency_days"] <= MAX_RECENCY_DAYS]

    scores = features.copy()
    scores["churn_probability"] = model.predict_proba(features[FEATURE_COLUMNS].astype(float))[:, 1]
    scores["risk_level"] = scores["churn_probability"].apply(risk_level)

    segments = pd.read_sql("SELECT customer_id, segment FROM customer_segments", engine)
    scores = scores.reset_index().merge(segments, on="customer_id", how="left")

    scores.to_sql("customer_scores", engine, if_exists="replace", index=False)
    print(f"Scored {len(scores):,} customers. Saved table customer_scores")
    print(pd.crosstab(scores["segment"], scores["risk_level"]).to_string())


if __name__ == "__main__":
    main()
