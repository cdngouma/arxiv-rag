# Data Sources and Paper Schema

## V1 project framing

**Research Paper Discovery & Ranking System:** An abstract-based search and RAG assistant for finding relevant, recent, and foundational research papers. It supports the **start of a literature review**, not comprehensive paper analysis or independent verification of scientific claims.

**Retrieval corpus:** One document per paper, indexed using its title and abstract.

## Data sources

| Source | Access | Purpose | Provider fields |
|---|---|---|---|
| **arXiv metadata snapshot** | Downloaded JSON Lines file (`arxiv-metadata-oai-snapshot.json`) | Primary corpus: titles, abstracts, authors, categories, and submission history | `id`, `title`, `abstract`, `authors`, `authors_parsed`, `categories`, `versions` (`version`, `created`), `update_date`, `doi`, `journal-ref` |
| **Semantic Scholar Academic Graph** | REST API (`POST /graph/v1/paper/batch`) | Citation metrics, publication details, and identifiers | `paperId`, `externalIds`, `year`, `publicationDate`, `publicationTypes`, `venue`, `citationCount`, `influentialCitationCount`, `referenceCount`, `title` |
| **Crossref** | REST API (`GET /works/{doi}`) | DOI-linked publication metadata and integrity notices (retractions, corrections, expressions of concern where recorded) | `DOI`, `type`, `title`, `container-title`, `published`, `published-print`, `published-online`, `relation`, `update-to` (including `DOI`, `type`, `source`, `updated`, `label` when supplied) |

**Documentation:** [arXiv dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) · [Semantic Scholar API](https://api.semanticscholar.org/api-docs/) · [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) · [Crossref retractions](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/)

## Linking records

Use `paper_id = "arxiv:" + arxiv_id` as the canonical identifier. Keep external IDs separately.

| Records | Matching strategy |
|---|---|
| arXiv → Semantic Scholar | Query using `ARXIV:<arxiv_id>`; verify `externalIds.ArXiv` where available |
| arXiv / Semantic Scholar → Crossref | Match normalized DOI to Crossref `DOI` |
| Crossref notice → paper | Match the DOI of the **affected paper**, retaining the notice's own DOI and relationship |
| Missing identifiers | Normalized title + author overlap + compatible year as a **candidate match requiring validation** |

## Canonical dataset

One normalized record per arXiv paper. Provider-specific values may be missing; nullable fields remain `null`.

| Field | Type | Meaning / source |
|---|---|---|
| `paper_id` | string | Canonical key (`arxiv:<id>`) |
| `arxiv_id` | string | arXiv `id` |
| `semantic_scholar_id` | string or null | Semantic Scholar `paperId` |
| `doi` | string or null | Normalized DOI |
| `title` | string | arXiv title |
| `abstract` | string | arXiv abstract |
| `authors` | list[string] | arXiv authors |
| `categories` | list[string] | arXiv categories |
| `first_submitted_date` | date or null | Earliest arXiv `versions[].created` |
| `last_updated_date` | date or null | arXiv `update_date` |
| `publication_date` | date or null | Semantic Scholar / Crossref publication date |
| `publication_year` | int or null | Publication year, if known |
| `publication_types` | list[string] | Semantic Scholar publication types |
| `venue` | string or null | Semantic Scholar venue / Crossref container title |
| `journal_reference` | string or null | arXiv `journal-ref` |
| `citation_count` | int or null | Semantic Scholar citation count |
| `influential_citation_count` | int or null | Semantic Scholar influential citations |
| `reference_count` | int or null | Semantic Scholar reference count |
| `integrity_status` | string | `unknown`, `no_notice_found`, `retracted`, `expression_of_concern`, `corrected`, `withdrawn`, or `other_notice` |
| `integrity_notices` | list[object] | Crossref notices, relationships, dates, and sources |
| `metadata_sources` | list[string] | Providers that contributed metadata |
| `match_provenance` | list[object] | How provider records were linked |
| `metadata_fetched_at` | datetime or null | UTC timestamp of metadata enrichment |

### Example record

*Illustrative values, not a real paper.*

```json
{
  "paper_id": "arxiv:example-id",
  "arxiv_id": "example-id",
  "semantic_scholar_id": null,
  "doi": null,
  "title": "Example Research Paper",
  "abstract": "Example abstract.",
  "authors": ["Example Author"],
  "categories": ["cs.LG"],
  "first_submitted_date": "2023-02-10",
  "last_updated_date": "2023-04-12",
  "publication_date": null,
  "publication_year": null,
  "publication_types": [],
  "venue": null,
  "journal_reference": null,
  "citation_count": null,
  "influential_citation_count": null,
  "reference_count": null,
  "integrity_status": "unknown",
  "integrity_notices": [],
  "metadata_sources": ["arxiv"],
  "match_provenance": [],
  "metadata_fetched_at": null
}
```

## Data quality

Prefer exact arXiv ID and DOI matches; validate fallback matches and retain provenance. Keep first submission, last update, and publication dates distinct. Do not treat missing citation counts as zero, DOI presence as proof of peer review, or missing integrity notices as proof of a clean record. Record source snapshot and API retrieval dates for reproducibility; index titles and abstracts only.
