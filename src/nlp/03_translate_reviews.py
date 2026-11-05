"""NLP step 3 - Translate the reviews into English (needed for VADER).

VADER is a lexicon built for English, so the French reviews are first
translated with Google Translate (deep-translator), in batches of 5,000.

Input : data/interim/reviews_clean.xlsx
Output: data/interim/reviews_translated_en.xlsx (column Commentaire_anglais)
"""
import sys
from pathlib import Path

import pandas as pd
from deep_translator import GoogleTranslator
from tqdm import tqdm

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import INTERIM, REVIEWS_CLEAN, REVIEWS_TRANSLATED

BATCH_SIZE = 5000
BATCH_DIR = INTERIM / "translation_batches"


def to_english(text):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return None


def main():
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(REVIEWS_CLEAN)
    n_batches = -(-len(df) // BATCH_SIZE)

    for i in range(n_batches):
        path = BATCH_DIR / f"batch_{i + 1}.xlsx"
        if path.exists():  # resume
            continue
        batch = df.iloc[i * BATCH_SIZE:(i + 1) * BATCH_SIZE].copy()
        tqdm.pandas(desc=f"Translation batch {i + 1}/{n_batches}")
        batch["Commentaire_anglais"] = batch["Commentaire_nettoye"].progress_apply(to_english)
        batch.to_excel(path, index=False)

    out = pd.concat([pd.read_excel(BATCH_DIR / f"batch_{i + 1}.xlsx") for i in range(n_batches)],
                    ignore_index=True)
    out.to_excel(REVIEWS_TRANSLATED, index=False)
    print(f"Saved to {REVIEWS_TRANSLATED}")


if __name__ == "__main__":
    main()
