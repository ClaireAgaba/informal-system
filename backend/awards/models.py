from django.db import models
from django.conf import settings
from candidates.models import Candidate
from assessment_centers.models import AssessmentCenter


class TranscriptCollection(models.Model):
    """
    Records a transcript collection event where one person collects
    transcripts for one or more candidates from the same center.
    """
    designation = models.CharField(
        max_length=100,
        verbose_name='Designation',
        help_text='Config designation name (e.g. Head of Center) or special: candidate, other_person',
    )
    nin = models.CharField(
        max_length=50,
        verbose_name='NIN',
        help_text='National Identification Number of the collector',
    )
    assessment_center = models.ForeignKey(
        AssessmentCenter,
        on_delete=models.PROTECT,
        related_name='transcript_collections',
        verbose_name='Exam Center',
    )
    collector_name = models.CharField(
        max_length=200,
        verbose_name='Collector Name',
    )
    collector_phone = models.CharField(
        max_length=20,
        verbose_name='Phone Number',
    )
    email = models.EmailField(
        verbose_name='Email',
        help_text='Email address to receive the collection receipt',
    )
    collection_date = models.DateField(
        verbose_name='Date of Collection',
    )
    signature_data = models.TextField(
        null=True,
        blank=True,
        verbose_name='Signature Data',
        help_text='Base64 encoded signature image from signature pad',
    )
    supporting_document = models.FileField(
        upload_to='transcript_collections/documents/',
        null=True,
        blank=True,
        verbose_name='Supporting Document',
        help_text='Required for Candidate and Other Person designations',
    )
    candidates = models.ManyToManyField(
        Candidate,
        related_name='transcript_collections',
        verbose_name='Candidates',
    )
    candidate_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Number of Candidates',
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Receipt Number',
        help_text='Auto-generated collection receipt number',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transcript_collections_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transcript Collection'
        verbose_name_plural = 'Transcript Collections'

    def __str__(self):
        return f'{self.receipt_number} - {self.collector_name} ({self.designation})'

    @staticmethod
    def generate_receipt_number():
        """Generate a unique receipt number like TCR-2026-00001"""
        from django.utils import timezone
        year = timezone.now().year
        prefix = f'TCR-{year}-'
        last = TranscriptCollection.objects.filter(
            receipt_number__startswith=prefix
        ).order_by('-receipt_number').first()
        if last:
            last_num = int(last.receipt_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        return f'{prefix}{new_num:05d}'