import json
import logging
import re
from pathlib import Path
from typing import Sequence

import pandas as pd

logger = logging.getLogger(__name__)


def _load_raw_data(data_path: str | Path, target_categories: Sequence[str]) -> pd.DataFrame:
    """Load and filter arXiv JSONL metadata by target categories."""
    data_path = Path(data_path)

    target_categories = set(target_categories)
    cat_regex = re.compile("|".join(re.escape(cat) for cat in target_categories))

    filtered_data = []

    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            # Cheap pre-filter before JSON parsing
            if not cat_regex.search(line):
                continue

            item = json.loads(line)
            categories = set(item.get("categories", "").split())

            if categories.intersection(target_categories):
                filtered_data.append(item)

    return pd.DataFrame(filtered_data)


def _compute_publication_signal(row: pd.Series) -> bool:
    """Proxy for publication maturity using DOI or journal reference."""
    doi = row.get("doi")
    journal_ref = row.get("journal-ref")

    return pd.notna(doi) or pd.notna(journal_ref)


def preprocess_data(
    df: pd.DataFrame,
    start_year: int = 2020,
    end_year: int = 2026,
    sample_size: int | None = 50_000,
    random_state: int = 42,
) -> pd.DataFrame:
    """Clean, filter, deduplicate, and sample arXiv records."""
    rag_df = df.copy()

    required_cols = ["id", "title", "abstract", "update_date"]
    missing_cols = [col for col in required_cols if col not in rag_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    rag_df["abstract"] = rag_df["abstract"].fillna("").astype(str)
    rag_df["title"] = rag_df["title"].fillna("").astype(str)

    if "num_tokens" not in rag_df.columns:
        rag_df["num_tokens"] = rag_df["abstract"].str.split().str.len()

    if "year" not in rag_df.columns:
        rag_df["year"] = pd.to_datetime(
            rag_df["update_date"],
            errors="coerce",
        ).dt.year

    if "is_published" not in rag_df.columns:
        rag_df["is_published"] = rag_df.apply(_compute_publication_signal, axis=1)

    mean_tokens = rag_df["num_tokens"].mean()
    std_tokens = rag_df["num_tokens"].std()

    lower_limit = max(30, mean_tokens - 2.5 * std_tokens)
    upper_limit = mean_tokens + 2.5 * std_tokens

    logger.info(
        "Filtering abstracts outside token range: [%.1f, %.1f]",
        lower_limit,
        upper_limit,
    )

    mask = (
        rag_df["id"].notna()
        & rag_df["title"].str.strip().ne("")
        & rag_df["abstract"].str.strip().ne("")
        & rag_df["num_tokens"].between(lower_limit, upper_limit)
        & rag_df["year"].between(start_year, end_year)
    )

    rag_df = rag_df[mask].copy()

    # Keep newest metadata version per title
    rag_df = rag_df.sort_values(by="update_date", ascending=True)
    rag_df = rag_df.drop_duplicates(subset=["title"], keep="last")

    if sample_size is not None and len(rag_df) > sample_size:
        sampling_fraction = sample_size / len(rag_df)

        rag_df = (
            rag_df.groupby("year", group_keys=False)
            .sample(frac=sampling_fraction, random_state=random_state)
        )

        # Exact sample size after fractional grouped sampling
        if len(rag_df) > sample_size:
            rag_df = rag_df.sample(n=sample_size, random_state=random_state)

    rag_df["id"] = "arxiv." + rag_df["id"].astype(str)

    keep_cols = ["id", "year", "is_published", "title", "abstract"]

    return rag_df[keep_cols].reset_index(drop=True)


def load_preprocess_data(
    data_path: str | Path,
    target_categories: Sequence[str],
    start_year: int = 2020,
    end_year: int = 2026,
    sample_size: int | None = 50_000,
    random_state: int = 42,
) -> pd.DataFrame:
    """Load raw arXiv metadata and return processed RAG dataframe."""
    raw_df = _load_raw_data(
        data_path=data_path,
        target_categories=target_categories,
    )

    rag_df = preprocess_data(
        df=raw_df,
        start_year=start_year,
        end_year=end_year,
        sample_size=sample_size,
        random_state=random_state,
    )

    logger.info("Successfully loaded and preprocessed %d arXiv records.", len(rag_df))

    return rag_df