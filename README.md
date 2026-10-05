# Customer churn and segmentation (Online Retail II)

[Versión en español](README.es.md)

In this project I use two years of sales from an online gift shop (about 1
million invoice lines and 5,852 customers). Most of its customers are
wholesalers. They don't cancel a subscription, they just stop ordering, so
the shop doesn't really know who it is losing.

I wanted to answer two questions:

1. What kinds of customers does the shop have?
2. Which active customers are likely to stop buying, and why?

## Main findings

- 21% of the customers (the *Champions* group) bring 74% of the revenue. They
  order every few weeks (19 orders on average) and spend about £10,500 each.
- 1,444 customers are in the *At risk* group. They used to order regularly (5
  orders, about £2,000 each), but on average they haven't bought anything in
  about 7 months.
- The strongest signals of churn are how recently and how often a customer
  buys. For example, a customer who bought one product, one time, eleven months
  ago has a 97% chance of not coming back.
- The model gets a ROC-AUC of 0.76 on customers it never saw during training.
  This means that if I pick one customer who left and one who stayed, the model
  gives a higher score to the one who left 76% of the time. It only uses
  purchase history.

| Segment | Customers | Avg. days since last order | Avg. orders | Avg. spend | Share of revenue |
|---------|---------:|------:|------:|---------:|------:|
| Champions | 1,201 | 28 | 19.0 | £10,470 | 73.7% |
| At risk | 1,444 | 230 | 5.0 | £1,966 | 16.6% |
| Promising | 1,254 | 29 | 3.0 | £829 | 6.1% |
| Lost | 1,953 | 396 | 1.4 | £316 | 3.6% |

![Share of revenue by segment](reports/figures/eda_segments_revenue.png)

## Recommendation

4,271 customers bought something in the last year. The model gives 746 of them
a high risk of leaving in the next 90 days (probability of 0.7 or more). I
think the shop should not treat all of them the same:

- Focus first on the *At risk* group: 760 of them have medium or high risk.
  They already showed that they buy regularly, so winning them back is worth
  the most.
- Contact the 50 *Champions* with medium or high risk personally, because each
  one is worth about £10,000.
- Don't spend retention money on *Lost* customers with high risk. They bought
  very little and they are probably already gone.

## What drives churn

![SHAP beeswarm](reports/figures/shap_beeswarm.png)

I used SHAP to see which features push the prediction up or down. Each dot is
a customer. Dots on the right push towards churn, and red means the feature
has a high value for that customer. A long time since the last order pushes
towards churn. Many orders, high spend, recent activity and buying many
different products make a customer more likely to stay.

## Dashboard

I built a Power BI report with four pages: the customer segments, churn risk,
an action list with the high-risk customers sorted by how much they spend, and
a page that shows how good the model is.

![Churn risk page](reports/figures/powerbi_churn_risk.png)

Other pages: [Segments](reports/figures/powerbi_segments.png),
[Action list](reports/figures/powerbi_action_list.png),
[Model](reports/figures/powerbi_model.png)

There is also a Spanish version of the dashboard (`powerbi/ChurnDashboardES.pbip`,
see [README.es.md](README.es.md)).

---

## Technical details

### Steps

1. Download the Excel file from UCI and save it as CSV.
2. Load the CSV into PostgreSQL (running in Docker) and clean it with a SQL view.
3. Group customers with RFM + KMeans and save them to `customer_segments`.
4. Build features and the churn label, then train logistic regression and
   XGBoost (runs tracked in MLflow).
5. Use the best model for SHAP plots, a FastAPI `/predict` endpoint, and to
   score current customers into `customer_scores`.
6. Power BI reads `customer_segments` and `customer_scores` from Postgres.

| Step | File | What it does |
|------|------|--------------|
| 1 | `docker-compose.yml` | PostgreSQL 16 (host port 5433) and the API |
| 2 | `src/download_data.py` | Downloads the dataset, joins both sheets and removes 34,335 duplicated rows |
| 3 | `src/load_to_postgres.py`, `sql/` | Loads 1,033,036 rows; a view keeps 776,583 valid purchases |
| 4 | `notebooks/eda.ipynb`, `sql/03_eda_queries.sql` | Exploratory analysis |
| 5 | `src/segment_customers.py` | RFM, then log + standard scaling, then KMeans (k=4) |
| 6 | `src/build_features.py` | 9 behaviour features and the churn label |
| 7 | `src/train_model.py` | Logistic regression vs XGBoost with 5-fold CV, tracked in MLflow |
| 8 | `src/explain_model.py` | SHAP plots for the whole model and for one customer |
| 9 | `src/score_customers.py` | Scores current customers and saves them in Postgres for Power BI |
| 10 | `api/` | FastAPI service with the trained model |
| 11 | `powerbi/ChurnDashboard.pbip` | Power BI dashboard (4 pages) that reads from Postgres |
| 12 | `powerbi/make_spanish_report.py` | Creates the Spanish copy of the report (`ChurnDashboardES.pbip`) |

