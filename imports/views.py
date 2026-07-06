from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsPMOAdmin

from .orchestrator import run_import
from .serializers import ExcelUploadSerializer


class ExcelDryRunView(APIView):
    """Validate an uploaded workbook without persisting; return a per-row report."""

    permission_classes = [IsPMOAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=ExcelUploadSerializer, responses=dict)
    def post(self, request):
        serializer = ExcelUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = run_import(serializer.validated_data["file"], dry_run=True)
        return Response(report)


class ExcelConfirmView(APIView):
    """Persist a validated workbook. Rolls back entirely if any row fails."""

    permission_classes = [IsPMOAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=ExcelUploadSerializer, responses=dict)
    def post(self, request):
        serializer = ExcelUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            report = run_import(serializer.validated_data["file"], dry_run=False)
            if report["has_errors"]:
                transaction.set_rollback(True)
                return Response(
                    {"detail": "Import aborted: rows with errors.", **report},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(report, status=status.HTTP_201_CREATED)
