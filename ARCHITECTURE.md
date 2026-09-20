# Architecture

This is a proposed hackathon architecture, not an official requirement. The official PDF and datasets were unavailable at bootstrap time; confirm every stage and its contracts before implementation.

```text
USER QUERY
  ↓
QUERY ENRICHMENT
  ↓
STRUCTURE EXTRACTION
  ↓
FAST-PATH CACHE
  ↓
DEEPLINK MAPPING
  ↓
ACTION SEQUENCING
  ↓
VALIDATION
  ↓
CACHE UPDATE
  ↓
REST API
  ↓
FRONTEND
```

| Component | Input → processing → output | Dependencies | Failure cases | Tests |
| --- | --- | --- | --- | --- |
| User query | Text → API request parsing → typed request | FastAPI, Pydantic | missing/invalid text | API request tests |
| Query enrichment | Query → paraphrase/context expansion → candidates | official query data/retrieval | unavailable data, no match | enrichment unit tests |
| Structure extraction | Candidates → structured actions → draft plan | official response schema | malformed source | extraction unit tests |
| Fast-path cache | Cache key → lookup → validated plan or miss | cache abstraction | stale/invalid entry | cache tests |
| Deeplink mapping | Draft actions → catalog match → mapped actions | official deeplink catalog | missing/ambiguous target | mapping tests |
| Action sequencing | Actions → ordered plan → ordered actions | official rules | conflicting order | sequencing tests |
| Validation | Plan → schema/rule checks → accepted plan/errors | Pydantic, official schema | schema/rule violation | validation tests |
| Cache update | Validated plan → store → cache entry | cache abstraction | storage failure | cache tests |
| REST API | Typed request → engine call → response | FastAPI | input/internal errors | API tests |
| Frontend | API response → rendered guide → user view | React (later) | network/schema mismatch | frontend tests (later) |

The current skeleton implements only the API wiring and placeholder response. An in-memory cache, FastAPI/Pydantic validation, pytest, and later lightweight semantic retrieval are implementation choices pending the official requirements.
