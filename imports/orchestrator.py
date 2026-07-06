"""Excel → relational import orchestrator.

Reads the PMO Command Center workbook, normalizes each sheet's headers to the
target Resource field names, and runs django-import-export Resources in FK-safe
order. Supports dry-run (validate only) and confirm (persist).

The COLUMN_MAP layer bridges the Excel's human headers ("Project ID") to the
Resource fields ("legacy_code"). Sheets not listed are skipped.
"""
from __future__ import annotations

import tablib
from openpyxl import load_workbook

from apps.clients.resources import ClientResource
from apps.projects.resources import (
    ApiComponentResource,
    EndpointResource,
    MilestoneResource,
    ProjectResource,
    TaskResource,
)
from apps.resources.resources import EmployeeResource, TaskAssignmentResource
from apps.tracking.resources import ActionResource, IssueResource, RiskResource

# Ordered: catalogs are seeded separately (seed_catalogs); FKs resolve top-down.
PIPELINE = [
    # (sheet_name, Resource, {excel_header: resource_field})
    ("Team", EmployeeResource, {
        "Employee ID": "legacy_code", "Name": "name", "Role": "role", "Manager": "manager",
        "Availability %": "availability_pct", "Weekly Hrs": "weekly_hours",
    }),
    ("Projects", ProjectResource, {
        "Project ID": "legacy_code", "Project Name": "name", "Client": "client",
        "Start Date": "start_date", "Planned End": "planned_end", "Actual End": "actual_end",
        "Progress %": "progress_pct", "Planned Hrs": "planned_hours", "Consumed Hrs": "consumed_hours",
    }),
    ("APIs", ApiComponentResource, {
        "API ID": "legacy_code", "Project ID": "owner_project", "API Name": "name",
        "Description": "description", "Version": "version",
    }),
    ("Endpoints", EndpointResource, {
        "Endpoint ID": "legacy_code", "API ID": "api", "Path": "path",
        "Description": "description",
    }),
    ("Tasks", TaskResource, {
        "Task ID": "legacy_code", "Project ID": "project", "API ID": "api",
        "Endpoint ID": "endpoint", "Task Name": "name", "Estimated Hrs": "estimated_hours",
        "Actual Hrs": "actual_hours", "Progress %": "progress_pct", "Notes": "notes",
    }),
    ("Milestones", MilestoneResource, {
        "Milestone ID": "legacy_code", "Project ID": "project", "Milestone Name": "name",
        "Target Date": "target_date", "Actual Date": "actual_date",
    }),
    ("Assignments", TaskAssignmentResource, {
        "Assignment ID": "legacy_code", "Task ID": "task", "Employee ID": "employee",
        "Assigned Date": "assigned_date", "Delivery Date": "delivery_date",
    }),
    ("Issues", IssueResource, {
        "Issue ID": "legacy_code", "Project ID": "project", "Description": "description",
    }),
    ("Risks", RiskResource, {
        "Risk ID": "legacy_code", "Project ID": "project", "Description": "description",
        "Probability": "probability", "Impact": "impact",
    }),
    ("Actions", ActionResource, {
        "Action ID": "legacy_code", "Project ID": "project", "Description": "description",
    }),
]

ClientResource  # referenced when a Clients sheet exists; kept importable


def _sheet_to_dataset(ws, column_map: dict[str, str]) -> tablib.Dataset:
    """Convert a worksheet to a Dataset, keeping only mapped columns, skipping
    rows whose ID (first mapped column) is blank (filters formula-only rows)."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return tablib.Dataset()
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    keep = [(i, column_map[h]) for i, h in enumerate(headers) if h in column_map]
    ds = tablib.Dataset(headers=[field for _, field in keep])
    id_field = keep[0][1] if keep else None
    for raw in rows[1:]:
        values = [raw[i] if i < len(raw) else None for i, _ in keep]
        if id_field and (values[0] is None or str(values[0]).strip() == ""):
            continue  # skip pre-seeded formula rows with no real ID
        ds.append(values)
    return ds


def run_import(file_obj, *, dry_run: bool) -> dict:
    """Execute the pipeline. Returns a per-entity report with row-level errors."""
    wb = load_workbook(file_obj, data_only=True, read_only=True)
    report = {"dry_run": dry_run, "entities": [], "has_errors": False}

    for sheet_name, resource_cls, column_map in PIPELINE:
        if sheet_name not in wb.sheetnames:
            continue
        dataset = _sheet_to_dataset(wb[sheet_name], column_map)
        resource = resource_cls()
        result = resource.import_data(dataset, dry_run=dry_run, raise_errors=False)

        row_errors = []
        for line, errors in result.row_errors():
            row_errors.append({"row": line, "errors": [str(e.error) for e in errors]})

        entity_report = {
            "sheet": sheet_name,
            "model": resource_cls.Meta.model.__name__,
            "total_rows": len(dataset),
            "new": result.totals.get("new", 0),
            "updated": result.totals.get("update", 0),
            "skipped": result.totals.get("skip", 0),
            "invalid": result.totals.get("invalid", 0),
            "row_errors": row_errors,
        }
        if row_errors or entity_report["invalid"]:
            report["has_errors"] = True
        report["entities"].append(entity_report)

    return report
