"""NLP step 1 - Clean the Trustpilot reviews.

- normalises the text, removes URLs and unwanted symbols (keeps basic
  punctuation and expressive emojis);
- drops unusable reviews: missing text, empty after cleaning, shorter than
  5 characters, only punctuation or only emojis.

Input : data/interim/reviews_trustpilot.xlsx
Output: data/interim/reviews_clean.xlsx
        data/processed/reviews_summary_by_company.csv (aggregates only, publishable)
"""
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import REVIEWS_CLEAN, REVIEWS_RAW, REVIEWS_SUMMARY

KEEP = r"[^a-zA-ZÀ-ÿ0-9\s\.,!?❤️🧡💛💚💙💜🖤🤍🤎🙂🙁😀😁😂🤣😅😊😍😘😭😢😡😠👍👎✨⭐🌟💥🙏👏🙌🔥💯]"
EMOJI_ONLY = re.compile(
    r"^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF"
    r"\U00002600-\U000026FF\U00002B50-\U00002B55‍♀♂]+$",
    flags=re.UNICODE)


def clean_text(text):
    if pd.isnull(text):
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(KEEP, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    df = pd.read_excel(REVIEWS_RAW)
    n_raw = len(df)
    raw_counts = df.groupby("Entreprise").size().rename("n_reviews_collected")

    df["Commentaire_nettoye"] = df["Commentaire"].apply(clean_text)
    df = df[~df["Commentaire"].str.lower().str.contains("commentaire non disponible", na=False)]
    df = df[df["Commentaire_nettoye"].str.strip() != ""]
    df = df[df["Commentaire_nettoye"].str.len() >= 5]
    df = df[~df["Commentaire_nettoye"].str.fullmatch(r"[^\w\sÀ-ÿ]+", na=False)]
    df = df[~df["Commentaire_nettoye"].str.match(EMOJI_ONLY, na=False)]

    print(f"Reviews collected: {n_raw}")
    print(f"Reviews kept after cleaning: {len(df)} ({len(df) / n_raw:.1%})")
    print(f"Companies with at least one review: {df['Entreprise'].nunique()}")
    df.to_excel(REVIEWS_CLEAN, index=False)

    rating = pd.to_numeric(df["Note individuelle"], errors="coerce")
    summary = (df.assign(rating=rating)
                 .groupby("Entreprise")
                 .agg(n_reviews_clean=("rating", "size"),
                      mean_rating=("rating", "mean"))
                 .join(raw_counts, how="right")
                 .fillna({"n_reviews_clean": 0})
                 .reset_index()
                 .rename(columns={"Entreprise": "company"}))
    summary["mean_rating"] = summary["mean_rating"].round(3)
    summary["n_reviews_clean"] = summary["n_reviews_clean"].astype(int)
    summary = summary[["company", "n_reviews_collected", "n_reviews_clean", "mean_rating"]]
    summary.to_csv(REVIEWS_SUMMARY, index=False)
    print(f"Summary by company saved to {REVIEWS_SUMMARY}")


if __name__ == "__main__":
    main()
