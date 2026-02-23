from rest_framework import serializers
from .models import CandidateFee, CenterFee


class CandidateFeeSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    registration_number = serializers.CharField(source='candidate.registration_number', read_only=True)
    occupation_name = serializers.CharField(source='candidate.occupation.occ_name', read_only=True)
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    funding_source = serializers.CharField(source='candidate.funding_source', read_only=True)
    candidate_verification_status = serializers.CharField(source='candidate.verification_status', read_only=True)
    marked_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CandidateFee
        fields = [
            'id', 'candidate', 'candidate_name', 'registration_number', 'occupation_name',
            'candidate_verification_status',
            'assessment_series', 'assessment_series_name', 'payment_code', 'funding_source',
            'total_amount', 'amount_paid', 'amount_due', 'payment_date',
            'payment_status', 'attempt_status',
            'verification_status', 'payment_reference',
            'marked_by', 'marked_by_name', 'marked_date',
            'approved_by', 'approved_by_name', 'approved_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['amount_due', 'created_at', 'updated_at', 'marked_by', 'marked_date', 'approved_by', 'approved_date']
    
    def get_marked_by_name(self, obj):
        if obj.marked_by:
            name = f'{obj.marked_by.first_name} {obj.marked_by.last_name}'.strip()
            return name or obj.marked_by.username
        return None
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            name = f'{obj.approved_by.first_name} {obj.approved_by.last_name}'.strip()
            return name or obj.approved_by.username
        return None


class CenterFeeSerializer(serializers.ModelSerializer):
    assessment_center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    assessment_center_number = serializers.CharField(source='assessment_center.center_number', read_only=True)
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    
    class Meta:
        model = CenterFee
        fields = [
            'id', 'assessment_series', 'assessment_series_name',
            'assessment_center', 'assessment_center_name', 'assessment_center_number',
            'total_candidates', 'total_amount', 'amount_paid', 'amount_due',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['amount_due', 'created_at', 'updated_at']
