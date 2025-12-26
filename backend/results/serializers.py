from rest_framework import serializers
from .models import WorkersPasResult
from occupations.models import OccupationPaper, OccupationModule, OccupationLevel
from assessment_series.models import AssessmentSeries


class WorkersPasResultSerializer(serializers.ModelSerializer):
    """Serializer for Workers PAS results with read-only computed fields"""
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    level_name = serializers.CharField(source='level.level_name', read_only=True)
    module_code = serializers.CharField(source='module.module_code', read_only=True)
    module_name = serializers.CharField(source='module.module_name', read_only=True)
    paper_code = serializers.CharField(source='paper.paper_code', read_only=True)
    paper_name = serializers.CharField(source='paper.paper_name', read_only=True)
    grade = serializers.ReadOnlyField()
    comment = serializers.ReadOnlyField()
    entered_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkersPasResult
        fields = [
            'id', 'candidate', 'assessment_series', 'assessment_series_name',
            'level', 'level_name', 'module', 'module_code', 'module_name',
            'paper', 'paper_code', 'paper_name', 'type', 'mark', 'grade',
            'status', 'comment', 'entered_by', 'entered_by_name',
            'entered_at', 'updated_at'
        ]
        read_only_fields = ['entered_at', 'updated_at', 'type']
    
    def get_entered_by_name(self, obj):
        if obj.entered_by:
            return f"{obj.entered_by.first_name} {obj.entered_by.last_name}".strip() or obj.entered_by.username
        return None


class WorkersPasResultCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating/updating Workers PAS results"""
    paper_id = serializers.IntegerField()
    mark = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, required=False)
    status = serializers.ChoiceField(
        choices=WorkersPasResult.STATUS_CHOICES,
        default='normal'
    )
    
    def validate_paper_id(self, value):
        """Validate that the paper exists"""
        try:
            paper = OccupationPaper.objects.get(id=value)
            return value
        except OccupationPaper.DoesNotExist:
            raise serializers.ValidationError(f'Paper with id {value} not found')
    
    def validate_mark(self, value):
        """Validate mark is within range"""
        if value is not None:
            if value < -1 or value > 100:
                raise serializers.ValidationError('Mark must be between -1 and 100 (-1 for missing)')
        return value
