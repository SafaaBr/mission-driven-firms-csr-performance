"""Step 4 - Customer reviews from Trustpilot.

For each company, finds its Trustpilot page and collects every review
(text, individual rating, date) plus the overall rating.
Output: data/interim/reviews_trustpilot.xlsx (not published: personal content
and Trustpilot terms of use). Requires Chrome + Selenium.
Collected in 2025; Trustpilot's HTML classes change often, so the XPaths
below will probably need updating.
"""
import re
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import COMPANIES_LIST, INTERIM, REVIEWS_RAW


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", urllib.parse.unquote(text).lower())


def find_review_page(driver, company):
    driver.get(f"https://fr.trustpilot.com/search?query={company}")
    time.sleep(3)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'OK')]"))).click()
    except Exception:
        pass
    links = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
        (By.XPATH, "//a[contains(@href, '/review/')]")))
    target = normalize(company)
    for link in links:
        href = link.get_attribute("href")
        if target in normalize(href):
            return href
    return None


def parse_review(review):
    try:
        comment = review.find_element(By.XPATH, ".//p[contains(@class, 'typography_body-l')]").text.strip()
    except Exception:
        comment = "Commentaire non disponible"
    try:
        alt = review.find_element(By.XPATH, ".//img[contains(@alt, 'étoiles')]").get_attribute("alt")
        m = re.search(r"Noté (\d) sur 5 étoiles", alt)
        rating = int(m.group(1)) if m else None
    except Exception:
        rating = None
    try:
        t = review.find_element(By.TAG_NAME, "time")
        date_iso, date_txt = t.get_attribute("datetime"), t.text
    except Exception:
        date_iso, date_txt = None, None
    return comment, rating, date_iso, date_txt


def main():
    with open(COMPANIES_LIST, encoding="utf-8") as f:
        companies = [line.strip() for line in f if line.strip()]

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    reviews, not_found = [], []
    for company in companies:
        print(f"\n=== {company} ===")
        try:
            page_url = find_review_page(driver, company)
            if not page_url:
                not_found.append(company)
                continue
            driver.get(page_url)
            time.sleep(3)
            try:
                global_rating = driver.find_element(
                    By.XPATH, "//span[contains(@class, 'typography_display-m')]").text.strip().replace(",", ".")
            except Exception:
                global_rating = None

            page = 1
            while True:
                driver.get(f"{page_url}?languages=all&page={page}")
                time.sleep(3)
                cards = driver.find_elements(
                    By.XPATH, "//article[contains(@class, 'card_card') and contains(@class, 'styles_reviewCard')]")
                if not cards:
                    break
                for card in cards:
                    comment, rating, date_iso, date_txt = parse_review(card)
                    reviews.append({"Entreprise": company, "Commentaire": comment,
                                    "Date ISO": date_iso, "Date formatée": date_txt,
                                    "Note individuelle": rating, "Note globale": global_rating,
                                    "Lien Trustpilot": page_url})
                print(f"page {page}: {len(cards)} reviews")
                page += 1
        except Exception as e:
            print(f"Error for {company}: {e}")
            not_found.append(company)

    driver.quit()
    pd.DataFrame(reviews).to_excel(REVIEWS_RAW, index=False)
    pd.DataFrame({"company": not_found}).to_csv(INTERIM / "trustpilot_not_found.csv", index=False)
    print(f"\n{len(reviews)} reviews saved to {REVIEWS_RAW}")


if __name__ == "__main__":
    main()
