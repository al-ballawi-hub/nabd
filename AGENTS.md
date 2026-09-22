# Nabd (نبض) — Project Context for AI Agents

Smart medical-records analysis & medical review platform.
Graduation project, University of Hail, Software Engineering Department.
Supervisor: Ahmad Alshomar.

## Purpose
A cloud-based AI assistant for physicians: digitizes scattered paper
records (OCR), detects drug conflicts, summarizes long patient histories
into a "Top Risks" dashboard, tracks treatment response, flags hereditary
risks via a medical family tree, prevents duplicate lab tests, and gives
patients plain-language explanations of their conditions.

## Repository layout (monorepo)
```
nabd/
├── apps/
│   └── web/              # React 18 + TS + Vite + Tailwind + TanStack Query
│       └── src/
│           ├── components/   # reusable UI (shadcn-style)
│           ├── features/     # one folder per module below
│           ├── lib/          # api client, utils
│           └── routes/       # react-router pages
├── services/
│   └── api/              # FastAPI (Python 3.12)
│       └── app/
│           ├── api/v1/       # routers (one per feature)
│           ├── core/         # config, security, logging
│           ├── models/       # SQLAlchemy models
│           ├── schemas/      # Pydantic v2 schemas
│           ├── services/     # business logic (OCR, interactions, LLM)
│           └── tests/
├── packages/
│   └── shared/           # shared TS types + constants
├── docs/                 # architecture, API specs, meeting notes
└── .opencode/            # agent configs
```

## Commands
| Task | Command |
|---|---|
| Install web deps | `npm install` (in apps/web) |
| Dev server (web) | `npm run dev` |
| Dev server (api) | `uvicorn app.main:app --reload` (in services/api) |
| Type check (web) | `npm run typecheck` |
| Lint (web) | `npm run lint` |
| Tests (api) | `pytest` |
| Lint (api) | `ruff check . && mypy .` |
| DB migrations | `alembic revision --autogenerate -m "msg"` |

## Conventions
- Git: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`), branch per
  feature (`feat/ocr-module`), PRs reviewed by at least one teammate.
- API: REST, `/api/v1/` prefix, camelCase JSON, error format
  `{ "detail": "..." }` (FastAPI default).
- Env vars prefixed `VITE_` (web) or loaded via pydantic-settings (api).
  Secrets live in `.env` (gitignored) — never commit them.
- UI: Arabic-first RTL design (Saudi users), Tailwind, primary color
  teal/emerald (medical calm), dark-mode ready. All medical content must
  render both Arabic and English labels from `packages/shared/i18n`.

## Definition of Done (per module)
1. Code merged to `main` with passing CI (typecheck + lint + tests)
2. API endpoints documented in `docs/api/`
3. Privacy review: no PHI in logs; access checks in place
4. At least one teammate has reviewed and approved

## Key deadlines (Graduation Project I)
- Architecture & UI/UX design — 8 Nov 2026
- OCR + records module — 29 Nov 2026
- Drug-interaction + Top Risks — 13 Dec 2026
- Remaining modules — 27 Dec 2026
- Integration & testing — 10 Jan 2027
- Final report & presentation — 24 Jan 2027
