"""Step 1 - List of mission-driven companies (Observatoire des sociétés à mission).

Scrapes the names of the referenced companies (67 listing pages) and saves
them, one per line, to data/raw/companies_list.txt.
Collected in 2025; the website structure may have changed since.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANIES_LIST

BASE_URL = "https://www.observatoiredessocietesamission.com/societes-a-mission-referencees/"
TOTAL_PAGES = 67


def scrape_page(page_num):
    """Return the company names listed on one page."""
    url = BASE_URL if page_num == 1 else f"{BASE_URL}?jsf=jet-engine&pagenum={page_num}"
    print(f"Page {page_num}: {url}")
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print(f"Error on page {page_num}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    return [h3.get_text(strip=True) for h3 in soup.find_all("h3")]


def main():
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(scrape_page, range(1, TOTAL_PAGES + 1)))
    companies = [name for page in results for name in page]
    print(f"\nCompanies collected: {len(companies)}")

    with open(COMPANIES_LIST, "w", encoding="utf-8") as f:
        for name in companies:
            f.write(name + "\n")
    print(f"Saved to {COMPANIES_LIST}")


if __name__ == "__main__":
    main()
