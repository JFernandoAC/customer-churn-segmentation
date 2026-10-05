# Predicción de abandono (churn) y segmentación de clientes — Online Retail II

[English version](README.md)

Una tienda en línea de regalos vende sobre todo a mayoristas. Los clientes nunca
"cancelan": simplemente dejan de pedir. Este proyecto responde dos preguntas con
dos años de ventas reales (1 millón de líneas de factura, 5,852 clientes):

1. **¿Quiénes son nuestros clientes?** Cuatro grupos con significado de negocio.
2. **¿Quién está por dejar de comprar?** Una probabilidad de abandono para cada
   cliente activo, con las razones detrás.

## Hallazgos principales

- **El 21% de los clientes genera el 74% de los ingresos.** Estos *Champions*
  piden cada pocas semanas (19 pedidos en promedio) y gastan ~£10,500 cada uno.
- **1,444 clientes están *At risk* (en riesgo):** antes pedían con regularidad
  (5 pedidos, ~£2,000 cada uno) pero llevan ~7 meses sin comprar en promedio.
- **Qué tan reciente y qué tan seguido compra un cliente** son, por mucho, las
  señales más fuertes de abandono. Alguien que compró un solo producto, una sola
  vez, hace once meses, tiene 97% de probabilidad de no volver.
- El modelo ordena a un cliente que se va por encima de uno que se queda **el 76%
  de las veces** (ROC-AUC 0.76 en clientes que nunca vio), usando solo el
  historial de compras.

| Segmento | Clientes | Días prom. desde última compra | Pedidos prom. | Gasto prom. | % de ingresos |
|----------|---------:|------:|------:|---------:|------:|
| Champions | 1,201 | 28 | 19.0 | £10,470 | 73.7% |
| At risk | 1,444 | 230 | 5.0 | £1,966 | 16.6% |
| Promising | 1,254 | 29 | 3.0 | £829 | 6.1% |
| Lost | 1,953 | 396 | 1.4 | £316 | 3.6% |

![Ingresos por segmento](reports/figures/eda_segments_revenue.png)

## Recomendación

De los 4,271 clientes que compraron en el último año, 746 tienen riesgo alto de
irse en los próximos 90 días. No todos valen lo mismo:

- **Priorizar a los 760 clientes *At risk* con riesgo medio o alto.** Ya
  demostraron que compran con regularidad; recuperarlos es lo que más rinde.
- **Dar atención personalizada a los 50 *Champions* con riesgo medio/alto.** Cada
  uno vale ~£10,000.
- **No gastar presupuesto de retención en los *Lost* de riesgo alto.** Compraron
  poco y lo más probable es que ya se fueron.

## Qué provoca el abandono

![SHAP beeswarm](reports/figures/shap_beeswarm.png)

Cada punto es un cliente. Los puntos a la derecha empujan hacia el abandono; rojo
significa un valor alto de esa variable. Mucho tiempo sin comprar empuja al
abandono; muchos pedidos, gasto alto, actividad reciente y una canasta variada
retienen al cliente.

## Dashboard

Un reporte de Power BI de tres páginas lleva esto al negocio: quiénes son los
clientes, quién está en riesgo y una lista de acción con los clientes de riesgo
alto ordenados por cuánto valen.

![Página de riesgo de abandono](reports/figures/powerbi_churn_risk.png)

Más páginas: [Segmentos](reports/figures/powerbi_segments.png) ·
[Lista de acción](reports/figures/powerbi_action_list.png)

---

## Detalles técnicos

### Flujo

```
Excel de UCI ─► CSV ─► PostgreSQL (Docker) ─► vista SQL de limpieza
                                            ├─► RFM + KMeans ─► customer_segments
                                            └─► features + etiqueta de churn ─► LogReg vs XGBoost (MLflow)
                                                                                 ├─► gráficas SHAP
                                                                                 ├─► FastAPI /predict (Docker)
                                                                                 └─► customer_scores ─► Power BI
```

