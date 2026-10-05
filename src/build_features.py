"""Build one row per customer with behaviour features and a churn label.

The idea: pretend we are standing on CUTOFF_DATE. Features only use what
happened BEFORE that date; the label only looks at what happened AFTER it.
"""
from pathlib import Path

import pandas as pd

from db import get_engine

CHURN_WINDOW_DAYS = 90
# Customers who had not bought in a whole year are already gone; predicting
# them is trivial and would inflate the model's scores, so we leave them out.
MAX_RECENCY_DAYS = 365
FEATURES_PATH = Path("data/processed/features.csv")

FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "avg_order_value",
    "tenure_days",
    "distinct_products",
    "orders_last_90d",
    "cancel_rate",
    "is_uk",
]


def load_transactions(engine):
    purchases = pd.read_sql(
        "SELECT invoice, stock_code, invoice_date, line_total, customer_id, country "
        "FROM clean_transactions",
        engine,
    )
    cancellations = pd.read_sql("SELECT invoice, invoice_date, customer_id FROM cancellations", engine)
    return purchases, cancellations


def build_features(purchases, cancellations, cutoff_date):
    """Features per customer using only data before cutoff_date."""
    past = purchases[purchases["invoice_date"] < cutoff_date]
    past_cancellations = cancellations[cancellations["invoice_date"] < cutoff_date]

    # One row per order, so that "frequency" counts orders and not invoice lines.
    orders = past.groupby(["customer_id", "invoice"]).agg(
        order_date=("invoice_date", "min"),
        order_total=("line_total", "sum"),
    ).reset_index()

    features = orders.groupby("customer_id").agg(
        first_order=("order_date", "min"),
        last_order=("order_date", "max"),
        frequency=("invoice", "count"),
        monetary=("order_total", "sum"),
    )
    features["recency_days"] = (cutoff_date - features["last_order"]).dt.days
    features["tenure_days"] = (cutoff_date - features["first_order"]).dt.days
    features["avg_order_value"] = features["monetary"] / features["frequency"]

    recent_orders = orders[orders["order_date"] >= cutoff_date - pd.Timedelta(days=90)]
    features["orders_last_90d"] = recent_orders.groupby("customer_id")["invoice"].count()

    features["distinct_products"] = past.groupby("customer_id")["stock_code"].nunique()

    cancelled_orders = past_cancellations.groupby("customer_id")["invoice"].nunique()
    features["cancel_rate"] = cancelled_orders / features["frequency"]

    # Most customers are from the UK; the rest are mostly wholesalers abroad.
    country = past.groupby("customer_id")["country"].agg(lambda c: c.mode()[0])
    features["is_uk"] = (country == "United Kingdom").astype(int)

    # Customers with no recent orders or no cancellations get NaN above -> 0.
    features = features.fillna({"orders_last_90d": 0, "cancel_rate": 0})
    return features[FEATURE_COLUMNS]


def build_labels(purchases, customer_ids, cutoff_date):
    """churned = 1 if the customer did not buy in the window after cutoff_date."""
    window_end = cutoff_date + pd.Timedelta(days=CHURN_WINDOW_DAYS)
    future = purchases[(purchases["invoice_date"] >= cutoff_date)
                       & (purchases["invoice_date"] < window_end)]
    buyers = set(future["customer_id"])
    churned = [0 if customer in buyers else 1 for customer in customer_ids]
    return pd.Series(churned, index=customer_ids, name="churned")


def main():
    engine = get_engine()
    purchases, cancellations = load_transactions(engine)

    last_date = purchases["invoice_date"].max().normalize() + pd.Timedelta(days=1)
    cutoff_date = last_date - pd.Timedelta(days=CHURN_WINDOW_DAYS)
    print(f"Data ends {last_date.date()}, cutoff date {cutoff_date.date()}")

    features = build_features(purchases, cancellations, cutoff_date)
    features = features[features["recency_days"] <= MAX_RECENCY_DAYS]
    features["churned"] = build_labels(purchases, features.index, cutoff_date)

    FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(FEATURES_PATH)
    print(f"{len(features):,} customers, churn rate {features['churned'].mean():.1%}")
    print(f"Saved {FEATURES_PATH}")


if __name__ == "__main__":
    main()
