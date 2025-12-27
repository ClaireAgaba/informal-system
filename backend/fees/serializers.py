from rest_framework import serializers
from .models import CandidateFee, CenterFee


class CandidateFeeSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    registration_number = serializers.CharField(source='candidate.registration_number', read_only=True)
    occupation_name = serializers.CharField(source='candidate.occupation.occ_name', read_only=True)
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    funding_source = serializers.CharField(source='candidate.funding_source', read_only=True)
    
    class Meta:
        model = CandidateFee
        fields = [
            'id', 'candidate', 'candidate_name', 'registration_number', 'occupation_name',
            'assessment_series', 'assessment_series_name', 'payment_code', 'funding_source',
            'total_amount', 'amount_paid', 'amount_due', 'payment_date',
            'payment_status', 'attempt_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['amount_due', 'created_at', 'updated_at']


class CenterFeeSerializer(serializers.ModelSerializer):
    assessment_center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    
    class Meta:
        model = CenterFee
        fields = [
            'id', 'assessment_series', 'assessment_series_name',
            'assessment_center', 'assessment_center_name',
            'total_candidates', 'total_amount', 'amount_paid', 'amount_due',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['amount_due', 'created_at', 'updated_at']
