from rest_framework import serializers
from .models import AssessmentSeries


class AssessmentSeriesSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentSeries
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_status(self, obj):
        return obj.get_status()
