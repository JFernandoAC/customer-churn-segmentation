---
name: run-pipeline
description: Run the churn project end to end (Docker Postgres, data load, segmentation, features, training, SHAP, scoring, API) and check each step. Use when asked to run, rebuild, verify or debug the pipeline.
---

# Correr el pipeline completo

Todos los comandos desde la raíz del proyecto, con el venv activo
(`.venv\Scripts\activate` en Windows).

| # | Comando | Comprobación |
|---|---------|--------------|
| 1 | `docker compose up -d db` | `docker compose ps` muestra `db` como `healthy` |
| 2 | `python src/download_data.py` | `data/raw/online_retail_II.csv` con 1,033,036 filas |
| 3 | `python src/load_to_postgres.py` | imprime `clean_transactions has 776,583 rows` |
| 4 | `python src/segment_customers.py` | tabla de 4 segmentos + `reports/figures/choose_k.png` |
| 5 | `python src/build_features.py` | ~4,300 clientes, churn ~49% |
| 6 | `python src/train_model.py` | métricas de 2 modelos, guarda `models/churn_model.joblib` y las tablas `model_metrics` / `confusion_matrix` |
| 7 | `python src/explain_model.py` | 3 PNG `shap_*.png` en `reports/figures/` y la tabla `feature_importance` |
| 8 | `python src/score_customers.py` | tabla `customer_scores` + cruce segmento × riesgo |
| 9 | `pytest` | todas las pruebas pasan |
| 10 | `docker compose up -d --build api` | `curl http://localhost:8000/health` → `{"status":"ok"}` |
| 11 | `mlflow ui --backend-store-uri sqlite:///mlflow.db` | http://localhost:5000 muestra 2 corridas |
| 12 | Abrir `powerbi/ChurnDashboard.pbip` → *Actualizar* | 4 páginas; "Churn risk" muestra 746 clientes de riesgo alto y "Model" ROC-AUC 0.758 |

Los pasos 6-8 y 10 dependen del anterior: si reentrenas, reconstruye la API
(`--build`) para que copie el modelo nuevo.

## Errores comunes
- **`connection refused` en 5433**: Docker Desktop apagado o `db` no levantó.
  `docker compose logs db`.
- **`port is already allocated`**: algo más usa 5433/8000. Cambia el puerto del
  host en `docker-compose.yml` y en `.env`.
- **`password authentication failed`**: el volumen se creó con otra contraseña.
  `docker compose down -v` borra el volumen (y los datos cargados) y vuelve a
  empezar desde el paso 1.
- **La API no carga el modelo**: versiones distintas entre `.venv` y
  `requirements-api.txt`. Deben coincidir scikit-learn, xgboost, numpy y pandas.
- **`.env` no existe**: copia `.env.example` a `.env`.
- **Power BI pide credenciales al actualizar**: pestaña *Base de datos*,
  `retail` / `retail` (las guarda en tu usuario de Windows, no en el proyecto).
- **Power BI muestra tablas vacías**: es normal en un PBIP recién clonado (los
  datos viven en `cache.abf`, que no se sube a git). Presiona *Actualizar*.
