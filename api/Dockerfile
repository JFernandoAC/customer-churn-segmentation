# Same Python version used to train the model
FROM python:3.14-slim

# XGBoost needs the OpenMP library, which the slim image does not include
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first: Docker caches this layer, so changing the code
# does not reinstall every library.
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY api/ api/
COPY models/churn_model.joblib models/churn_model.joblib

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
