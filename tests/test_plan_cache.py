"""Only validated plans enter the cache; lookups are semantic and persistent."""

import copy
import json

import pytest

from app.services.plan_builder import PlanBuilder
from app.services.plan_cache import PlanCache

HASH_THRESHOLD = 0.3  # the hashed fallback embedder scores lower than a real model


@pytest.fixture(scope="module")
def built(catalog, siis_rows):
    row = next(r for r in siis_rows if r["id"] == "row_2")
    siis = row["siis_response"]
    build = PlanBuilder(catalog).build(row["original_query"], siis["content"], siis["title"])
    assert build is not None and build.errors == ()
    return row["original_query"], build


def test_exact_query_hits_and_paraphrase_hits_semantically(catalog, built):
    query, build = built
    cache = PlanCache(catalog, threshold=HASH_THRESHOLD)
    cache.add("row_2", query, build.query_variations, build.response)
    exact = cache.lookup(query)
    assert exact.exact is True and exact.entry.entry_id == "row_2"
    # The hashed fallback only recognises near-rephrases; real paraphrases are covered by tests/test_acceptance.py.
    paraphrase = cache.lookup("screen turns completely blank or white when I search")
    assert paraphrase is not None and paraphrase.exact is False


def test_unrelated_query_misses(catalog, built):
    query, build = built
    cache = PlanCache(catalog, threshold=HASH_THRESHOLD)
    cache.add("row_2", query, build.query_variations, build.response)
    assert cache.lookup("what is the best pasta recipe") is None


def test_invalid_plan_is_rejected_and_not_stored(catalog, built):
    query, build = built
    bad = copy.deepcopy(build.response)
    bad["contexts"][0]["goal"] = "Fix it"
    cache = PlanCache(catalog)
    with pytest.raises(ValueError):
        cache.add("row_2", query, build.query_variations, bad)
    assert len(cache) == 0


def test_save_and_load_round_trip(catalog, built, tmp_path):
    query, build = built
    cache = PlanCache(catalog)
    cache.add("row_2", query, build.query_variations, build.response)
    path = tmp_path / "cache.json"
    cache.save(path)
    loaded = PlanCache.load(path, catalog)
    assert len(loaded) == 1
    assert loaded.lookup(query).entry.response == build.response


def test_load_revalidates_every_entry(catalog, built, tmp_path):
    query, build = built
    cache = PlanCache(catalog)
    cache.add("row_2", query, build.query_variations, build.response)
    path = tmp_path / "cache.json"
    cache.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["entries"][0]["response"]["contexts"][0]["goal"] = "Fix it"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        PlanCache.load(path, catalog)
