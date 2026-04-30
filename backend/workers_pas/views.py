"""
Views for the Worker's PAS module.

Public endpoints:
  - GET    /api/workers-pas/occupations/         List Worker's PAS occupations
  - GET    /api/workers-pas/series/              List assessment series
  - GET    /api/workers-pas/candidates/          List eligible candidates
  - POST   /api/workers-pas/books/generate/      Generate one booklet PDF
  - POST   /api/workers-pas/books/bulk/          Bulk-generate booklets (ZIP)
  - GET    /api/workers-pas/books/               List issued books
  - GET    /api/workers-pas/books/{id}/download/ Download a book's PDF
"""
import io
import os
import zipfile
from datetime import date

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from assessment_series.models import AssessmentSeries
from candidates.models import Candidate, CandidateEnrollment
from occupations.models import Occupation, OccupationLevel, OccupationModule

from .models import WorkersPasBook
from .pdf import generate_book_pdf, impose_2up_a4
from .serializers import (
    WPOccupationSerializer, WPAssessmentSeriesSerializer,
    WPCandidateSerializer, WorkersPasBookSerializer,
)


# ---------------------------------------------------------------------------
# Lookup endpoints
# ---------------------------------------------------------------------------

class WorkersPasOccupationListView(APIView):
    """List occupations that are configured as Worker's PAS."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = Occupation.objects.filter(
            occ_category='workers_pas', is_active=True,
        ).order_by('occ_name')
        return Response(WPOccupationSerializer(qs, many=True).data)


class WorkersPasSeriesListView(APIView):
    """List assessment series available for Worker's PAS book generation."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = AssessmentSeries.objects.filter(is_active=True).order_by('-start_date')
        return Response(WPAssessmentSeriesSerializer(qs, many=True).data)


