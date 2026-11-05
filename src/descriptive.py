"""Descriptive analysis of the analysis dataset (one row per company).

Outputs (results/):
  missing_values_by_year.csv    share of missing values per indicator and year
  descriptive_stats_2021.csv    mean, std, min, median, max of the 2021 variables
  figures/companies_by_size.png
  figures/companies_by_region.png
  figures/correlation_matrix.png
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from config import ANALYSIS_DATASET, FIGURES, RESULTS

VARS_2021 = ["roe_2021", "revenue_2021", "operating_result_2021", "net_income_2021",
             "equity_2021", "financial_debt_2021", "csr_score", "bert_sentiment_score"]
SIZE_LABELS = {"Petite ou Moyenne Entreprise": "SME",
               "Entreprise de Taille Intermédiaire": "Intermediate-size",
               "Grande Entreprise": "Large"}
REGION_LABELS = {
    "ile de france": "Île-de-France", "pays de la loire": "Pays de la Loire",
    "auvergne rhone alpes": "Auvergne-Rhône-Alpes", "hauts de france": "Hauts-de-France",
    "nouvelle aquitaine": "Nouvelle-Aquitaine", "provence alpes cote dazur": "Provence-Alpes-Côte d'Azur",
    "centre val de loire": "Centre-Val de Loire", "occitanie": "Occitanie", "bretagne": "Bretagne",
    "normandie": "Normandie", "grand est": "Grand Est", "bourgogne franche comte": "Bourgogne-Franche-Comté",
    "corse": "Corse"}
BLUE = "#4C72B0"


def missing_values(df):
    out = {}
    for col in df.columns:
        m = re.match(r"(.+?)_(20\d{2})$", col)
        if m:
            out.setdefault(m.group(2), {})[m.group(1)] = round(df[col].isna().mean() * 100, 1)
    table = pd.DataFrame(out).sort_index()
    table.to_csv(RESULTS / "missing_values_by_year.csv")
    return table


def bar(counts, title, xlabel, path):
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(counts) + 1.5))
    ax.barh(counts.index, counts.values, color=BLUE)
    ax.invert_yaxis()
    for i, v in enumerate(counts.values):
        ax.text(v + 0.5, i, str(v), va="center")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def correlation_matrix(df):
    corr = df[VARS_2021].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    shown = corr.mask(mask)
    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(shown, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(VARS_2021)), VARS_2021, rotation=45, ha="right")
    ax.set_yticks(range(len(VARS_2021)), VARS_2021)
    for i in range(len(VARS_2021)):
        for j in range(len(VARS_2021)):
            if not mask[i, j]:
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, shrink=0.8)
    ax.set_title("Correlation matrix (Pearson, pairwise complete observations)")
    plt.tight_layout()
    plt.savefig(FIGURES / "correlation_matrix.png", dpi=150)
    plt.close()


def main():
    df = pd.read_excel(ANALYSIS_DATASET)
    print(f"Companies in the analysis dataset: {len(df)}")

    print("\nMissing values (%) by indicator and year:")
    print(missing_values(df))

    desc = df[VARS_2021].agg(["count", "mean", "std", "min", "median", "max"]).T.round(3)
    desc.to_csv(RESULTS / "descriptive_stats_2021.csv")
    print("\nDescriptive statistics (2021, amounts in million euros):")
    print(desc)

    sizes = df["size_category"].map(SIZE_LABELS).value_counts()
    bar(sizes, "Mission-driven companies by size", "Number of companies",
        FIGURES / "companies_by_size.png")
    regions = df["region"].map(REGION_LABELS).fillna(df["region"]).value_counts()
    bar(regions, "Mission-driven companies by region", "Number of companies",
        FIGURES / "companies_by_region.png")
    correlation_matrix(df)
    print(f"\nFigures saved to {FIGURES}")


if __name__ == "__main__":
    main()
