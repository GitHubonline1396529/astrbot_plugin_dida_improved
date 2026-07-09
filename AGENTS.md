# AGENTS.md

AI assistant reference index for `astrbot_plugin_dida_improved`.

> **Before writing code**, read `docs/development/coding-conventions.md`.
> **Before changing structure**, read `docs/development/architecture.md`.
> Consult the docs below for topic-specific details.

## Project structure

```
astrbot_plugin_dida_improved/
├── logo.png              # Plugin icon
├── main.py               # Plugin entry: command handlers + LLM tool registration
├── client.py             # Dida365 Open API HTTP client
├── service/              # Business logic layer (package)
├── models.py             # Data models (DidaTask, DidaProject, DidaPluginSettings)
├── exceptions.py         # Custom exception hierarchy
├── time_utils.py         # Timezone-aware datetime utilities
├── __init__.py           # Package marker (empty, for pytest)
├── tests/                # Test suite (see docs/development/testing.md)
├── requirements-dev.txt  # Dev dependencies
├── docs/                 # MkDocs documentation source
├── mkdocs.yml            # MkDocs configuration (Material theme)
├── site/                 # Built docs output (gitignored)
├── pages/docs/           # AstrBot Plugin Page target (gitignored, optional)
├── .gitattributes        # Archive export rules
├── .github/workflows/    # CI/CD: docs deploy + sync-to-main
├── _conf_schema.json     # Plugin config schema (auto-rendered in WebUI)
├── metadata.yaml         # Plugin metadata
├── pyproject.toml        # Ruff + pytest config
├── AGENTS.md             # This file
├── README.md             # User-facing documentation
├── LICENSE               # AGPL v3
└── data/                 # Runtime data (auto-generated)
```

## Quick reference

| Topic | Location |
|-------|----------|
| Architecture & design decisions | `docs/development/architecture.md` |
| Dida365 API technical details | `docs/development/architecture.md#dida365-api` |
| Coding conventions | `docs/development/coding-conventions.md` |
| API reference (auto-generated) | `docs/development/api-reference.md` |
| Documentation workflow | `docs/development/docs-workflow.md` |
| Release workflow | `docs/development/release-workflow.md` |
| Setup & environment | `docs/development/setup.md` |
| Testing guide | `docs/development/testing.md` |
| User commands | `docs/usage/commands.md` |
| LLM tools (12 tools) | `docs/usage/llm-tools.md` |

## External references

| Resource | URL |
|----------|-----|
| Dida365 Open API specification | [TickTick Developer](https://developer.dida365.com/docs#/openapi) |
| AstrBot plugin development guide | [AstrBot 插件开发指南 🌠](https://docs.astrbot.app/dev/star/plugin-new.html) |

## Essential rules

- **Python code entirely in English** — including string literals and log messages.
- **No ASCII art in docs** — use tables, lists, or code blocks.
- **80-column rule** applies to `.py` files only; does **not** apply to `docs/*.md`.
- **API docs** auto-generated from Google-style docstrings via `mkdocstrings`.
- For the full coding conventions (commits, tests, imports, etc.), see `docs/development/coding-conventions.md`.

## Build & verification

```bash
ruff format . && ruff check .   # Format + lint
pytest -v                        # Unit tests (no AstrBot runtime needed)
mkdocs build                     # Build docs to site/
mkdocs serve                     # Preview at http://localhost:8000
```

CI auto-deploys docs on `dev` push (changes under `docs/`, `*.py`, `mkdocs.yml`).  
Push `v*` tag on `dev` → GitHub Actions syncs release files to `main`.  
See `docs/development/docs-workflow.md` and `docs/development/release-workflow.md`.

## Architecture & key patterns

**3-layer architecture:** `main.py` (entry) → `service/` (business logic) → `client.py` (HTTP).  
See `docs/development/architecture.md` for full design decisions, data flow, and API details.

**Key design decisions (summary):**
1. Inbox fetched separately from project tasks via `/project/inbox/data`.
2. Task listing merges results from all projects + inbox.
3. LLM tools registered via `@filter.llm_tool()` decorators in `main.py`.
4. Error handling centralized in `DidaService.explain_error()`.

**Critical gotchas:**
- Inbox `projectId` (e.g., `inbox1014302018`) is **virtual** — not a real project ID.
- **Never** include `reminders` field on task update — causes HTTP 500.
- Task update is full-object replacement (`POST /task/{id}`), not partial patch.
- LLM tool parameter names must not conflict with AstrBot module names (avoid `filter` as a param name).