class WorkersPasCandidateListView(APIView):
    """
    List candidates registered for a given Worker's PAS occupation in a series.

    Query params:
      occupation (required) - Occupation id
      series     (required) - AssessmentSeries id
      search     - optional case-insensitive search on name/reg_no
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        occupation_id = request.query_params.get('occupation')
        series_id = request.query_params.get('series')
        search = (request.query_params.get('search') or '').strip()

        if not occupation_id or not series_id:
            return Response(
                {'detail': 'occupation and series are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Candidates with an enrollment in this series for this WP occupation
        enrollments = CandidateEnrollment.objects.filter(
            assessment_series_id=series_id,
            candidate__occupation_id=occupation_id,
            candidate__occupation__occ_category='workers_pas',
            is_active=True,
        )
        candidate_ids = enrollments.values_list('candidate_id', flat=True).distinct()

        qs = Candidate.objects.filter(id__in=list(candidate_ids))
        if search:
            qs = qs.filter(full_name__icontains=search) | qs.filter(
                registration_number__icontains=search)
        qs = qs.order_by('full_name')

        # Annotate with whether a book has already been generated for this series
        existing_books = {
            (b.candidate_id, b.book_number): b
            for b in WorkersPasBook.objects.filter(
                candidate_id__in=qs.values_list('id', flat=True),
                occupation_id=occupation_id,
                assessment_series_id=series_id,
            )
        }

        for c in qs:
            book = next(
                (b for (cid, _bn), b in existing_books.items() if cid == c.id),
                None,
            )
            c._has_book = book is not None
            c._book_number = book.book_number if book else None

        return Response(WPCandidateSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# Book generation
# ---------------------------------------------------------------------------

def _build_book_data(candidate, occupation, levels_qs, signatures, request=None):
    """Assemble the dict consumed by ``generate_book_pdf``."""
    levels = []
    for lvl in levels_qs:
        modules = list(lvl.modules.filter(is_active=True).order_by('module_code'))
        levels.append({
            'level_name': lvl.level_name,
            'level_description': lvl.level_description or '',
            'competence_description': lvl.competence_description or '',
            'modules': [
                {
                    'module_name': m.module_name,
                    'module_code': m.module_code,
                    'wp_description': m.wp_description or '',
                    'wp_competence_items': m.wp_competence_items or '',
                }
                for m in modules
            ],
        })

    photo_path = None
    if candidate.passport_photo:
        try:
            photo_path = candidate.passport_photo.path
            if not os.path.exists(photo_path):
                photo_path = None
        except Exception:
            photo_path = None

    centre_name = ''
    if getattr(candidate, 'assessment_center', None):
        centre_name = candidate.assessment_center.center_name or \
                      candidate.assessment_center.center_number or ''

    return {
        'candidate_name': candidate.full_name or '',
        'date_of_birth': candidate.date_of_birth.strftime('%d/%m/%Y') if candidate.date_of_birth else '',
        'gender': (candidate.gender or '').title(),
        'reg_no': candidate.registration_number or '',
        'centre_name': centre_name,
        'occupation_name': occupation.occ_name,
        'occupation_wp_code': occupation.wp_code or '',
        'nationality': candidate.nationality or 'Uganda',
        'print_date': date.today().strftime('%d/%m/%Y'),
        'photo_path': photo_path,
        'levels': levels,
        'es_signature_path': signatures.get('es'),
        'cp_signature_path': signatures.get('cp'),
        'coat_of_arms_path': signatures.get('coat'),
        'uvtab_logo_path': signatures.get('logo'),
        'employment_history_pages': 4,  # 5 rows x 4 pages = 20 rows
    }


def _signature_paths():
    base = os.path.join(settings.BASE_DIR, 'static', 'images')
    paths = {
        'es': os.path.join(base, 'es_signature.jpg'),
        'cp': os.path.join(base, 'chairperson_signature.jpg'),
        'coat': os.path.join(base, 'coat_of_arms.png'),
        'logo': os.path.join(base, 'uvtab_logo.png'),
    }
    return {k: (v if os.path.exists(v) else None) for k, v in paths.items()}


@transaction.atomic
def _get_or_create_book(candidate, occupation, series, generated_by=None):
    """Return an existing WorkersPasBook (and bump reprint_count) or create a new one."""
    book = WorkersPasBook.objects.select_for_update().filter(
        candidate=candidate, occupation=occupation, assessment_series=series,
    ).first()
    if book is not None:
        book.reprint_count = (book.reprint_count or 0) + 1
        book.save(update_fields=['reprint_count', 'updated_at'])
        return book, False

    if not occupation.wp_code:
        raise ValueError(
            f"Occupation '{occupation.occ_name}' has no Worker's PAS code (wp_code) configured."
        )

    seq = WorkersPasBook.allocate_sequence()
    book_number = WorkersPasBook.format_book_number(occupation.wp_code, seq)
    book = WorkersPasBook.objects.create(
        candidate=candidate,
        occupation=occupation,
        assessment_series=series,
        sequence_number=seq,
        book_number=book_number,
        full_label=WorkersPasBook.format_full_label(book_number),
        generated_by=generated_by,
    )
    return book, True


def _render_pdf_for_book(book):
    """Render and save the PDF for ``book``, returning bytes."""
    occupation = book.occupation
    levels_qs = list(occupation.levels.filter(is_active=True).order_by('level_name'))
    sigs = _signature_paths()
    data = _build_book_data(book.candidate, occupation, levels_qs, sigs)
    data['full_label'] = book.full_label
    pdf_bytes = generate_book_pdf(data)

    book.pdf_file.save(
        f"workers_pas_{book.book_number.replace('/', '_')}.pdf",
        ContentFile(pdf_bytes), save=True,
    )
    return pdf_bytes


class WorkersPasBookViewSet(viewsets.ReadOnlyModelViewSet):
    """List and download generated books."""
    queryset = WorkersPasBook.objects.select_related(
        'candidate', 'occupation', 'assessment_series',
    ).all()
    serializer_class = WorkersPasBookSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['occupation', 'assessment_series', 'candidate']
    search_fields = ['book_number', 'candidate__full_name',
                     'candidate__registration_number']

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        book = self.get_object()
        if not book.pdf_file or not os.path.exists(book.pdf_file.path):
            pdf_bytes = _render_pdf_for_book(book)
        else:
            with open(book.pdf_file.path, 'rb') as f:
                pdf_bytes = f.read()
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = (
            f'inline; filename="{book.book_number.replace("/", "_")}.pdf"'
        )
        return resp


class WorkersPasGenerateView(APIView):
    """Generate a Worker's PAS booklet PDF for a single candidate."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        occupation_id = request.data.get('occupation_id')
        series_id = request.data.get('series_id')

        if not (candidate_id and occupation_id and series_id):
            return Response(
                {'detail': 'candidate_id, occupation_id and series_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        candidate = get_object_or_404(Candidate, pk=candidate_id)
        occupation = get_object_or_404(Occupation, pk=occupation_id)
        series = get_object_or_404(AssessmentSeries, pk=series_id)

        try:
            book, _created = _get_or_create_book(
                candidate, occupation, series,
                generated_by=request.user if request.user.is_authenticated else None,
            )
            pdf_bytes = _render_pdf_for_book(book)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = (
            f'inline; filename="{book.book_number.replace("/", "_")}.pdf"'
        )
        return resp


class WorkersPasBulkGenerateView(APIView):
    """
    Bulk-generate Worker's PAS booklets.

    Body params:
      occupation_id (required)
      series_id     (required)
      candidate_ids (optional list) - if omitted, generate for all eligible candidates
      mode          - 'single' (default, ZIP of A5 PDFs) or 'a4_2up'
                      (ZIP containing paired A4 PDFs + an "all.pdf")
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        occupation_id = request.data.get('occupation_id')
        series_id = request.data.get('series_id')
        candidate_ids = request.data.get('candidate_ids') or []
        mode = request.data.get('mode') or 'single'

        if not (occupation_id and series_id):
            return Response(
                {'detail': 'occupation_id and series_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        occupation = get_object_or_404(Occupation, pk=occupation_id)
        series = get_object_or_404(AssessmentSeries, pk=series_id)

        candidates_qs = Candidate.objects.filter(occupation=occupation)
        if candidate_ids:
            candidates_qs = candidates_qs.filter(id__in=candidate_ids)
        else:
            enrollments = CandidateEnrollment.objects.filter(
                assessment_series=series,
                candidate__occupation=occupation,
                is_active=True,
            ).values_list('candidate_id', flat=True)
            candidates_qs = candidates_qs.filter(id__in=list(set(enrollments)))
        candidates = list(candidates_qs.order_by('full_name'))

        if not candidates:
            return Response(
                {'detail': 'No candidates found matching the criteria.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate per-candidate PDFs (A5)
        generated = []
        for cand in candidates:
            try:
                book, _ = _get_or_create_book(
                    cand, occupation, series,
                    generated_by=request.user if request.user.is_authenticated else None,
                )
                pdf_bytes = _render_pdf_for_book(book)
                generated.append((book, pdf_bytes))
            except ValueError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            if mode == 'a4_2up':
                # Pair candidates two at a time and impose
                pairs = []
                i = 0
                while i < len(generated):
                    a = generated[i]
                    b = generated[i + 1] if i + 1 < len(generated) else None
                    pairs.append((a, b))
                    i += 2
                for idx, (a, b) in enumerate(pairs, start=1):
                    pdf_a = a[1]
                    pdf_b = b[1] if b else None
                    a_label = a[0].book_number.replace('/', '_')
                    b_label = b[0].book_number.replace('/', '_') if b else 'BLANK'
                    imposed = impose_2up_a4(pdf_a, pdf_b)
                    name = f"A4_pair_{idx:03d}_{a_label}_{b_label}.pdf"
                    zf.writestr(name, imposed)
            else:
                for book, pdf_bytes in generated:
                    name = f"{book.book_number.replace('/', '_')}.pdf"
                    zf.writestr(name, pdf_bytes)

        zip_buf.seek(0)
        filename = (
            f"workers_pas_{occupation.wp_code or occupation.occ_code}_"
            f"{series.name.replace(' ', '_')}_{mode}.zip"
        )
        resp = HttpResponse(zip_buf.getvalue(), content_type='application/zip')
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp
