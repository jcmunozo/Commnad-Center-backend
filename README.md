# PMO Command Center — Backend

Django 5 + DRF + PostgreSQL backend for the PMO Command Center (migrated from the
Excel workbook). See `../PMO_Command_Center_Guide.md` for the domain background.

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build          # starts db, redis, web (migrates on boot)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_catalogs   # reference data
docker compose exec web python manage.py seed_roles      # PMO Admin / PM / Team / Viewer
docker compose exec web python manage.py createsuperuser
```

API docs: http://localhost:8000/api/docs/ · Schema: `/api/schema/`

## Local (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
export DATABASE_URL=postgres://pmo:pmo@localhost:5432/pmo
python manage.py migrate && python manage.py seed_catalogs && python manage.py seed_roles
python manage.py runserver
```

## Tests / lint

```bash
pytest                 # pytest-django (see pyproject.toml)
ruff check . && black --check .
pre-commit install
```

## Apps

| App | Contains |
|-----|----------|
| `core` | Abstract `TimeStampedModel`, `ActiveManager`, role permissions, base viewset |
| `accounts` | `AppUser`, JWT `/me`, `seed_roles` |
| `catalogs` | 20 reference tables, `seed_catalogs`, auto-generated read/write viewsets |
| `clients` | `Client` |
| `projects` | Project, ApiComponent, Endpoint, reuse refs, Task, Milestone, dashboards |
| `resources` | Employee, EmployeeShift, TaskAssignment, workload service |
| `tracking` | Issue, Risk, ProjectUpdate, Action |
| `imports` | Excel dry-run / confirm import pipeline |

## Excel import

`POST /api/imports/excel/dry-run/` (multipart `file=`) validates and returns a
per-row report; `POST /api/imports/excel/confirm/` persists (atomic; aborts on any
error). Catalogs must be seeded first. Column mapping lives in
`imports/orchestrator.py` (`PIPELINE`).
