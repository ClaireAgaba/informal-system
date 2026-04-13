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
