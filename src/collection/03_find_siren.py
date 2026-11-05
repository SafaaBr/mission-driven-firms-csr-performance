"""Step 3 - SIREN number of each company (annuaire-entreprises.data.gouv.fr).

Searches each company name and keeps the SIREN of the first result.
Output: data/raw/company_siren.csv (the published file was then completed
with sector, region and dates, and checked by hand).
Requires Chrome + Selenium. Collected in 2025.
"""
import re
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANIES_LIST, INTERIM


def clean_name(name):
    name = re.sub(r"[^a-zA-Z0-9\s-]", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()


def main():
    with open(COMPANIES_LIST, encoding="utf-8") as f:
        companies = [line.strip() for line in f if line.strip()]

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    results = []
    try:
        for company in companies:
            print(f"Searching: {company}")
            search_url = ("https://annuaire-entreprises.data.gouv.fr/rechercher?terme="
                          + company.replace(" ", "+"))
            driver.get(search_url)
            time.sleep(3)
            try:
                first = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/entreprise/']")))
                match = re.search(r"\b\d{9}\b", first.get_attribute("href"))
                siren = match.group(0) if match else "NA"
            except Exception:
                siren = "NA"
            results.append([company, clean_name(company), siren])
    finally:
        driver.quit()

    out = INTERIM / "siren_search_results.csv"
    pd.DataFrame(results, columns=["Dénomination", "Nom extrait", "SIREN"]).to_csv(out, index=False)
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
