"""Explain the churn model with SHAP: which features push a customer to churn."""
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import shap

from build_features import FEATURE_COLUMNS
from train_model import MODEL_PATH, TEST_PATH

FIGURES = "reports/figures"


def save_current_figure(name):
    plt.savefig(f"{FIGURES}/{name}", dpi=120, bbox_inches="tight")
    plt.close()


def main():
    # TreeExplainer works for tree models like XGBoost, which won training.
    model = joblib.load(MODEL_PATH)
    X_test = pd.read_csv(TEST_PATH, index_col="customer_id")[FEATURE_COLUMNS].astype(float)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)

    # Global view 1: average impact of each feature (bigger bar = more important)
    shap.plots.bar(shap_values, show=False)
    save_current_figure("shap_importance.png")

    # Global view 2: one dot per customer. Red = high feature value, blue = low.
    # Dots to the right push towards churn, to the left towards staying.
    shap.plots.beeswarm(shap_values, show=False)
    save_current_figure("shap_beeswarm.png")

    # Local view: why the model gave THIS customer their score.
    probabilities = model.predict_proba(X_test)[:, 1]
    riskiest = probabilities.argmax()
    print(f"Customer {X_test.index[riskiest]} has churn probability {probabilities[riskiest]:.1%}")
    shap.plots.waterfall(shap_values[riskiest], show=False)
    save_current_figure("shap_waterfall_one_customer.png")

    print(f"Saved SHAP plots to {FIGURES}/")


if __name__ == "__main__":
    main()
