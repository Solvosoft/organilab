from rest_framework import serializers

class ReportDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.ListSerializer(child=serializers.CharField()), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
