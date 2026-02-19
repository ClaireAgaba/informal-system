from rest_framework import serializers
from .models import TranscriptCollection


class TranscriptCollectionListSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    center_code = serializers.CharField(source='assessment_center.center_number', read_only=True)

    class Meta:
        model = TranscriptCollection
        fields = [
            'id', 'receipt_number', 'created_at', 'collector_name',
            'nin', 'center_name', 'center_code', 'candidate_count',
            'designation', 'collector_phone', 'email', 'collection_date',
        ]


class TranscriptCollectionDetailSerializer(serializers.ModelSerializer):
    center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    center_code = serializers.CharField(source='assessment_center.center_number', read_only=True)
    candidates = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TranscriptCollection
        fields = [
            'id', 'receipt_number', 'created_at', 'designation',
            'collector_name', 'collector_phone', 'email', 'nin',
            'center_name', 'center_code', 'collection_date',
            'candidate_count', 'signature_data', 'supporting_document',
            'candidates', 'created_by_name',
        ]

    def get_candidates(self, obj):
        return [{
            'id': c.id,
            'registration_number': c.registration_number,
            'full_name': c.full_name,
            'center_name': c.assessment_center.center_name if c.assessment_center else '',
            'transcript_serial_number': c.transcript_serial_number,
            'transcript_type': 'Transcript',
        } for c in obj.candidates.select_related('assessment_center').all()]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return ''
