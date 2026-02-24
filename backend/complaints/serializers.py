from rest_framework import serializers
from .models import Complaint, ComplaintCategory, ComplaintAttachment
from assessment_centers.models import AssessmentCenter
from assessment_series.models import AssessmentSeries
from occupations.models import Occupation
from users.models import User


class ComplaintCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'description', 'is_active']


class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ComplaintAttachment
        fields = ['id', 'file', 'uploaded_at', 'uploaded_by', 'uploaded_by_name']
        read_only_fields = ['uploaded_at', 'uploaded_by']


class ComplaintListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    exam_center_name = serializers.CharField(source='exam_center.center_name', read_only=True)
    exam_series_name = serializers.CharField(source='exam_series.name', read_only=True)
    program_name = serializers.CharField(source='program.occ_name', read_only=True)
    helpdesk_team_name = serializers.CharField(source='helpdesk_team.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'ticket_number', 'category', 'category_name',
            'exam_center', 'exam_center_name', 'exam_series', 'exam_series_name',
            'program', 'program_name', 'status', 'status_display',
            'helpdesk_team', 'helpdesk_team_name', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['ticket_number', 'created_at', 'updated_at']


class ComplaintDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    exam_center_name = serializers.CharField(source='exam_center.center_name', read_only=True)
    exam_series_name = serializers.CharField(source='exam_series.name', read_only=True)
    program_name = serializers.CharField(source='program.occ_name', read_only=True)
    helpdesk_team_name = serializers.CharField(source='helpdesk_team.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'ticket_number', 'category', 'category_name',
            'exam_center', 'exam_center_name', 'exam_series', 'exam_series_name',
            'program', 'program_name', 'phone',
            'issue_description', 'proof_of_complaint',
            'status', 'status_display', 'helpdesk_team', 'helpdesk_team_name',
            'team_response', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'attachments'
        ]
        read_only_fields = ['ticket_number', 'created_by', 'created_at', 'updated_at']


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'id', 'category', 'exam_center', 'exam_series', 'program',
            'phone', 'issue_description', 'proof_of_complaint',
            'status', 'helpdesk_team'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'id', 'category', 'exam_center', 'exam_series', 'program',
            'phone', 'issue_description', 'proof_of_complaint',
            'status', 'helpdesk_team', 'team_response'
        ]
        read_only_fields = ['id']
