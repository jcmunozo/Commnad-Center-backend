from rest_framework import serializers


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, f):
        if not f.name.lower().endswith((".xlsx", ".xlsm")):
            raise serializers.ValidationError("Only .xlsx/.xlsm workbooks are supported.")
        return f
