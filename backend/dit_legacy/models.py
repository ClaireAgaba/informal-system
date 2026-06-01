from django.conf import settings
from django.db import models


class DitLegacyAuditLog(models.Model):
    """Tracks changes made to legacy DIT candidate records."""
    _use_default_db = True

    person_id = models.CharField(max_length=50, db_index=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    changed_by_name = models.CharField(max_length=255, blank=True, default='')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.person_id}: {self.field_name} changed at {self.changed_at}'


class DitLegacyExamResult(models.Model):
    """Stores exam results added/edited via the UI for legacy DIT candidates.

    These live in the default DB because the legacy MySQL result tables are
    empty and the original data comes from CSV extracts.
    """
    _use_default_db = True

    person_id = models.CharField(max_length=50, db_index=True)
    paper = models.CharField(max_length=255, blank=True, default='')
    exam_date = models.CharField(max_length=100, blank=True, default='')
    exam_mark = models.CharField(max_length=20, blank=True, default='')
    exam_grade = models.CharField(max_length=10, blank=True, default='')
    exam_comment = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dit_exam_results_created',
    )
    created_by_name = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.person_id}: {self.paper} — {self.exam_grade}'
