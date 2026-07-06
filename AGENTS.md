## Project structure

```
astrbot_plugin_dida_improved/
├── logo.png          # Plugin icon
├── main.py           # Plugin entry point: command handlers and LLM tool registration
├── client.py         # Dida365 Open API HTTP client
├── service.py        # Business logic layer (queries, formatting, error handling)
├── models.py         # Data models (DidaTask, DidaProject, DidaPluginSettings)
├── exceptions.py     # Custom exception hierarchy
├── time_utils.py     # Timezone-aware datetime utilities
├── __init__.py       # Package marker for test imports
├── tests/            # Test suite
│   ├── conftest.py   # Shared fixtures and sys.path setup (reads ASTRBOT_CORE_PATH from .env)
│   ├── test_models.py
│   ├── test_exceptions.py
│   ├── test_time_utils.py
│   ├── test_client.py
│   ├── test_service.py
│   ├── test_main.py
│   └── integration/
│       └── test_real_api.py  # Optional real API tests
├── requirements-dev.txt  # Test dependencies (not installed by AstrBot)
├── docs/             # MkDocs documentation source (Markdown)
│   ├── index.md
│   ├── installation.md
│   ├── configuration.md
│   ├── usage/
│   ├── development/
│   │   ├── api-reference.md   # Auto-generated from docstrings
│   │   └── ...
│   ├── troubleshooting.md
│   └── changelog.md
├── mkdocs.yml        # MkDocs configuration (Material theme)
├── site/             # Built documentation output (gitignored)
├── pages/docs/       # AstrBot Plugin Page target (gitignored, optional)
├── .gitattributes    # Archive export rules (marks dev-only files for ZIP exclusion)
├── .github/workflows/deploy-docs.yml
├── .github/workflows/sync-main-on-tag.yml  # Syncs release files to main on tag push
├── _conf_schema.json # Plugin configuration schema (auto-rendered in WebUI)
├── metadata.yaml     # Plugin metadata for AstrBot registry
├── pyproject.toml    # Ruff + pytest config
├── AGENTS.md         # This file: AI assistant reference index
└── README.md         # User-facing documentation
```

## Quick reference

| Topic | Location |
|-------|----------|
| Coding conventions | `docs/development/coding-conventions.md` |
| Architecture & design decisions | `docs/development/architecture.md` |
| API reference (auto-generated) | `docs/development/api-reference.md` |
| Documentation workflow | `docs/development/docs-workflow.md` |
| Dida365 API technical details | `docs/development/architecture.md#dida365-api` |
| Commit conventions | `docs/development/coding-conventions.md#commit-conventions` |
| Release workflow | `docs/development/release-workflow.md` |

## Coding rules

Python source code must be entirely in English, including string literals and log 
messages.

## Documentation rules

- **No ASCII art in docs** — use tables, lists, or code blocks instead
- API docs auto-generated from docstrings via `mkdocstrings`
- **80-column rule does NOT apply to `docs/*.md`** — some Markdown
  renderers treat hard line breaks in Chinese text as spaces, causing
  garbled rendering. Write naturally without artificial line breaks.

## Build & verification

```bash
ruff format . && ruff check .
pytest -v                              # run unit tests (requires ASTRBOT_CORE_PATH in .env)
mkdocs build                           # build docs to site/
mkdocs serve                           # preview at http://localhost:8000
mkdocs gh-deploy                       # deploy to GitHub Pages
```

Push to `dev` with changes under `docs/` or `*.py` → GitHub Actions
auto-deploys docs to `gh-pages`.

Push a `v*` tag on `dev` → GitHub Actions syncs release files to `main`.

## Dida365 API essentials

- `GET /project` / `GET /project/{id}/data` — projects & tasks
- `GET /project/inbox/data` — **separate endpoint** for Inbox
- `POST /task` / `POST /task/{id}` — create / update (full object)
- `POST /project/{id}/task/{id}/complete` — complete
- `DELETE /project/{id}/task/{id}` — delete
- **Never** include `reminders` field on update (causes HTTP 500)
- Inbox `projectId` like `inbox1014302018` is **virtual** — not a real ID

## Key design decisions

1. Inbox fetched separately from project tasks via `/project/inbox/data`.
2. All task listing combines results from all projects + inbox.
3. LLM Function Tools registered via `@filter.llm_tool()` decorators in `main.py`.
4. Error handling centralized in `DidaService.explain_error()`.
