from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

LOYAL_CUSTOMER = {
    "recency_days": 5, "frequency": 40, "monetary": 25000, "avg_order_value": 625,
    "tenure_days": 700, "distinct_products": 300, "orders_last_90d": 8,
    "cancel_rate": 0.05, "is_uk": 1,
}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_predict_returns_probability():
    response = client.post("/predict", json=LOYAL_CUSTOMER)
    assert response.status_code == 200
    assert 0 <= response.json()["churn_probability"] <= 1


def test_loyal_customer_is_less_risky_than_one_time_buyer():
    one_time_buyer = {**LOYAL_CUSTOMER, "recency_days": 300, "frequency": 1, "monetary": 80,
                      "avg_order_value": 80, "tenure_days": 300, "distinct_products": 2,
                      "orders_last_90d": 0}
    loyal = client.post("/predict", json=LOYAL_CUSTOMER).json()["churn_probability"]
    one_time = client.post("/predict", json=one_time_buyer).json()["churn_probability"]
    assert loyal < one_time


def test_negative_values_are_rejected():
    response = client.post("/predict", json={**LOYAL_CUSTOMER, "recency_days": -1})
    assert response.status_code == 422
