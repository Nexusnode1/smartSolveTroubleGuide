# Smart Guided Troubleshooting Engine

Turns a vague Galaxy complaint into an ordered, validated plan with deeplinks, and shows it in a chat with a phone simulator.

## Run it

One-time setup (Python 3.11+ and Node 20):

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    cd frontend; npm install; cd ..

Then, from the project root:

    .\scripts\dev.ps1

This starts the API (port 8000) and the chat UI (port 5173) and opens the browser. The first start downloads the embedding model (about 420 MB) and takes a minute; later starts take about 20 seconds.

Try: "touch is laggy and my taps register late", "my phone screen is cracked", "screen stays black and the phone will not turn on". Press **Open** on an auto step and the phone simulator shows the Settings screen it points to.

## Check the criteria

    pytest                                       # all tests, including the 80% / 300 ms acceptance tests
    python scripts/benchmark.py                  # official-data metrics -> metrics.md
    python scripts/benchmark_paraphrase_dataset.py  # corrected paraphrase dataset -> docs/siis_paraphrase_baseline_benchmark.md
    python scripts/benchmark_cross_domain.py     # Battery/Camera/Performance fixture -> docs/cross_domain_generalization.md
    python scripts/benchmark_latency.py          # real REST latency against a live process -> docs/docker_latency_benchmark.md
    cd frontend && npm test && npm run build     # frontend tests and production build

## API

    GET  /health                 200 {"status":"ok"} once ready, else 503
    POST /v1/troubleshoot        {"query": "...", "siis_response": "<optional raw text>"}

## Your own model later

See `docs/training-integration.md`: export training pairs, fine-tune, evaluate with `--embedding-model`, then set `EMBEDDING_MODEL`.

## Beyond the Display domain

The 20 official sample rows are all Display complaints, even though the PDF describes four
device domains (Battery, Display, Camera, Performance). `docs/domain-coverage.md` and
`docs/cross_domain_generalization.md` explain how the other three are tested (a clearly
labeled synthetic fixture, not additional official coverage) and the real bugs that testing
found and fixed.

## Demo and submission

`docs/demo_readiness.md` has the verified strongest demo queries (with exact expected output),
a 2-3 minute demo script, an architecture diagram description, and the submission checklist.
Read this before presenting or submitting.

## Docker

A Dockerfile, `.dockerignore`, and `docker-compose.yml` exist and bake the embedding model and
plan cache in at build time (see `docs/docker_latency_benchmark.md`). **Docker itself has not
been build/run-verified in this environment** (Docker is not installed here); the latency
numbers in that document are real, measured local-process numbers, not container numbers --
read the caveat at the top of that file before citing them as container performance.

## Layout

    app/services/   siis_parser, key_matcher, plan_builder, plan_cache, troubleshooting_service
    app/retrieval/  embeddings (hash fallback), st_embedder (sentence-transformers, local models)
    frontend/       Vite + React chat, plan card, phone simulator
    scripts/        dev.ps1, build_plans.py, build_paraphrase_dataset.py, export_training_pairs.py,
                    benchmark.py, benchmark_paraphrase_dataset.py, benchmark_cross_domain.py,
                    benchmark_latency.py
    docs/           design spec, implementation plan, training guide, domain-coverage,
                    siis_alignment_audit / siis_dataset_quality_report / siis_hard_negatives /
                    siis_paraphrase_baseline_benchmark, cross_domain_generalization /
                    cross_domain_hard_negatives, camera_hard_negative_analysis,
                    docker_latency_benchmark, demo_readiness
    tests/fixtures/ paraphrases.json / paraphrases_holdout.json (Display), domain_articles.json /
                    cross_domain_articles.json (synthetic Battery/Camera/Performance),
                    camera_hard_negative.json