| Paso | Archivo | Qué hace |
|------|---------|----------|
| 1 | `docker-compose.yml` | PostgreSQL 16 (puerto 5433 del host) y la API |
| 2 | `src/download_data.py` | Descarga el dataset, une las dos hojas, quita 34,335 filas duplicadas |
| 3 | `src/load_to_postgres.py`, `sql/` | Carga 1,033,036 filas; una vista deja 776,583 compras válidas |
| 4 | `notebooks/eda.ipynb`, `sql/03_eda_queries.sql` | Análisis exploratorio |
| 5 | `src/segment_customers.py` | RFM → logaritmo + escalado → KMeans (k=4) |
| 6 | `src/build_features.py` | 9 variables de comportamiento y la etiqueta de churn |
| 7 | `src/train_model.py` | Regresión logística vs XGBoost, validación cruzada de 5 partes, registrado en MLflow |
| 8 | `src/explain_model.py` | Explicaciones SHAP globales y por cliente |
| 9 | `src/score_customers.py` | Califica a los clientes actuales en Postgres para Power BI |
| 10 | `api/` | Servicio FastAPI con el modelo entrenado |
| 11 | `powerbi/ChurnDashboard.pbip` | Dashboard de Power BI (3 páginas) que lee de Postgres |

### Definición de churn

No hay suscripción, así que churn se define con una fecha de corte: **un cliente
hizo churn si no compró nada en los 90 días siguientes al corte** (11-sep-2011).
Las variables usan solo datos anteriores al corte, lo que evita la fuga de datos
(probado en `tests/test_features.py`). Solo entran clientes que compraron en el
año previo al corte: predecir a alguien inactivo desde hace dos años es trivial e
infla las métricas. Resultado: 4,306 clientes, 49% de churn.

### Resultados del modelo (conjunto de prueba, 862 clientes)

| Modelo | ROC-AUC CV | ROC-AUC prueba | PR-AUC prueba | Precision | Recall | F1 |
|--------|-----------:|---------------:|--------------:|----------:|-------:|---:|
| Regresión logística (log + escalado) | 0.762 | 0.754 | 0.717 | 0.670 | 0.722 | 0.695 |
| **XGBoost** | **0.770** | **0.758** | 0.712 | 0.679 | 0.715 | 0.697 |

El modelo se elige por validación cruzada, no por el conjunto de prueba. XGBoost
gana por menos de 0.01 de AUC; la línea base simple es casi igual de buena, lo
cual vale la pena saber: casi toda la señal está en la recencia y la frecuencia.

### Decisiones clave

- **Vista SQL para limpiar** — las reglas viven en un archivo
  (`sql/02_clean_view.sql`) y se pueden cambiar sin recargar datos.
- **Logaritmo + escalado antes de KMeans** — sin el logaritmo, KMeans aísla a 42
  clientes extremos en dos grupos diminutos y mete a 3,830 en uno solo.
- **k = 4** — k=2 tiene mejor silhouette pero no es accionable; k=4 es un máximo
  local ([gráfica](reports/figures/choose_k.png)).
- **La misma función `build_features` para entrenar y para calificar** — evita
  que las variables se calculen distinto en cada lado.
- **La API fija las versiones de librerías del entrenamiento** — el modelo es un
  pickle; debe cargarse con las mismas versiones de scikit-learn/XGBoost.
- **Power BI como proyecto PBIP** — el reporte y su modelo (medidas en TMDL,
  visuales en PBIR) son archivos de texto, así que el dashboard se versiona y se
  revisa en git como el código.

### Limitaciones

- La ventana de 90 días de la etiqueta (sep–dic 2011) es la temporada navideña,
  así que el churn medido probablemente es menor que en una temporada tranquila.
  Con más años de datos usaría varios cortes.
- Solo hay historial de compras: sin visitas al sitio, tickets de soporte ni datos
  de satisfacción, lo que limita la precisión alcanzable.
- El umbral de 0.5 y los niveles de riesgo 0.4/0.7 no están ajustados a costos
  reales de campaña.

### Cómo correrlo

Requisitos: Docker Desktop y Python 3.14.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate en Linux/Mac)
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

Dashboard: abre `powerbi/ChurnDashboard.pbip` en Power BI Desktop y presiona
*Actualizar* (usuario y contraseña de Postgres: `retail` / `retail`, del `.env`).

Ejemplo de petición:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"recency_days": 300, "frequency": 1, "monetary": 80, "avg_order_value": 80,
       "tenure_days": 300, "distinct_products": 2, "orders_last_90d": 0,
       "cancel_rate": 0, "is_uk": 1}'
# {"churn_probability": 0.944, "will_churn": true}
```

### Datos

[Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii),
UCI Machine Learning Repository, donado por Daqing Chen. Licencia: CC BY 4.0.
