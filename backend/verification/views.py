from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from candidates.models import Candidate


def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _search_current_candidates(q):
    """Search current UVTAB candidates by registration number, certificate number, or name."""
    qs = Candidate.objects.select_related(
        'assessment_center', 'occupation', 'district',
    ).filter(is_submitted=True)

    # Try exact match on registration_number first
    exact = qs.filter(registration_number__iexact=q)
    if exact.exists():
        qs = exact
    else:
        # Try certificate / transcript serial number exact match
        exact_cert = qs.filter(transcript_serial_number__iexact=q)
        if exact_cert.exists():
            qs = exact_cert
        else:
            # Fallback: LIKE search on regno, name, payment code
            from django.db.models import Q
            qs = qs.filter(
                Q(registration_number__icontains=q)
                | Q(transcript_serial_number__icontains=q)
                | Q(payment_code__icontains=q)
                | Q(full_name__icontains=q)
            )

    results = []
    for c in qs[:20]:
        results.append({
            'source': 'current',
            'person_id': c.id,
            'registration_number': c.registration_number or '',
            'full_name': c.full_name,
            'gender': c.gender or '',
            'date_of_birth': str(c.date_of_birth) if c.date_of_birth else '',
            'contact': c.contact or '',
            'district': c.district.name if c.district else '',
            'assessment_center': c.assessment_center.center_name if c.assessment_center else '',
            'center_number': c.assessment_center.center_number if c.assessment_center else '',
            'occupation': c.occupation.occ_name if c.occupation else '',
            'occupation_code': c.occupation.occ_code if c.occupation else '',
            'registration_category': c.get_registration_category_display() if c.registration_category else '',
            'entry_year': c.entry_year,
            'intake': c.get_intake_display() if c.intake else '',
            'transcript_serial_number': c.transcript_serial_number or '',
            'payment_code': c.payment_code or '',
            'status': c.status,
            'is_graduated': c.is_graduated,
            'graduation_status': c.graduation_status,
            'has_passport_photo': bool(c.passport_photo),
        })
    return results


