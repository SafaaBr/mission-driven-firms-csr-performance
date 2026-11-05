"""Step 5 - Financial indicators from Pappers (one page per SIREN).

Collects revenue, net income, operating result, equity, financial debt,
return on equity and return on assets for every available year, and
computes ROE = net income / equity * 100.
Output: data/interim/financials/financials_batch_*.xlsx (not published).
Requires Chrome + Selenium. Collected in 2025.
"""
import math
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANY_SIREN, FINANCIALS_DIR

INDICATORS = [
    "chiffre d'affaires (€)",
    "résultat net (€)",
    "résultat d'exploitation (€)",
    "fonds propres (€)",
    "dettes financières (€)",
    "rentabilité sur fonds propres (%)",
    "rentabilité économique (%)",
]
BATCH_SIZE = 100


def parse_amount(value):
    """'1,2 M' -> 1.2 ; '350 k' -> 0.35 ; '2 Md' -> 2000 (unit: million euros)."""
    if not value:
        return None
    v = value.replace(",", ".").replace(" ", "").upper()
    try:
        if "MDS" in v or "MD" in v:
            return float(v.replace("MDS", "").replace("MD", "")) * 1000
        if "M" in v:
            return float(v.replace("M", ""))
        if "K" in v:
            return float(v.replace("K", "")) / 1000
        return float(v)
    except ValueError:
        return None


def extract(driver, siren):
    driver.get(f"https://www.pappers.fr/entreprise/{siren}")
    time.sleep(5)
    try:
        driver.find_element(By.CLASS_NAME, "close-btn").click()
        time.sleep(1)
    except Exception:
        pass
    for _ in range(45):  # scroll to load the ratio tables
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.25)
    try:
        name = driver.find_element(By.XPATH, "//h1").text.strip()
    except Exception:
        name = None

    rows = []
    for table in driver.find_elements(By.XPATH, "//div[@class='ratios']//table"):
        years = [int(th.text.strip()) for th in table.find_elements(By.XPATH, ".//tr[@class='tr-header']/th")[1:]
                 if th.text.strip().isdigit()]
        for tr in table.find_elements(By.TAG_NAME, "tr"):
            try:
                label = tr.find_element(By.TAG_NAME, "th").text.strip().lower()
            except Exception:
                continue
            if label not in INDICATORS:
                continue
            for i, td in enumerate(tr.find_elements(By.TAG_NAME, "td")[:len(years)]):
                rows.append({"SIREN": siren, "Nom": name, "Année": years[i],
                             "Indicateur": label, "Valeur": parse_amount(td.text.strip())})

    # ROE computed from net income and equity
    df = pd.DataFrame(rows)
    if not df.empty:
        for year, sub in df.groupby("Année"):
            ni = sub.loc[sub["Indicateur"] == "résultat net (€)", "Valeur"]
            eq = sub.loc[sub["Indicateur"] == "fonds propres (€)", "Valeur"]
            if len(ni) and len(eq) and pd.notna(ni.iloc[0]) and pd.notna(eq.iloc[0]) and eq.iloc[0] != 0:
                rows.append({"SIREN": siren, "Nom": name, "Année": year,
                             "Indicateur": "roe calculé (%)",
                             "Valeur": round(ni.iloc[0] / eq.iloc[0] * 100, 2)})
    return rows


def main():
    sirens = pd.read_csv(COMPANY_SIREN)["SIREN"].dropna().astype(int).astype(str).str.zfill(9).tolist()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=Options())
    for b in range(math.ceil(len(sirens) / BATCH_SIZE)):
        batch = sirens[b * BATCH_SIZE:(b + 1) * BATCH_SIZE]
        print(f"Batch {b + 1}: {len(batch)} companies")
        rows = [r for s in batch for r in extract(driver, s)]
        pd.DataFrame(rows).to_excel(FINANCIALS_DIR / f"financials_batch_{b + 1}.xlsx", index=False)
    driver.quit()


if __name__ == "__main__":
    main()
