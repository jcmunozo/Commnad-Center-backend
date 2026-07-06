from django.urls import path

from .views import ExcelConfirmView, ExcelDryRunView

urlpatterns = [
    path("excel/dry-run/", ExcelDryRunView.as_view(), name="excel-dry-run"),
    path("excel/confirm/", ExcelConfirmView.as_view(), name="excel-confirm"),
]
