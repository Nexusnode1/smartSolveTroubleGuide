# Architecture

Offline warm-up, per SIIS row:

    SIIS text -> parse sections/steps -> relevance gate -> exact-label deeplink match
              -> order auto/manual/critical -> validate -> semantic cache (persisted)

Online, per request:

    query -> normalise -> embed -> cosine lookup -> cached plan | fallback (no_match / no_siis_context)
    (with siis_response supplied: cold build, validate, cache, return)

Semantic cache keys per plan: the original query, its 9 paraphrases, and one "action name + first step" key per action.

Swap points for your own model: `EMBEDDING_MODEL` and `SIMILARITY_THRESHOLD` (`app/config.py`). The article-relevance gate `relevance()` (`app/services/relevance.py`) is lexical and is the next candidate for a learned replacement. See `docs/training-integration.md`.
