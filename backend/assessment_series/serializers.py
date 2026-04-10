from rest_framework import serializers
from .models import AssessmentSeries


class AssessmentSeriesSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    surcharge_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentSeries
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_status(self, obj):
        return obj.get_status()
    
    def get_surcharge_display(self, obj):
        return obj.get_surcharge_display()
    
    def validate(self, data):
        """Validate that only one surcharge option can be selected"""
        surcharge_50 = data.get('surcharge_50', getattr(self.instance, 'surcharge_50', False) if self.instance else False)
        surcharge_100 = data.get('surcharge_100', getattr(self.instance, 'surcharge_100', False) if self.instance else False)
        
        if surcharge_50 and surcharge_100:
            raise serializers.ValidationError({
                'surcharge_50': 'Only one surcharge option can be selected at a time.',
                'surcharge_100': 'Only one surcharge option can be selected at a time.'
            })
        
        return data
