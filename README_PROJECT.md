# Smart Guided Troubleshooting Engine

Initial bootstrap for Samsung Prism Hackathon Theme 2. The official Theme 2 PDF and starter datasets were not present when this skeleton was created, so no troubleshooting behavior has been implemented.

## Architecture

The intended flow is query enrichment → structure extraction → cache → deeplink mapping → sequencing → validation → cache update → REST API → frontend. See [ARCHITECTURE.md](ARCHITECTURE.md). These are implementation placeholders until verified against the official materials.

## Layout

```text
smartSolveTroubleGuide/
├── app/              # FastAPI application and future pipeline modules
├── data/             # original (immutable), processed, and sample data
├── frontend/         # reserved for React
├── scripts/          # future data/benchmark utilities
└── tests/            # pytest suite
```

## Requirements and setup

Use Python 3.11 or later.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate` after creating the environment. Run tests with `pytest`.

## API

Start the server, then call:

```text
GET  http://127.0.0.1:8000/health
POST http://127.0.0.1:8000/api/v1/troubleshoot
```

The health endpoint returns `{"status":"ok"}`. The troubleshoot endpoint accepts `{"query":"..."}` and deliberately returns a marked placeholder; it does not produce a troubleshooting plan.

## Current status and next step

The project is importable and API-wired only. `data/original/`, `data/processed/`, and `data/samples/` are intentionally empty because no official datasets were supplied. Add the official Theme 2 PDF, query/response data, deeplink catalog, and schema without altering originals; then derive `PROJECT_SPEC.md` and implement the pipeline one verified stage at a time.
