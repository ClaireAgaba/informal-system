"""
Models for Worker's PAS booklet generation.
"""
from django.db import models, transaction
from django.utils import timezone


class WorkersPasBook(models.Model):
    """
    A generated Worker's PAS booklet for a candidate.

    The book number follows the format: ``WP/<wp_code>/<wp_occ_code><sequence>``
    where ``wp_occ_code`` is the numeric occupation code (e.g. 26) and
    ``sequence`` is a per-occupation 6-digit zero-padded number that restarts
    at 1 for each occupation.
    """

    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.PROTECT,
        related_name='workers_pas_books',
    )
    occupation = models.ForeignKey(
        'occupations.Occupation',
        on_delete=models.PROTECT,
        related_name='workers_pas_books',
    )
    assessment_series = models.ForeignKey(
        'assessment_series.AssessmentSeries',
        on_delete=models.PROTECT,
        related_name='workers_pas_books',
    )

    sequence_number = models.PositiveIntegerField(
        db_index=True,
        help_text="Per-occupation zero-padded sequence number used in the book number. "
                  "Restarts at 1 for each occupation.",
    )
    book_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Full formatted book number, e.g. WP/BLD/26000001.",
    )
    full_label = models.CharField(
        max_length=80,
        help_text="Display label as printed on the cover, e.g. 'UVTAB: WP/BLD/26000001'.",
    )

    pdf_file = models.FileField(
        upload_to='workers_pas/books/',
        blank=True,
        null=True,
        help_text="Generated PDF for this booklet.",
    )

    issued_date = models.DateField(default=timezone.now)
    reprint_count = models.PositiveIntegerField(default=0)

    generated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workers_pas_books_generated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Worker's PAS Book"
        verbose_name_plural = "Worker's PAS Books"
        indexes = [
            models.Index(fields=['candidate', 'occupation']),
            models.Index(fields=['assessment_series']),
            models.Index(fields=['issued_date']),
        ]
        constraints = [
            # Each candidate gets one book per occupation+series. Reprints bump
            # reprint_count instead of creating new rows.
            models.UniqueConstraint(
                fields=['candidate', 'occupation', 'assessment_series'],
                name='uniq_wp_book_candidate_occ_series',
            ),
            # Sequence numbers restart per occupation, so the (occupation,
            # sequence_number) pair must be unique.
            models.UniqueConstraint(
                fields=['occupation', 'sequence_number'],
                name='uniq_wp_book_occ_sequence',
            ),
        ]

    def __str__(self):
        return self.book_number

    @classmethod
    @transaction.atomic
    def allocate_sequence(cls, occupation):
        """Atomically allocate the next per-occupation sequence number."""
        last = (
            cls.objects.select_for_update()
            .filter(occupation=occupation)
            .order_by('-sequence_number')
            .values_list('sequence_number', flat=True)
            .first()
        )
        return (last or 0) + 1

    @staticmethod
    def format_book_number(wp_code, wp_occ_code, sequence_number):
        """Format the book number as ``WP/<wp_code>/<wp_occ_code><seq:06d>``.

        Example: ``format_book_number('BLD', 26, 1) -> 'WP/BLD/26000001'``.
        """
        return f"WP/{wp_code}/{wp_occ_code}{sequence_number:06d}"

    @staticmethod
    def format_full_label(book_number):
        return f"UVTAB: {book_number}"
