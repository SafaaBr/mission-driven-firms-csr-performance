"""Step 6 - Company size and main activity (annuaire-entreprises.data.gouv.fr).

For each SIREN: name, main activity, NAF/APE code and size category
(SME / intermediate-size / large company).
Output: data/raw/company_size_activity.csv. Requires Chrome + Selenium.
Collected in 2025.
"""
import random
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANY_SIREN, COMPANY_SIZE

URL = "https://annuaire-entreprises.data.gouv.fr/entreprise/{}?redirected=1"


def get_field(driver, label=None, xpath=None):
    try:
        xp = xpath or f"//td[div[text()='{label}']]/following-sibling::td"
        return driver.find_element(By.XPATH, xp).text.strip()
    except Exception:
        return None


def main():
    sirens = pd.read_csv(COMPANY_SIREN)["SIREN"].dropna().astype(int).astype(str).str.zfill(9).tolist()
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    rows = []
    for i, siren in enumerate(sirens):
        driver.get(URL.format(siren))
        for _ in range(6):  # scroll so the React page loads
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(2)
        rows.append({
            "SIREN": siren,
            "Dénomination": get_field(driver, "Dénomination"),
            "Activité principale": get_field(driver, "Activité principale (NAF/APE)"),
            "Code NAF/APE": get_field(driver, "Code NAF/APE"),
            "Taille de la structure": get_field(
                driver, xpath="//td[.//span[contains(text(),'Taille de la structure')]]/following-sibling::td"),
        })
        if (i + 1) % 100 == 0:  # intermediate save
            pd.DataFrame(rows).to_csv(COMPANY_SIZE, index=False)
        time.sleep(random.uniform(2, 4))

    driver.quit()
    pd.DataFrame(rows).to_csv(COMPANY_SIZE, index=False)
    print(f"Saved to {COMPANY_SIZE}")


if __name__ == "__main__":
    main()
