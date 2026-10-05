"""Small API that returns the churn probability of a customer."""
import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

MODEL_PATH = os.getenv("MODEL_PATH", "models/churn_model.joblib")

app = FastAPI(title="Customer churn API")
model = joblib.load(MODEL_PATH)  # loaded once at startup, not on every request


class Customer(BaseModel):
    # Field(ge=0) rejects negative numbers with a clear 422 error.
    recency_days: float = Field(ge=0, description="Days since the last order")
    frequency: float = Field(ge=1, description="Number of orders")
    monetary: float = Field(ge=0, description="Total spent")
    avg_order_value: float = Field(ge=0)
    tenure_days: float = Field(ge=0, description="Days since the first order")
    distinct_products: float = Field(ge=1)
    orders_last_90d: float = Field(ge=0)
    cancel_rate: float = Field(ge=0, description="Cancelled orders / orders")
    is_uk: int = Field(ge=0, le=1)


class Prediction(BaseModel):
    churn_probability: float
    will_churn: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(customer: Customer):
    # The model was trained on a DataFrame, so it expects the same column
    # names in the same order. model_dump() keeps the order of the class.
    row = pd.DataFrame([customer.model_dump()]).astype(float)
    probability = float(model.predict_proba(row)[0, 1])
    return Prediction(churn_probability=round(probability, 4), will_churn=probability >= 0.5)
