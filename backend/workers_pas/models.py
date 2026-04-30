"""
Models for Worker's PAS booklet generation.
"""
from django.db import models, transaction
from django.utils import timezone


class WorkersPasBook(models.Model):
    """
    A generated Worker's PAS booklet for a candidate.

    The book number follows the format: ``WP/<wp_code>/<sequence>`` where the
    sequence is a globally-unique 8-digit zero-padded number across all
    Worker's PAS books (independent of occupation).
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
        unique=True,
        db_index=True,
        help_text="Global zero-padded sequence number used in the book number.",
    )
    book_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Full formatted book number, e.g. WP/BLD/00000001.",
    )
    full_label = models.CharField(
        max_length=80,
        help_text="Display label as printed on the cover, e.g. 'UVTAB: WP/BLD/00000001'.",
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
        ]

    def __str__(self):
        return self.book_number

    @classmethod
    @transaction.atomic
    def allocate_sequence(cls):
        """Atomically allocate the next global sequence number."""
        last = (
            cls.objects.select_for_update()
            .order_by('-sequence_number')
            .values_list('sequence_number', flat=True)
            .first()
        )
        return (last or 0) + 1

    @staticmethod
    def format_book_number(wp_code, sequence_number):
        """Format the book number as WP/<wp_code>/<8-digit-sequence>."""
        return f"WP/{wp_code}/{sequence_number:08d}"

    @staticmethod
    def format_full_label(book_number):
        return f"UVTAB: {book_number}"