### How I defined churn

There is no subscription, so I used a cutoff date (11 Sep 2011). A customer
churned if they didn't buy anything in the 90 days after the cutoff. The
features only use data from before the cutoff, so the model can't see the
future (there is a test for this in `tests/test_features.py`).

I only kept customers who bought something in the year before the cutoff. If I
included people who have been inactive for two years, they would be very easy
to predict and the metrics would look better than they really are. In the end
I had 4,306 customers and 49% of them churned.

### Model results (test set, 862 customers)

| Model | CV ROC-AUC | Test ROC-AUC | Test PR-AUC | Precision | Recall | F1 |
|-------|-----------:|-------------:|------------:|----------:|-------:|---:|
| Logistic regression (log + scaler) | 0.762 | 0.754 | 0.717 | 0.670 | 0.722 | 0.695 |
| XGBoost (selected) | 0.770 | 0.758 | 0.712 | 0.679 | 0.715 | 0.697 |

I chose the model with cross-validation, not with the test set. XGBoost won,
but by less than 0.01 AUC. The logistic regression is almost as good, which
tells me that most of the information is in recency and frequency.

### Decisions I made

- I put all the cleaning rules in one SQL view (`sql/02_clean_view.sql`), so I
  can change a rule without loading the data again.
- I applied a log and scaling before KMeans. Without the log, KMeans put 42
  extreme customers in two tiny clusters and 3,830 customers in one big cluster.
- I used k=4. k=2 had a better silhouette score, but two groups are not very
  useful for the business, and k=4 is a local maximum
  ([chart](reports/figures/choose_k.png)).
- Training and scoring use the same `build_features` function, so the features
  are calculated the same way in both places.
- The API uses the same scikit-learn and XGBoost versions as training, because
  the model is saved as a pickle and may not load with other versions.
- I saved the Power BI dashboard as a PBIP project. The measures (TMDL) and
  visuals (PBIR) are text files, so I can track changes in git like the code.
- The Spanish report is generated from the English one. Both use the same
  semantic model, the Spanish labels are extra columns made in Power Query, and
  a script copies the English report and translates it. This way I only edit
  one report.

### Limitations

- The 90 days after the cutoff (Sep to Dec 2011) are the Christmas season, so
  churn is probably lower than in a normal period. With more years of data I
  would use several cutoff dates.
- I only have purchase history. There is no data about website visits, support
  tickets or customer satisfaction, and that limits how good the model can get.
- The 0.5 threshold and the 0.4/0.7 risk levels are not based on real campaign
  costs.

### How to run it

You need Docker Desktop and Python 3.14.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
cp .env.example .env

docker compose up -d db
python src/download_data.py
python src/load_to_postgres.py
python src/segment_customers.py
python src/build_features.py
python src/train_model.py
python src/explain_model.py
python src/score_customers.py
pytest

docker compose up -d --build api   # http://localhost:8000/docs
mlflow ui --backend-store-uri sqlite:///mlflow.db   # http://localhost:5000
```

Dashboard: open `powerbi/ChurnDashboard.pbip` in Power BI Desktop and click
*Refresh* (Postgres user and password are `retail` / `retail`, from `.env`).
The Spanish version is `powerbi/ChurnDashboardES.pbip`. If you change the
English report, run `python powerbi/make_spanish_report.py` with Desktop closed
to update the Spanish one.

Example request:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"recency_days": 300, "frequency": 1, "monetary": 80, "avg_order_value": 80,
       "tenure_days": 300, "distinct_products": 2, "orders_last_90d": 0,
       "cancel_rate": 0, "is_uk": 1}'
# {"churn_probability": 0.944, "will_churn": true}
```

### Data

[Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
from the UCI Machine Learning Repository, donated by Daqing Chen. License: CC BY 4.0.
