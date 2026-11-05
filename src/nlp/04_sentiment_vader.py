"""NLP step 4 - Sentiment score with VADER (on the English translation).

The VADER compound score (-1 to 1) is mapped to a 1-5 rating so it can be
compared with the Trustpilot stars:
  <= -0.6 -> 1 ; <= -0.2 -> 2 ; < 0.2 -> 3 ; < 0.6 -> 4 ; otherwise 5

Input : data/interim/reviews_translated_en.xlsx
Output: data/interim/reviews_scored_vader.xlsx (columns Score_VADER, Note_VADER)
"""
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import REVIEWS_TRANSLATED, REVIEWS_VADER

analyzer = SentimentIntensityAnalyzer()


def vader_compound(text):
    if not isinstance(text, str):
        return None
    return analyzer.polarity_scores(text)["compound"]


def to_rating(score):
    if score is None or pd.isna(score):
        return None
    if score <= -0.6:
        return 1
    if score <= -0.2:
        return 2
    if score < 0.2:
        return 3
    if score < 0.6:
        return 4
    return 5


def main():
    df = pd.read_excel(REVIEWS_TRANSLATED)
    tqdm.pandas(desc="VADER")
    df["Score_VADER"] = df["Commentaire_anglais"].progress_apply(vader_compound)
    df["Note_VADER"] = df["Score_VADER"].apply(to_rating)
    df.to_excel(REVIEWS_VADER, index=False)
    print(f"Saved to {REVIEWS_VADER}")


if __name__ == "__main__":
    main()
