# PMO Command Center — Backend

Django 5.1 + DRF + PostgreSQL backend for the PMO Command Center.
Up-to-date documentation of the whole system (models, endpoints, permissions, business rules):
[`../docs/ESTADO_ACTUAL.md`](../docs/ESTADO_ACTUAL.md).

## Quick start (Docker, from the repo root)

```bash
docker compose up -d --build            # db, redis, web (migrates on boot), celery, frontend
docker compose exec web python manage.py seed_catalogs   # reference data (idempotent)
docker compose exec web python manage.py seed_roles      # PMO Admin / PM / Team / Viewer
docker compose exec web python manage.py createsuperuser
```

Run Compose from the **repo root**: the `docker-compose.yml` in this folder targets a separate, stale project.

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
| `core` | Abstract `TimeStampedModel`, `ActiveManager`, role permissions, `BaseModelViewSet`, pagination |
| `accounts` | `AppUser`, `GET /api/me/`, `seed_roles` |
| `catalogs` | Reference tables served under `/api/catalogs/<slug>/`, `seed_catalogs` |
| `projects` | `Project`, `ProjectPhase`, `ProjectFavorite`, `Sprint`, `Task`, `SubTask`, `Milestone`, portfolio dashboards |
| `resources` | `Employee`, `EmployeeShift`, `Leave`, `Holiday`, `TaskAssignment`, `TeamWorkloadPeriod`, workload service |
| `tickets` | `Ticket`, `TicketStatusLog`, WIP-hours service |
| `workitems` | Continuous Improvement: `WorkItem`, `WorkItemTask`, `WorkItemMilestone` |
| `notes` | Personal `Note` (private per user) |
| `links` | Reference `Link` attached to a project, note, ticket or work item |
| `clients` | Legacy — model kept for migration history, **not routed** |
| `tracking` | Empty — kept for migration history (replaced by `projects.SubTask`) |

There is no Excel importer any more (removed 2026-07-14).
