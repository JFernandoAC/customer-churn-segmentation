"""Build the Spanish report (ChurnDashboardES) from the English one.

The English report is the source of truth. This script copies it, points the
visuals to the Spanish label columns of the shared semantic model (segment_es,
risk_level_es, ...) and translates every visible text with the SPANISH table.

Run from the project root with Power BI Desktop closed:
    python powerbi/make_spanish_report.py
"""
import json
import shutil
import uuid
from pathlib import Path

ENGLISH_REPORT = Path("powerbi/ChurnDashboard.Report")
SPANISH_REPORT = Path("powerbi/ChurnDashboardES.Report")

# Columns with a Spanish twin in the semantic model (built in M)
SPANISH_COLUMNS = {
    ("customer_segments", "segment"): "segment_es",
    ("customer_scores", "segment"): "segment_es",
    ("customer_scores", "risk_level"): "risk_level_es",
    ("confusion_matrix", "actual"): "actual_es",
    ("confusion_matrix", "predicted"): "predicted_es",
    ("model_metrics", "model"): "model_es",
    ("model_metrics", "metric"): "metric_es",
    ("feature_importance", "feature_label"): "feature_label_es",
}

SPANISH = {
    # Page names
    "Segments": "Segmentos",
    "Churn risk": "Riesgo de churn",
    "Action list": "Lista de acción",
    "Model": "Modelo",
    # Banners
    "Who are our customers?  4 segments from RFM + KMeans  (Online Retail II, Dec 2009 - Dec 2011)":
        "¿Quiénes son nuestros clientes?  4 segmentos con RFM + KMeans  (Online Retail II, dic 2009 - dic 2011)",
    "Who is about to stop buying?  Churn risk in the next 90 days (customers active in the last year)":
        "¿Quién está por dejar de comprar?  Riesgo de churn en los próximos 90 días (clientes activos en el último año)",
    "Action list: high-risk customers (churn probability ≥ 70%), most valuable first":
        "Lista de acción: clientes de riesgo alto (probabilidad de churn ≥ 70%), los más valiosos primero",
    "How good is the churn model?  Logistic regression vs XGBoost, tested on 862 customers it never saw":
        "¿Qué tan bueno es el modelo de churn?  Regresión logística vs XGBoost, probado con 862 clientes que nunca vio",
    # Visual titles
    "Customers": "Clientes",
    "Revenue (2 years)": "Ingresos (2 años)",
    "Avg spend per customer": "Gasto promedio por cliente",
    "Avg orders per customer": "Pedidos promedio por cliente",
    "Share of customers vs share of revenue": "% de clientes vs % de ingresos",
    "Segment profile": "Perfil de cada segmento (días, pedidos y gasto: promedio por cliente)",
    "Each dot is a customer: how recently and how much they bought":
        "Cada punto es un cliente: qué tan reciente y cuánto compró",
    "Total spend (£, log scale)": "Gasto total (£, escala logarítmica)",
    "High risk customers (≥ 70%)": "Clientes de riesgo alto (≥ 70%)",
    "% of customers at high risk": "% de clientes en riesgo alto",
    "Historic spend of high-risk customers": "Gasto histórico de los clientes de riesgo alto",
    "Customers scored": "Clientes evaluados",
    "Customers by segment and churn risk": "Clientes por segmento y riesgo de churn",
    "Average churn probability by segment": "Probabilidad promedio de churn por segmento",
    "How churn probability is spread (10-point bands)": "Cómo se reparte la probabilidad de churn (bandas de 10 puntos)",
    "Customers to contact": "Clientes a contactar",
    "Their historic spend": "Su gasto histórico",
    "High-risk customers sorted by total spend": "Clientes de riesgo alto ordenados por gasto total",
    "XGBoost test ROC-AUC": "ROC-AUC de XGBoost (prueba)",
    "CV ROC-AUC gain over logistic regression": "Mejora de ROC-AUC (CV) vs reg. logística",
    "Churners caught (recall)": "Clientes que se fueron y detectó (recall)",
    "Churn alerts that were right (precision)": "Alertas de churn acertadas (precisión)",
    "Logistic regression vs XGBoost": "Regresión logística vs XGBoost",
    "Confusion matrix (XGBoost, 862 test customers)": "Matriz de confusión (XGBoost, 862 clientes de prueba)",
    "What the model relies on (mean |SHAP value|)": "En qué se basa el modelo (|valor SHAP| promedio)",
    # Field names shown in headers, legends and tooltips
    "Segment": "Segmento",
    "Risk level": "Nivel de riesgo",
    "Customer": "Cliente",
    "customer_id": "Cliente",
    "Churn probability": "Probabilidad de churn",
    "Churn probability band": "Banda de probabilidad de churn",
    "Days since last order": "Días sin comprar",
    "Orders": "Pedidos",
    "Total spend": "Gasto total",
    "Avg order value": "Ticket promedio",
    "Days as customer": "Días como cliente",
    "Orders last 90 days": "Pedidos 90 días",
    "Distinct products": "Productos distintos",
    "Actual": "Real",
    "Predicted": "Predicción",
    "Metric": "Métrica",
    "Score": "Valor",
    "Feature": "Variable",
    "Mean |SHAP value|": "|Valor SHAP| promedio",
    # Measure names (used when a field has no display name of its own)
    "Revenue": "Ingresos",
    "Revenue share": "% de ingresos",
    "Customer share": "% de clientes",
    "Avg days since last order": "Días sin comprar",
    "Avg orders": "Pedidos",
    "Avg spend": "Gasto",
    "High risk customers": "Clientes de riesgo alto",
    "% high risk": "% en riesgo alto",
    "Revenue at risk": "Gasto histórico en riesgo",
    "Avg churn probability": "Probabilidad promedio de churn",
    "Test customers": "Clientes de prueba",
    "Selected test ROC-AUC": "ROC-AUC (prueba)",
    "Selected recall": "Recall",
    "Selected precision": "Precisión",
    "CV ROC-AUC gain over baseline": "Mejora en ROC-AUC (CV)",
    # Data values used in colors and filters (same labels as the M steps)
    "Champions": "Campeones",
    "Promising": "Prometedores",
    "At risk": "En riesgo",
    "Lost": "Perdidos",
    "High": "Alto",
    "Medium": "Medio",
    "Low": "Bajo",
    "Logistic regression": "Regresión logística",
}

