"""NLP step 5 - Compare BERT and VADER with the real ratings, then aggregate.

1. Validation: share of reviews where the predicted rating equals the
   rating given by the customer on Trustpilot (exact match), plus the mean
   absolute gap in stars.
2. Aggregation: mean BERT rating per company = bert_sentiment_score, the
   sentiment variable used in the analysis dataset.

Input : data/interim/reviews_scored_bert.xlsx, data/interim/reviews_scored_vader.xlsx
Output: results/sentiment_validation.csv, data/interim/bert_score_by_company.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import INTERIM, RESULTS, REVIEWS_BERT, REVIEWS_VADER


def main():
    bert = pd.read_excel(REVIEWS_BERT)
    vader = pd.read_excel(REVIEWS_VADER)
    assert bert["Commentaire"].equals(vader["Commentaire"]), "Reviews are not aligned"

    truth = pd.to_numeric(bert["Note individuelle"], errors="coerce")
    rows = []
    for name, pred in (("BERT", bert["Note_BERT"]), ("VADER", vader["Note_VADER"])):
        ok = truth.notna() & pred.notna()
        rows.append({"model": name, "n_reviews": int(ok.sum()),
                     "exact_match_pct": round((pred[ok] == truth[ok]).mean() * 100, 2),
                     "mean_abs_gap_stars": round((pred[ok] - truth[ok]).abs().mean(), 3)})
    res = pd.DataFrame(rows)
    res.to_csv(RESULTS / "sentiment_validation.csv", index=False)
    print(res.to_string(index=False))

    by_company = (bert.groupby("Entreprise")["Note_BERT"].mean()
                      .rename("bert_sentiment_score").reset_index())
    by_company.to_csv(INTERIM / "bert_score_by_company.csv", index=False)
    print(f"BERT score computed for {len(by_company)} companies")


if __name__ == "__main__":
    main()
