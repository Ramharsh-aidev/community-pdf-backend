from rest_framework import serializers

class PDFAnalysisResultSerializer(serializers.Serializer):
    issue = serializers.CharField()
    description = serializers.CharField()