def _search_legacy_candidates(q):
    """Search DIT legacy candidates by registration number, certificate number, or name."""
    q_like = f"%{q}%"

    sql = """
        SELECT
            s.student_id AS person_id,
            s.firstname AS first_name,
            s.othername AS other_name,
            s.surname,
            s.gender,
            s.dob AS date_of_birth,
            s.telephone AS contact,
            COALESCE(s.nsin, s.exam_no) AS registration_number,
            s.certificate_no AS certificate_number,
            d.district_name AS district,
            i.institution_name AS training_provider,
            c.course_name AS occupation,
            c.course_code AS occupation_code,
            l.level_name AS level,
            r.year_proposed AS assessment_year
        FROM students s
        LEFT JOIN districts d ON d.district_id = s.district_id
        LEFT JOIN students_registration sr ON sr.student_id = s.student_id
        LEFT JOIN registrations r ON r.registration_id = sr.registration_id
        LEFT JOIN institutions i ON i.institution_id = r.institution_id
        LEFT JOIN courses c ON c.course_id = r.course_id
        LEFT JOIN levels l ON l.level_id = r.level_id
        WHERE (
            LOWER(COALESCE(s.nsin, '')) LIKE %s
            OR LOWER(COALESCE(s.exam_no, '')) LIKE %s
            OR LOWER(COALESCE(s.certificate_no, '')) LIKE %s
            OR LOWER(COALESCE(s.firstname, '')) LIKE %s
            OR LOWER(COALESCE(s.othername, '')) LIKE %s
            OR LOWER(COALESCE(s.surname, '')) LIKE %s
        )
        ORDER BY s.student_id DESC
        LIMIT 20
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            params = [q_like.lower()] * 6
            cursor.execute(sql, params)
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError):
        return []

    results = []
    for r in rows:
        full_name = ' '.join(filter(None, [r.get('first_name'), r.get('other_name'), r.get('surname')]))
        cert_no = r.get('certificate_number') or ''
        results.append({
            'source': 'dit_legacy',
            'person_id': r.get('person_id'),
            'registration_number': r.get('registration_number') or '',
            'full_name': full_name,
            'gender': r.get('gender') or '',
            'date_of_birth': str(r['date_of_birth']) if r.get('date_of_birth') else '',
            'contact': r.get('contact') or '',
            'district': r.get('district') or '',
            'assessment_center': r.get('training_provider') or '',
            'center_number': '',
            'occupation': r.get('occupation') or '',
            'occupation_code': r.get('occupation_code') or '',
            'registration_category': '',
            'entry_year': r.get('assessment_year'),
            'intake': '',
            'transcript_serial_number': '',
            'certificate_number': cert_no,
            'payment_code': '',
            'status': 'completed' if cert_no else 'active',
            'is_graduated': bool(cert_no),
            'graduation_status': 'Graduated' if cert_no else 'Active',
            'level': r.get('level') or '',
            'has_passport_photo': False,
        })
    return results


@api_view(['GET'])
@permission_classes([AllowAny])
def verify(request):
    """
    Unified verification endpoint for the UVTAB website.
    Searches both current EMIS candidates and DIT legacy candidates.

    Query params:
        q         – registration number, certificate number, transcript serial,
                    payment code, or candidate name (required)
        source    – optional filter: 'current', 'dit_legacy', or omit for both
    """
    q = (request.query_params.get('q') or '').strip()
    source = (request.query_params.get('source') or '').strip().lower()

    if not q or len(q) < 2:
        return Response({
            'detail': 'Please provide a search query (at least 2 characters).',
            'results': [],
            'count': 0,
        }, status=400)

    results = []

    if source in ('', 'current'):
        results.extend(_search_current_candidates(q))

    if source in ('', 'dit_legacy'):
        results.extend(_search_legacy_candidates(q))

    return Response({
        'query': q,
        'source_filter': source or 'all',
        'results': results,
        'count': len(results),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_detail(request, source, person_id):
    """
    Get full details for a verified candidate.

    URL: /api/verify/<source>/<person_id>/
    source: 'current' or 'dit_legacy'
    """
    if source == 'current':
        try:
            c = Candidate.objects.select_related(
                'assessment_center', 'occupation', 'district',
                'nature_of_disability',
            ).get(pk=person_id, is_submitted=True)
        except Candidate.DoesNotExist:
            return Response({'detail': 'Candidate not found'}, status=404)

        data = {
            'source': 'current',
            'person_id': c.id,
            'registration_number': c.registration_number or '',
            'full_name': c.full_name,
            'gender': c.gender or '',
            'date_of_birth': str(c.date_of_birth) if c.date_of_birth else '',
            'contact': c.contact or '',
            'district': c.district.name if c.district else '',
            'nationality': str(c.candidate_country) if c.candidate_country else c.nationality or '',
            'assessment_center': c.assessment_center.center_name if c.assessment_center else '',
            'center_number': c.assessment_center.center_number if c.assessment_center else '',
            'occupation': c.occupation.occ_name if c.occupation else '',
            'occupation_code': c.occupation.occ_code if c.occupation else '',
            'registration_category': c.get_registration_category_display() if c.registration_category else '',
            'entry_year': c.entry_year,
            'intake': c.get_intake_display() if c.intake else '',
            'start_date': str(c.start_date) if c.start_date else '',
            'finish_date': str(c.finish_date) if c.finish_date else '',
            'assessment_date': str(c.assessment_date) if c.assessment_date else '',
            'transcript_serial_number': c.transcript_serial_number or '',
            'payment_code': c.payment_code or '',
            'status': c.status,
            'is_graduated': c.is_graduated,
            'graduation_status': c.graduation_status,
            'has_disability': c.has_disability,
            'disability': c.nature_of_disability.name if c.nature_of_disability else '',
            'has_passport_photo': bool(c.passport_photo),
            'passport_photo_url': c.passport_photo.url if c.passport_photo else '',
        }
        return Response(data)

    elif source == 'dit_legacy':
        sql = """
            SELECT
                s.student_id AS person_id,
                s.firstname AS first_name,
                s.othername AS other_name,
                s.surname,
                s.gender,
                s.dob AS date_of_birth,
                s.telephone AS contact,
                s.email,
                s.nin AS national_id,
                COALESCE(s.nsin, s.exam_no) AS registration_number,
                s.certificate_no AS certificate_number,
                s.home_address,
                s.village,
                s.subcountry AS subcounty,
                d.district_name AS district,
                i.institution_name AS training_provider,
                i.short_name AS training_provider_short,
                c.course_name AS occupation,
                c.course_code AS occupation_code,
                l.level_name AS level,
                r.year_proposed AS assessment_year,
                r.actual_assessment_date,
                s.disadility_option AS disability_option,
                s.disability_name
            FROM students s
            LEFT JOIN districts d ON d.district_id = s.district_id
            LEFT JOIN students_registration sr ON sr.student_id = s.student_id
            LEFT JOIN registrations r ON r.registration_id = sr.registration_id
            LEFT JOIN institutions i ON i.institution_id = r.institution_id
            LEFT JOIN courses c ON c.course_id = r.course_id
            LEFT JOIN levels l ON l.level_id = r.level_id
            WHERE s.student_id = %s
            ORDER BY r.year_proposed DESC
            LIMIT 1
        """
        try:
            with connections['dit_legacy'].cursor() as cursor:
                cursor.execute(sql, [person_id])
                rows = _dictfetchall(cursor)
        except (ProgrammingError, OperationalError):
            return Response({'detail': 'Database error'}, status=500)

        if not rows:
            return Response({'detail': 'Candidate not found'}, status=404)

        r = rows[0]
        full_name = ' '.join(filter(None, [r.get('first_name'), r.get('other_name'), r.get('surname')]))
        cert_no = r.get('certificate_number') or ''

        data = {
            'source': 'dit_legacy',
            'person_id': r.get('person_id'),
            'registration_number': r.get('registration_number') or '',
            'full_name': full_name,
            'gender': r.get('gender') or '',
            'date_of_birth': str(r['date_of_birth']) if r.get('date_of_birth') else '',
            'contact': r.get('contact') or '',
            'email': r.get('email') or '',
            'national_id': r.get('national_id') or '',
            'district': r.get('district') or '',
            'subcounty': r.get('subcounty') or '',
            'village': r.get('village') or '',
            'assessment_center': r.get('training_provider') or '',
            'assessment_center_short': r.get('training_provider_short') or '',
            'occupation': r.get('occupation') or '',
            'occupation_code': r.get('occupation_code') or '',
            'level': r.get('level') or '',
            'assessment_year': r.get('assessment_year'),
            'actual_assessment_date': str(r['actual_assessment_date']) if r.get('actual_assessment_date') else '',
            'certificate_number': cert_no,
            'status': 'completed' if cert_no else 'active',
            'is_graduated': bool(cert_no),
            'graduation_status': 'Graduated' if cert_no else 'Active',
            'has_disability': r.get('disability_option') == 'Yes' or bool(r.get('disability_name')),
            'disability': r.get('disability_name') or '',
            'photo_url': f"/api/dit-legacy/person/{r.get('person_id')}/photo/",
        }
        return Response(data)

    else:
        return Response({'detail': 'Invalid source. Use "current" or "dit_legacy".'}, status=400)
