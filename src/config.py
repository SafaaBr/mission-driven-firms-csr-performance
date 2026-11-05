"""Project paths. Every script imports its paths from here (no absolute paths)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"          # large or non-redistributable files (git-ignored)
PROCESSED = DATA / "processed"

RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

# Collected files
COMPANIES_LIST = RAW / "companies_list.txt"
COMPANY_DETAILS = RAW / "company_details.csv"
COMPANY_SIREN = RAW / "company_siren.csv"
COMPANY_SIZE = RAW / "company_size_activity.csv"

# Trustpilot reviews (not published: personal content, Trustpilot terms of use)
REVIEWS_RAW = INTERIM / "reviews_trustpilot.xlsx"
REVIEWS_CLEAN = INTERIM / "reviews_clean.xlsx"
REVIEWS_BERT = INTERIM / "reviews_scored_bert.xlsx"
REVIEWS_TRANSLATED = INTERIM / "reviews_translated_en.xlsx"
REVIEWS_VADER = INTERIM / "reviews_scored_vader.xlsx"

# Financial data scraped from Pappers (not published)
FINANCIALS_DIR = INTERIM / "financials"

# Final dataset used for the analysis (one row per company)
ANALYSIS_DATASET = PROCESSED / "analysis_dataset.xlsx"
REVIEWS_SUMMARY = PROCESSED / "reviews_summary_by_company.csv"

for p in (INTERIM, PROCESSED, FIGURES, FINANCIALS_DIR):
    p.mkdir(parents=True, exist_ok=True)