missing = set()


def to_spanish(text):
    if text not in SPANISH:
        missing.add(text)
        return text
    return SPANISH[text]


def translate_literal(value):
    """Literals look like "'Customers'" (with quotes). Only translate known texts."""
    if value.startswith("'") and value[1:-1] in SPANISH:
        return "'" + SPANISH[value[1:-1]] + "'"
    return value


def switch_column(field, aliases):
    """Point a column reference to its Spanish twin, if it has one."""
    column = field.get("Column")
    if not column:
        return
    # Filters name the table through an alias ("Source": "c"), visuals by its name
    source = column["Expression"]["SourceRef"]
    entity = source.get("Entity") or aliases.get(source.get("Source"))
    spanish_name = SPANISH_COLUMNS.get((entity, column["Property"]))
    if spanish_name:
        column["Property"] = spanish_name


def translate(node, is_text=False, aliases=None):
    """Walk the visual JSON. is_text marks a title or shape text, which must be translated."""
    aliases = aliases or {}
    if isinstance(node, list):
        for item in node:
            translate(item, is_text, aliases)
        return
    if not isinstance(node, dict):
        return

    if "From" in node:
        aliases = {source["Name"]: source["Entity"] for source in node["From"]}

    if "Column" in node:
        switch_column(node, aliases)

    # One field of a visual: fix its query names and give it a Spanish display name
    if "queryRef" in node and "field" in node:
        field = node["field"]
        switch_column(field, aliases)
        ref = field.get("Column") or field.get("Measure") or field.get("Aggregation", {}).get("Expression", {}).get("Column")
        entity = ref["Expression"]["SourceRef"]["Entity"]
        if "Column" in field:
            node["queryRef"] = f"{entity}.{field['Column']['Property']}"
            node["nativeQueryRef"] = field["Column"]["Property"]
        node["displayName"] = to_spanish(node.get("displayName") or ref["Property"])

    for child_key, child in node.items():
        if child_key == "Value" and isinstance(child, str):
            node[child_key] = translate_literal(child)
            if is_text and node[child_key] == child:
                missing.add(child)
        else:
            text_property = child_key == "text" and isinstance(child, dict) and "expr" in child
            translate(child, is_text or text_property, aliases)


def build():
    # Start from a fresh copy so visuals deleted in English also disappear here
    if (SPANISH_REPORT / "definition").exists():
        shutil.rmtree(SPANISH_REPORT / "definition")
    shutil.copytree(ENGLISH_REPORT / "definition", SPANISH_REPORT / "definition")
    shutil.copytree(ENGLISH_REPORT / "StaticResources", SPANISH_REPORT / "StaticResources", dirs_exist_ok=True)
    shutil.copy(ENGLISH_REPORT / "definition.pbir", SPANISH_REPORT / "definition.pbir")

    # Power BI needs a different id for each report
    platform = SPANISH_REPORT / ".platform"
    if not platform.exists():
        data = json.loads((ENGLISH_REPORT / ".platform").read_text(encoding="utf-8"))
        data["metadata"]["displayName"] = "ChurnDashboardES"
        data["config"]["logicalId"] = str(uuid.uuid4())
        platform.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    pages = SPANISH_REPORT / "definition" / "pages"
    for path in list(pages.glob("*/page.json")) + list(pages.glob("*/visuals/*/visual.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "page.json":
            data["displayName"] = to_spanish(data["displayName"])
        translate(data)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pbip = Path("powerbi/ChurnDashboardES.pbip")
    project = json.loads(Path("powerbi/ChurnDashboard.pbip").read_text(encoding="utf-8"))
    project["artifacts"][0]["report"]["path"] = SPANISH_REPORT.name
    pbip.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")

    if missing:
        print("Not translated (add them to SPANISH):")
        for text in sorted(missing):
            print("  ", text)
    else:
        print(f"Spanish report written to {SPANISH_REPORT}")


if __name__ == "__main__":
    build()
