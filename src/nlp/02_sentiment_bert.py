"""NLP step 2 - Sentiment score with a multilingual BERT model.

Model: nlptown/bert-base-multilingual-uncased-sentiment, which predicts a
rating from 1 to 5 stars directly from the (mostly French) review text.
Processed in batches of 10,000 reviews, saved one by one so a long run can
be resumed.

Input : data/interim/reviews_clean.xlsx
Output: data/interim/reviews_scored_bert.xlsx (column Note_BERT)
"""
import sys
from pathlib import Path

import pandas as pd
import torch
from torch.nn.functional import softmax
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import INTERIM, REVIEWS_BERT, REVIEWS_CLEAN

MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
BATCH_SIZE = 10_000
BATCH_DIR = INTERIM / "bert_batches"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()


def score_bert(text):
    """Return the predicted number of stars (1-5)."""
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            probs = softmax(model(**inputs).logits, dim=1).squeeze()
        return int(torch.argmax(probs).item()) + 1
    except Exception:
        return None


def main():
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(REVIEWS_CLEAN).reset_index(drop=True)
    n_batches = -(-len(df) // BATCH_SIZE)

    for i in range(n_batches):
        path = BATCH_DIR / f"batch_{i + 1}.xlsx"
        if path.exists():  # resume
            continue
        batch = df.iloc[i * BATCH_SIZE:(i + 1) * BATCH_SIZE].copy()
        tqdm.pandas(desc=f"BERT batch {i + 1}/{n_batches}")
        batch["Note_BERT"] = batch["Commentaire_nettoye"].progress_apply(score_bert)
        batch.to_excel(path, index=False)

    scored = pd.concat([pd.read_excel(BATCH_DIR / f"batch_{i + 1}.xlsx") for i in range(n_batches)],
                       ignore_index=True)
    scored.to_excel(REVIEWS_BERT, index=False)
    print(f"Saved to {REVIEWS_BERT}")


if __name__ == "__main__":
    main()
