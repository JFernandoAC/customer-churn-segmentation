"""Group customers into segments using RFM (Recency, Frequency, Monetary) and KMeans."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from db import get_engine

N_CLUSTERS = 4  # chosen by looking at reports/figures/choose_k.png
RFM_COLUMNS = ["recency_days", "frequency", "monetary"]

RFM_QUERY = """
SELECT
    customer_id,
    (SELECT MAX(invoice_date)::date FROM clean_transactions) + 1 - MAX(invoice_date)::date AS recency_days,
    COUNT(DISTINCT invoice) AS frequency,
    SUM(line_total)         AS monetary
FROM clean_transactions
GROUP BY customer_id
"""


def prepare_for_kmeans(rfm):
    # RFM values are very skewed (a few customers spend 100x the median).
    # log1p squeezes the big values, and the scaler puts the three columns on
    # the same scale so no single one dominates the distances.
    log_rfm = np.log1p(rfm[RFM_COLUMNS])
    return StandardScaler().fit_transform(log_rfm)


def plot_choose_k(X):
    k_values = range(2, 9)
    inertias, silhouettes = [], []
    for k in k_values:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        inertias.append(kmeans.inertia_)
        silhouettes.append(silhouette_score(X, kmeans.labels_))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.plot(k_values, inertias, marker="o")
    ax1.set(title="Elbow method", xlabel="Number of clusters (k)", ylabel="Inertia")
    ax2.plot(k_values, silhouettes, marker="o")
    ax2.set(title="Silhouette score (higher is better)", xlabel="Number of clusters (k)")
    fig.tight_layout()
    fig.savefig("reports/figures/choose_k.png", dpi=120)
    plt.close(fig)


def name_segments(rfm):
    """Give each of the 4 clusters a business name based on its average RFM.

    The 2 clusters that bought most recently are "active", the other 2 are
    not. Inside each pair, the one that spends more gets the better name.
    """
    profile = rfm.groupby("cluster")[RFM_COLUMNS].mean().sort_values("recency_days")
    active = profile.iloc[:2].sort_values("monetary", ascending=False)
    inactive = profile.iloc[2:].sort_values("monetary", ascending=False)
    names = ["Champions", "Promising", "At risk", "Lost"]
    ordered_clusters = list(active.index) + list(inactive.index)
    return dict(zip(ordered_clusters, names))


def main():
    engine = get_engine()
    rfm = pd.read_sql(RFM_QUERY, engine)
    X = prepare_for_kmeans(rfm)

    plot_choose_k(X)

    kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=10, random_state=42).fit(X)
    rfm["cluster"] = kmeans.labels_
    rfm["segment"] = rfm["cluster"].map(name_segments(rfm))

    summary = rfm.groupby("segment").agg(
        customers=("customer_id", "count"),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    ).round(1)
    summary["revenue_share"] = (summary["total_revenue"] / summary["total_revenue"].sum()).round(3)
    print(summary.sort_values("avg_monetary", ascending=False).to_string())

    rfm.drop(columns="cluster").to_sql("customer_segments", engine, if_exists="replace", index=False)
    print("Saved table customer_segments")


if __name__ == "__main__":
    main()
