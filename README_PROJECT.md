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

    pytest                          # all tests, including the 80% / 300 ms acceptance tests
    python scripts/benchmark.py     # measures and writes metrics.md

## API

    GET  /health                 200 {"status":"ok"} once ready, else 503
    POST /v1/troubleshoot        {"query": "...", "siis_response": "<optional raw text>"}

## Your own model later

See `docs/training-integration.md`: export training pairs, fine-tune, evaluate with `--embedding-model`, then set `EMBEDDING_MODEL`.

## Beyond the Display domain

The 20 official sample rows are all Display complaints, even though the PDF describes four
device domains (Battery, Display, Camera, Performance). `docs/domain-coverage.md` explains
how the other three are tested and what a real bug that testing found and fixed looked like.

## Layout

    app/services/   siis_parser, key_matcher, plan_builder, plan_cache, troubleshooting_service
    app/retrieval/  embeddings (hash fallback), st_embedder (sentence-transformers, local models)
    frontend/       Vite + React chat, plan card, phone simulator
    scripts/        dev.ps1, build_plans.py, benchmark.py, export_training_pairs.py
    docs/           design spec, implementation plan, training guide
