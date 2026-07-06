"""Populate catalog tables with the values detected in the Excel (Fase 2).

    python manage.py seed_catalogs
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogs import models as m


class Command(BaseCommand):
    help = "Seed reference catalogs with values from the PMO Command Center workbook."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed(m.SeverityLevel, [
            ("LOW", "Low", 1, 1), ("MEDIUM", "Medium", 2, 2),
            ("HIGH", "High", 3, 3), ("CRITICAL", "Critical", 4, 4),
        ], extra=("weight",), rows_fmt="code_name_sort_weight")
        self._simple(m.HealthStatus, [("GREEN", "Green"), ("YELLOW", "Yellow"), ("RED", "Red")])
        self._simple(m.ProjectType, [("API", "API-based"), ("REFACTOR", "Refactor"), ("OTHER", "Other")])
        self._closed(m.ProjectStatus, [
            ("PLANNING", "Planning", False), ("IN_PROGRESS", "In Progress", False),
            ("ON_HOLD", "On Hold", False), ("BLOCKED", "Blocked", False),
            ("COMPLETED", "Completed", True), ("CANCELLED", "Cancelled", True),
        ])
        self._closed(m.TaskStatus, [
            ("BACKLOG", "Backlog", False), ("TODO", "To Do", False),
            ("IN_PROGRESS", "In Progress", False), ("IN_REVIEW", "In Review", False),
            ("BLOCKED", "Blocked", False), ("DONE", "Done", True), ("CANCELLED", "Cancelled", True),
        ])
        self._simple(m.ApiStatus, [
            ("DESIGN", "Design"), ("IN_DEV", "In Development"), ("TESTING", "Testing"),
            ("DEPLOYED", "Deployed"), ("DEPRECATED", "Deprecated"),
        ])
        self._done(m.EndpointStatus, [
            ("PENDING", "Pending", False), ("IN_DEV", "In Development", False),
            ("READY_QA", "Ready for QA", False), ("IN_QA", "In QA", False),
            ("IN_SIT", "In SIT", False), ("IN_UAT", "In UAT", False),
            ("DONE", "Done", True), ("BLOCKED", "Blocked", False),
        ])
        self._closed(m.RiskStatus, [
            ("IDENTIFIED", "Identified", False), ("MITIGATING", "Mitigating", False),
            ("ACCEPTED", "Accepted", False), ("CLOSED", "Closed", True),
        ])
        self._closed(m.IssueStatus, [
            ("OPEN", "Open", False), ("INVESTIGATING", "Investigating", False),
            ("IN_RESOLUTION", "In Resolution", False), ("RESOLVED", "Resolved", True),
            ("CLOSED", "Closed", True),
        ])
        self._closed(m.MilestoneStatus, [
            ("PENDING", "Pending", False), ("IN_PROGRESS", "In Progress", False),
            ("COMPLETED", "Completed", True), ("DELAYED", "Delayed", False),
            ("CANCELLED", "Cancelled", True),
        ])
        self._closed(m.ActionStatus, [
            ("PENDING", "Pending", False), ("IN_PROGRESS", "In Progress", False),
            ("BLOCKED", "Blocked", False), ("COMPLETED", "Completed", True),
            ("CANCELLED", "Cancelled", True),
        ])
        self._simple(m.UpdateType, [
            ("CLIENT", "Client"), ("INTERNAL", "Internal"), ("CHANGE_REQ", "Change Request"),
            ("DECISION", "Decision"), ("MEETING", "Meeting"), ("BLOCKER", "Blocker"),
            ("ESCALATION", "Escalation"),
        ])
        self._simple(m.ActionOrigin, [
            ("CLIENT", "Client"), ("MEETING", "Meeting"), ("LEADERSHIP", "Leadership"),
            ("TEAM", "Team"), ("ISSUE", "Issue"), ("RISK", "Risk"), ("FOLLOW_UP", "Follow-up"),
        ])
        self._simple(m.TaskType, [
            ("DEV", "Development"), ("QA", "QA"), ("SIT", "SIT"), ("UAT", "UAT"),
            ("DOC", "Documentation"), ("CODE_REVIEW", "Code Review"), ("BUG_FIX", "Bug Fix"),
            ("DEVOPS", "DevOps"), ("DESIGN", "Design"), ("ANALYSIS", "Analysis"),
            ("DEPLOYMENT", "Deployment"), ("SUPPORT", "Support"),
        ])
        self._simple(m.HttpMethod, [
            ("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH"),
            ("DELETE", "DELETE"), ("OPTIONS", "OPTIONS"), ("HEAD", "HEAD"),
        ])
        self._simple(m.EmployeeLevel, [
            ("JUNIOR", "Junior"), ("MID", "Mid"), ("SENIOR", "Senior"),
            ("LEAD", "Lead"), ("MANAGER", "Manager"), ("ARCHITECT", "Architect"),
        ])
        self._simple(m.EmployeeStatus, [
            ("ACTIVE", "Active"), ("ON_LEAVE", "On Leave"),
            ("VACATION", "Vacation"), ("INACTIVE", "Inactive"),
        ])
        self._simple(m.Location, [
            ("COLOMBIA", "Colombia"), ("PHILIPPINES", "Philippines"), ("ARGENTINA", "Argentina"),
            ("MEXICO", "Mexico"), ("SPAIN", "Spain"), ("INDIA", "India"),
            ("USA_EAST", "USA East"), ("USA_WEST", "USA West"), ("UK", "UK"), ("BRAZIL", "Brazil"),
        ])
        for i, (code, name, off) in enumerate([
            ("UTC-5", "UTC-5 (Colombia)", "-5"), ("UTC-4", "UTC-4 (Chile/East)", "-4"),
            ("UTC-3", "UTC-3 (Argentina/Brazil)", "-3"), ("UTC-1", "UTC-1 (Azores)", "-1"),
            ("UTC+0", "UTC+0 (UK/Portugal)", "0"), ("UTC+1", "UTC+1 (Spain/France)", "1"),
            ("UTC+2", "UTC+2 (East Europe)", "2"), ("UTC+5:30", "UTC+5:30 (India)", "5.5"),
            ("UTC+8", "UTC+8 (Philippines/Singapore)", "8"), ("UTC+9", "UTC+9 (Japan/Korea)", "9"),
            ("UTC+10", "UTC+10 (Australia East)", "10"),
        ], start=1):
            m.Timezone.objects.update_or_create(
                code=code, defaults={"name": name, "utc_offset": off, "sort_order": i})
        for i, (code, name, sh, eh) in enumerate([
            ("STD", "Standard (9-18)", 9, 18), ("MORNING", "Morning (7-16)", 7, 16),
            ("AFTERNOON", "Afternoon (14-23)", 14, 23), ("NIGHT", "Night (22-7)", 22, 7),
            ("FLEX", "Flexible", 8, 17), ("PT_AM", "Part-time AM (9-13)", 9, 13),
            ("PT_PM", "Part-time PM (14-18)", 14, 18), ("OFF", "Off", None, None),
        ], start=1):
            m.Shift.objects.update_or_create(
                code=code, defaults={"name": name, "start_hour": sh, "end_hour": eh, "sort_order": i})

        self.stdout.write(self.style.SUCCESS("Catalogs seeded."))

    # ---- helpers ----
    def _simple(self, model, rows):
        for i, (code, name) in enumerate(rows, start=1):
            model.objects.update_or_create(code=code, defaults={"name": name, "sort_order": i})

    def _closed(self, model, rows):
        for i, (code, name, closed) in enumerate(rows, start=1):
            model.objects.update_or_create(
                code=code, defaults={"name": name, "is_closed": closed, "sort_order": i})

    def _done(self, model, rows):
        for i, (code, name, done) in enumerate(rows, start=1):
            model.objects.update_or_create(
                code=code, defaults={"name": name, "is_done": done, "sort_order": i})

    def _seed(self, model, rows, extra=(), rows_fmt=""):
        for code, name, sort, weight in rows:
            model.objects.update_or_create(
                code=code, defaults={"name": name, "sort_order": sort, "weight": weight})
