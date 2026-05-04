"""Serializers for the Worker's PAS module."""
from rest_framework import serializers

from candidates.models import Candidate
from occupations.models import Occupation
from assessment_series.models import AssessmentSeries

from .models import WorkersPasBook


class WPOccupationSerializer(serializers.ModelSerializer):
    levels_count = serializers.IntegerField(source='get_levels_count', read_only=True)

    class Meta:
        model = Occupation
        fields = ['id', 'occ_code', 'occ_name', 'wp_code', 'wp_occ_code', 'levels_count']


class WPAssessmentSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSeries
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current']


class WPCandidateSerializer(serializers.ModelSerializer):
    has_book = serializers.SerializerMethodField()
    book_number = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'registration_number', 'full_name', 'date_of_birth',
            'gender', 'nationality', 'has_book', 'book_number',
        ]

    def get_has_book(self, obj):
        return getattr(obj, '_has_book', False)

    def get_book_number(self, obj):
        return getattr(obj, '_book_number', None)


class WorkersPasBookSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_reg_no = serializers.CharField(
        source='candidate.registration_number', read_only=True)
    occupation_name = serializers.CharField(source='occupation.occ_name', read_only=True)
    series_name = serializers.CharField(source='assessment_series.name', read_only=True)

    class Meta:
        model = WorkersPasBook
        fields = [
            'id', 'book_number', 'full_label', 'sequence_number',
            'candidate', 'candidate_name', 'candidate_reg_no',
            'occupation', 'occupation_name',
            'assessment_series', 'series_name',
            'issued_date', 'reprint_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
