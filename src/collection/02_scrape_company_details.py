"""Step 2 - Details of each company (sector, region, creation date, mission date).

Reads data/raw/companies_list.txt, builds the URL of each company page on the
Observatoire des sociétés à mission and saves data/raw/company_details.csv.
Collected in 2025; the website structure may have changed since.
"""
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
import unidecode
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANIES_LIST, COMPANY_DETAILS

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0",
]
COLUMNS = ["Nom", "Lien", "Secteur", "Région", "Date de création", "Date de passage à mission"]


def name_to_slug(name):
    """Turn a company name into the slug used in the website URLs."""
    s = unidecode.unidecode(name.lower())
    s = s.replace(" ", "-").replace("'", "")
    s = s.strip(".")
    s = s.replace(".", "-").replace("&", "").replace(",", "-")
    s = s.replace("  ", "-").replace("--", "-").replace("''", "")
    return s


def scrape_details(name):
    url = f"https://www.observatoiredessocietesamission.com/societe-a-mission/{name_to_slug(name)}/"
    empty = [name, url, "NA", "NA", "NA", "NA"]
    print(f"Scraping: {url}")
    try:
        response = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        if response.status_code != 200:
            return empty
        soup = BeautifulSoup(response.text, "html.parser")
        if "Page not found" in soup.text or len(soup.text) < 100:
            return empty

        # Sector and region are encoded in the CSS classes of a <div>
        sector, region = "NA", "NA"
        div = soup.find("div", class_=lambda x: x and ("wntat_region-" in x or "wntat_sector-" in x))
        if div:
            for cls in div.get("class", []):
                if cls.startswith("wntat_sector-"):
                    sector = cls.replace("wntat_sector-", "").replace("-", " ").strip()
                if cls.startswith("wntat_region-"):
                    region = cls.replace("wntat_region-", "").replace("-", " ").strip()

        creation_date, mission_date = "NA", "NA"
        for field in soup.find_all("div", class_="jet-listing-dynamic-field__content"):
            text = field.get_text(strip=True)
            if "Créée en" in text:
                creation_date = text.replace("Créée en ", "").strip()
            if "Société à mission depuis le" in text:
                mission_date = text.replace("Société à mission depuis le ", "").strip()

        time.sleep(random.uniform(5, 10))  # polite delay
        return [name, url, sector, region, creation_date, mission_date]
    except Exception:
        return empty


def main():
    with open(COMPANIES_LIST, encoding="utf-8") as f:
        companies = [line.strip() for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=2) as executor:  # max 2 parallel requests
        rows = list(executor.map(scrape_details, companies))

    pd.DataFrame(rows, columns=COLUMNS).to_csv(COMPANY_DETAILS, index=False)
    print(f"Saved to {COMPANY_DETAILS}")


if __name__ == "__main__":
    main()
