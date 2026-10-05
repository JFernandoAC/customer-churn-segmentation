import pandas as pd

from build_features import build_features, build_labels

CUTOFF = pd.Timestamp("2011-06-01")


def make_purchases():
    rows = [
        # customer, invoice, date, total
        (1, "A1", "2011-01-10", 100.0),
        (1, "A2", "2011-05-20", 50.0),
        (1, "A3", "2011-07-01", 999.0),  # after the cutoff
        (2, "B1", "2010-12-01", 30.0),
    ]
    df = pd.DataFrame(rows, columns=["customer_id", "invoice", "invoice_date", "line_total"])
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    df["stock_code"] = "X"
    df["country"] = "United Kingdom"
    return df


def make_cancellations():
    df = pd.DataFrame({"customer_id": [1], "invoice": ["C1"],
                       "invoice_date": [pd.Timestamp("2011-02-01")]})
    return df


def test_features_ignore_purchases_after_cutoff():
    features = build_features(make_purchases(), make_cancellations(), CUTOFF)
    # The 999 order happened after the cutoff, so it must not be counted.
    assert features.loc[1, "monetary"] == 150.0
    assert features.loc[1, "frequency"] == 2


def test_recency_and_rates():
    features = build_features(make_purchases(), make_cancellations(), CUTOFF)
    assert features.loc[1, "recency_days"] == 12   # 20 May -> 1 June
    assert features.loc[1, "orders_last_90d"] == 1
    assert features.loc[1, "cancel_rate"] == 0.5   # 1 cancellation / 2 orders
    assert features.loc[2, "cancel_rate"] == 0


def test_label_looks_only_at_the_window_after_cutoff():
    labels = build_labels(make_purchases(), pd.Index([1, 2]), CUTOFF)
    assert labels[1] == 0  # bought on 1 July, inside the 90-day window
    assert labels[2] == 1  # never came back
