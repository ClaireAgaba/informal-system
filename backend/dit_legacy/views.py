import csv
import json
import os
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.http import FileResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Extracted data directories
_DATA_DIR = Path(settings.BASE_DIR) / 'scripts' / 'dit_extract_data'
_PHOTOS_DIR = _DATA_DIR / 'photos'

# Caches for extracted data (loaded lazily)
_extracted_results_cache = None   # student_id -> list of exam dicts
_id_mapping_cache = None          # old_person_id -> student_id
_photo_mapping_cache = None       # student_id -> old_person_id (for all records)
_photo_pids_cache = None          # set of old_person_ids that have photo files


def _load_photo_mapping():
    """Load student_id → old_person_id mapping from photo_mapping.json."""
    global _photo_mapping_cache
    if _photo_mapping_cache is not None:
        return _photo_mapping_cache
    mapping_file = _DATA_DIR / 'photo_mapping.json'
    if mapping_file.is_file():
        with open(mapping_file) as f:
            _photo_mapping_cache = json.load(f)  # {"student_id": "old_person_id"}
    else:
        _photo_mapping_cache = {}
    return _photo_mapping_cache


def _load_photo_pids():
    """Return set of old_person_ids that actually have a photo file on disk."""
    global _photo_pids_cache
    if _photo_pids_cache is not None:
        return _photo_pids_cache
    _photo_pids_cache = set()
    if _PHOTOS_DIR.is_dir():
        for f in _PHOTOS_DIR.iterdir():
            if f.suffix == '.jpg' and f.stat().st_size > 0:
                _photo_pids_cache.add(f.stem)
    return _photo_pids_cache


def _load_id_mapping():
    """Load old_person_id → student_id mapping (reverse also available)."""
    global _id_mapping_cache
    if _id_mapping_cache is not None:
        return _id_mapping_cache
    mapping_file = _DATA_DIR / 'id_mapping.json'
    if mapping_file.is_file():
        with open(mapping_file) as f:
            _id_mapping_cache = json.load(f)  # old_person_id -> student_id
    else:
        _id_mapping_cache = {}
    return _id_mapping_cache


def _load_extracted_results():
    """Load extracted exam results keyed by student_id."""
    global _extracted_results_cache
    if _extracted_results_cache is not None:
        return _extracted_results_cache

    _extracted_results_cache = defaultdict(list)
    # photo_mapping.json: {student_id: old_person_id}
    # Build reverse: old_person_id → list of student_ids (many-to-one)
    photo_map = _load_photo_mapping()
    reverse = defaultdict(list)
    for sid, old_pid in photo_map.items():
        reverse[str(old_pid)].append(str(sid))

    for csv_name in ('results_test.csv', 'results.csv'):
        csv_path = _DATA_DIR / csv_name
        if csv_path.is_file():
            with open(csv_path, newline='') as f:
                for row in csv.DictReader(f):
                    old_pid = row.get('person_id', '')
                    student_ids = reverse.get(old_pid, [])
                    if not student_ids:
                        continue
                    result = {
                        'instance': row.get('instance', ''),
                        'exam_number': row.get('exam_number', ''),
                        'module_codes': row.get('module_codes', ''),
                        'certificate_number': row.get('certificate_number', ''),
                        'sponsored_by': row.get('sponsored_by', ''),
                        'language': row.get('language', ''),
                        'exam_date': row.get('exam_date', ''),
                        'paper': row.get('paper', ''),
                        'exam_mark': row.get('exam_mark', ''),
                        'exam_results': row.get('exam_results', ''),
                        'exam_grade': row.get('exam_grade', ''),
                        'exam_comment': row.get('exam_comment', ''),
                    }
                    for student_id in student_ids:
                        _extracted_results_cache[student_id].append(result)
            break  # Use the first file found

    return _extracted_results_cache


def _dictfetchall(cursor):
    """Convert cursor results to list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """
    Search legacy DIT candidates by registration number or name.
    Supports filters: q (search term), regno, gender, district, training_provider
    Supports pagination: page, page_size
    
    Optimised: avoids expensive JOINs in the count/data queries when
    district or training_provider filters are not active.
    """
    q = (request.query_params.get('q') or '').strip()
    name = (request.query_params.get('name') or '').strip()
    regno = (request.query_params.get('regno') or '').strip()
    gender = (request.query_params.get('gender') or '').strip()
    status = (request.query_params.get('status') or '').strip()
    district = (request.query_params.get('district') or '').strip()
    training_provider = (request.query_params.get('training_provider') or '').strip()

    # Pagination
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except ValueError:
        page = 1
    try:
        page_size = max(1, min(int(request.query_params.get('page_size', 50)), 100))
    except ValueError:
        page_size = 50

    offset = (page - 1) * page_size

    # Determine if we need the expensive JOINs
    needs_district_join = bool(district)
    needs_institution_join = bool(training_provider)
    needs_joins = needs_district_join or needs_institution_join

    # ── Build WHERE clause on the students table only ──
    student_params = []
    student_where = ["1=1"]

    if q:
        q_like = f"%{q.lower()}%"
        student_where.append(
            "("
            "LOWER(COALESCE(s.nsin, '')) LIKE %s "
            "OR LOWER(COALESCE(s.exam_no, '')) LIKE %s "
            "OR LOWER(COALESCE(s.firstname, '')) LIKE %s "
            "OR LOWER(COALESCE(s.othername, '')) LIKE %s "
            "OR LOWER(COALESCE(s.surname, '')) LIKE %s"
            ")"
        )
        student_params.extend([q_like] * 5)

    if name:
        name_like = f"%{name.lower()}%"
        student_where.append(
            "("
            "LOWER(COALESCE(s.firstname, '')) LIKE %s "
            "OR LOWER(COALESCE(s.othername, '')) LIKE %s "
            "OR LOWER(COALESCE(s.surname, '')) LIKE %s"
            ")"
        )
        student_params.extend([name_like] * 3)

    if regno:
        regno_like = f"%{regno.lower()}%"
        student_where.append(
            "("
            "LOWER(COALESCE(s.nsin, '')) LIKE %s "
            "OR LOWER(COALESCE(s.exam_no, '')) LIKE %s "
            "OR LOWER(COALESCE(s.certificate_no, '')) LIKE %s"
            ")"
        )
        student_params.extend([regno_like] * 3)

    if gender:
        student_where.append("LOWER(COALESCE(s.gender, '')) = %s")
        student_params.append(gender.lower())

    if status == 'completed':
        student_where.append("s.certificate_no IS NOT NULL AND s.certificate_no != ''")
    elif status == 'in_progress':
        student_where.append("(s.certificate_no IS NULL OR s.certificate_no = '')")

    # Extra WHERE conditions that need JOINs
    join_params = []
    join_where = []

    if district:
        join_where.append("LOWER(COALESCE(d.district_name, '')) LIKE %s")
        join_params.append(f"%{district.lower()}%")

    if training_provider:
        join_where.append("LOWER(COALESCE(i.institution_name, '')) LIKE %s")
        join_params.append(f"%{training_provider.lower()}%")

    try:
        with connections['dit_legacy'].cursor() as cursor:

            # ── COUNT ──
            if not needs_joins and not student_params:
                # No filters at all → fast table count
                cursor.execute("SELECT COUNT(*) FROM students")
            elif not needs_joins:
                # Filters only on the students table → no JOINs needed
                cursor.execute(
                    f"SELECT COUNT(*) FROM students s WHERE {' AND '.join(student_where)}",
                    student_params,
                )
            else:
                # Need JOINs for district / training_provider
                joins = ""
                if needs_district_join:
                    joins += " LEFT JOIN districts d ON d.district_id = s.district_id"
                if needs_institution_join:
                    joins += (
                        " LEFT JOIN students_registration sr ON sr.student_id = s.student_id"
                        " LEFT JOIN registrations r ON r.registration_id = sr.registration_id"
                        " LEFT JOIN institutions i ON i.institution_id = r.institution_id"
                    )
                all_where = student_where + join_where
                all_params = student_params + join_params
                cursor.execute(
                    f"SELECT COUNT(DISTINCT s.student_id) FROM students s{joins} WHERE {' AND '.join(all_where)}",
                    all_params,
                )

            total_count = cursor.fetchone()[0]

            # ── DATA (always fetch district & training_provider for display) ──
            # Use a sub-query to paginate on student_id first (fast),
            # then JOIN for display columns.
            inner_where = student_where
            inner_params = list(student_params)
            inner_joins = ""

            if needs_district_join:
                inner_joins += " LEFT JOIN districts d ON d.district_id = s.district_id"
            if needs_institution_join:
                inner_joins += (
                    " LEFT JOIN students_registration sr ON sr.student_id = s.student_id"
                    " LEFT JOIN registrations r ON r.registration_id = sr.registration_id"
                    " LEFT JOIN institutions i ON i.institution_id = r.institution_id"
                )
                inner_where = inner_where + join_where
                inner_params = inner_params + join_params

            if needs_joins:
                # When filtering by joined tables, we must include them in the inner query
                data_sql = f"""
                    SELECT
                        s2.student_id AS person_id,
                        s2.firstname AS first_name,
                        s2.othername AS other_name,
                        s2.surname AS surname,
                        s2.gender,
                        s2.dob AS birth_date,
                        COALESCE(s2.nsin, s2.exam_no) AS registration_number,
                        s2.certificate_no AS certificate_number,
                        i2.institution_name AS training_provider,
                        d2.district_name AS district
                    FROM (
                        SELECT DISTINCT s.student_id
                        FROM students s{inner_joins}
                        WHERE {' AND '.join(inner_where)}
                        ORDER BY s.student_id DESC
                        LIMIT %s OFFSET %s
                    ) ids
                    JOIN students s2 ON s2.student_id = ids.student_id
                    LEFT JOIN districts d2 ON d2.district_id = s2.district_id
                    LEFT JOIN students_registration sr2 ON sr2.student_id = s2.student_id
                    LEFT JOIN registrations r2 ON r2.registration_id = sr2.registration_id
                    LEFT JOIN institutions i2 ON i2.institution_id = r2.institution_id
                    ORDER BY s2.student_id DESC
                """
                data_params = inner_params + [page_size, offset]
            else:
                # No district/training_provider filter → paginate students first, then JOIN
                data_sql = f"""
                    SELECT
                        s2.student_id AS person_id,
                        s2.firstname AS first_name,
                        s2.othername AS other_name,
                        s2.surname AS surname,
                        s2.gender,
                        s2.dob AS birth_date,
                        COALESCE(s2.nsin, s2.exam_no) AS registration_number,
                        s2.certificate_no AS certificate_number,
                        i.institution_name AS training_provider,
                        d.district_name AS district
                    FROM (
                        SELECT s.student_id
                        FROM students s
                        WHERE {' AND '.join(student_where)}
                        ORDER BY s.student_id DESC
                        LIMIT %s OFFSET %s
                    ) ids
                    JOIN students s2 ON s2.student_id = ids.student_id
                    LEFT JOIN districts d ON d.district_id = s2.district_id
                    LEFT JOIN students_registration sr ON sr.student_id = s2.student_id
                    LEFT JOIN registrations r ON r.registration_id = sr.registration_id
                    LEFT JOIN institutions i ON i.institution_id = r.institution_id
                    ORDER BY s2.student_id DESC
                """
                data_params = student_params + [page_size, offset]

            cursor.execute(data_sql, data_params)
            rows = _dictfetchall(cursor)

    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e), 'results': [], 'count': 0, 'total_count': 0}, status=500)

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    # Annotate with photo availability
    photo_map = _load_photo_mapping()
    photo_pids = _load_photo_pids()
    for row in rows:
        old_pid = photo_map.get(str(row.get('person_id', '')))
        row['has_photo'] = old_pid is not None and old_pid in photo_pids

    return Response({
        'results': rows,
        'count': len(rows),
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def person_detail(request, person_id: str):
    """
    Get detailed information for a legacy DIT candidate by student_id.
    """
    sql = """
        SELECT
            s.student_id AS person_id,
            s.firstname AS first_name,
            s.othername AS other_name,
            s.surname AS surname,
            s.gender,
            s.dob AS birth_date,
            COALESCE(s.nsin, s.exam_no) AS registration_number,
            s.certificate_no AS certificate_number,
            s.nin AS national_id,
            s.telephone,
            s.email,
            s.home_address,
            s.village,
            s.subcountry AS subcounty,
            c.course_name AS occupation,
            c.course_code AS occupation_code,
            l.level_name AS level,
            d.district_name AS district,
            i.institution_name AS training_provider,
            i.short_name AS training_provider_short,
            id.district_name AS training_provider_district,
            r.year_proposed AS assessment_year,
            r.month_proposed AS assessment_month,
            r.actual_assessment_date,
            s.disadility_option AS disability_option,
            s.disability_name,
            s.academic_level,
            s.school AS academic_school,
            s.date_time AS registered_at
        FROM students s
        LEFT JOIN districts d ON d.district_id = s.district_id
        LEFT JOIN students_registration sr ON sr.student_id = s.student_id
        LEFT JOIN registrations r ON r.registration_id = sr.registration_id
        LEFT JOIN institutions i ON i.institution_id = r.institution_id
        LEFT JOIN districts id ON id.district_id = i.district_id
        LEFT JOIN courses c ON c.course_id = r.course_id
        LEFT JOIN levels l ON l.level_id = r.level_id
        WHERE s.student_id = %s
        ORDER BY r.year_proposed DESC, r.registration_id DESC
        LIMIT 1
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [person_id])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'detail': str(e)}, status=500)

    if not rows:
        return Response({'detail': 'Not found'}, status=404)

    return Response(rows[0])


@api_view(['GET'])
@permission_classes([AllowAny])
def person_photo(request, person_id: str):
    """
    Serve the passport photo image for a legacy DIT candidate.
    Uses photo_mapping.json to translate student_id → old_person_id filename.
    """
    photo_map = _load_photo_mapping()
    old_pid = photo_map.get(str(person_id))
    if old_pid:
        photo_path = _PHOTOS_DIR / f'{old_pid}.jpg'
        if photo_path.is_file():
            return FileResponse(open(photo_path, 'rb'), content_type='image/jpeg')

    # Fallback: try direct student_id match
    photo_path = _PHOTOS_DIR / f'{person_id}.jpg'
    if photo_path.is_file():
        return FileResponse(open(photo_path, 'rb'), content_type='image/jpeg')

    return Response({'detail': 'No photo found for this candidate'}, status=404)


@api_view(['GET'])
@permission_classes([AllowAny])
def person_results(request, person_id: str):
    """
    Get all registration/assessment history for a legacy DIT candidate.
    """
    limit = request.query_params.get('limit')
    try:
        limit = max(1, min(int(limit), 500)) if limit else 200
    except ValueError:
        limit = 200

    sql = """
        SELECT
            sr.student_registration_id,
            sr.registration_id,
            sr.cand_course_code_reg AS modules_assessed,
            sr.amount,
            sr.sponsored_by,
            r.year_proposed AS assessment_year,
            r.month_proposed AS assessment_month,
            r.actual_assessment_date,
            r.tr_start_date AS training_start,
            r.tr_end_date AS training_end,
            r.completed,
            r.verified,
            r.approved,
            r.printed AS certificate_printed,
            c.course_name AS occupation,
            c.course_code AS occupation_code,
            l.level_name AS level,
            i.institution_name AS training_provider,
            i.short_name AS training_provider_short,
            d.district_name AS training_provider_district
        FROM students_registration sr
        JOIN registrations r ON r.registration_id = sr.registration_id
        LEFT JOIN courses c ON c.course_id = r.course_id
        LEFT JOIN levels l ON l.level_id = r.level_id
        LEFT JOIN institutions i ON i.institution_id = r.institution_id
        LEFT JOIN districts d ON d.district_id = i.district_id
        WHERE sr.student_id = %s
        ORDER BY r.year_proposed DESC, r.registration_id DESC
        LIMIT %s
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [person_id, limit])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'person_id': person_id, 'error': str(e), 'results': [], 'exam_results': [], 'count': 0}, status=500)

    # Include extracted exam-level results (paper, mark, grade)
    extracted = _load_extracted_results()
    exam_results = extracted.get(str(person_id), [])

    return Response({
        'person_id': person_id,
        'results': rows,
        'exam_results': exam_results,
        'count': len(rows),
    })


# ── Editable field → legacy DB column mapping ──
_EDITABLE_FIELDS = {
    # Biodata
    'first_name': 'firstname',
    'other_name': 'othername',
    'surname': 'surname',
    'gender': 'gender',
    'birth_date': 'dob',
    'national_id': 'nin',
    'telephone': 'telephone',
    'email': 'email',
    # Location
    'subcounty': 'subcountry',
    'village': 'village',
    'home_address': 'home_address',
    # Special needs
    'disability_option': 'disadility_option',
    'disability_name': 'disability_name',
}

# Human-readable labels for audit log
_FIELD_LABELS = {
    'first_name': 'First Name',
    'other_name': 'Other Name',
    'surname': 'Surname',
    'gender': 'Gender',
    'birth_date': 'Birth Date',
    'national_id': 'National ID',
    'telephone': 'Telephone',
    'email': 'Email',
    'district': 'District',
    'subcounty': 'Sub County',
    'village': 'Village',
    'home_address': 'Home Address',
    'disability_option': 'Has Disability',
    'disability_name': 'Disability',
    'passport_photo': 'Passport Photo',
}


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_person(request, person_id: str):
    """
    Update editable fields on a legacy DIT candidate record.
    Writes changes to the legacy DB and creates audit log entries.
    """
    from .models import DitLegacyAuditLog

    data = request.data
    if not data:
        return Response({'detail': 'No data provided'}, status=400)

    # --- Handle photo upload separately ---
    photo_file = request.FILES.get('passport_photo')

    # --- Fetch current values for audit comparison ---
    current_cols = list(set(_EDITABLE_FIELDS.values()))
    current_cols.append('district_id')
    select_cols = ', '.join(f's.{c}' for c in current_cols)

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(
                f"SELECT {select_cols} FROM students s WHERE s.student_id = %s",
                [person_id],
            )
            row = cursor.fetchone()
            if not row:
                return Response({'detail': 'Not found'}, status=404)
            col_names = [col[0] for col in cursor.description]
            current = dict(zip(col_names, row))
    except (ProgrammingError, OperationalError) as e:
        return Response({'detail': str(e)}, status=500)

    # Reverse lookup: db column → current value
    db_col_to_current = current

    # --- Build SET clause for the update ---
    set_parts = []
    set_params = []
    audit_entries = []

    changed_by = request.user if request.user.is_authenticated else None
    changed_by_name = ''
    if changed_by:
        changed_by_name = changed_by.get_full_name() or changed_by.username

    for field_name, db_col in _EDITABLE_FIELDS.items():
        if field_name not in data:
            continue
        new_val = str(data[field_name]).strip() if data[field_name] is not None else ''
        old_val = str(db_col_to_current.get(db_col) or '')

        if new_val != old_val:
            set_parts.append(f"{db_col} = %s")
            set_params.append(new_val if new_val else None)
            audit_entries.append(DitLegacyAuditLog(
                person_id=person_id,
                field_name=_FIELD_LABELS.get(field_name, field_name),
                old_value=old_val,
                new_value=new_val,
                changed_by=changed_by,
                changed_by_name=changed_by_name,
            ))

    # Handle district by name → district_id
    if 'district' in data:
        new_district = str(data['district']).strip()
        try:
            with connections['dit_legacy'].cursor() as cursor:
                # Get current district name
                cursor.execute(
                    "SELECT d.district_name FROM districts d WHERE d.district_id = %s",
                    [current.get('district_id') or 0],
                )
                old_row = cursor.fetchone()
                old_district = old_row[0] if old_row else ''

                if new_district.lower() != (old_district or '').lower():
                    # Look up new district_id
                    cursor.execute(
                        "SELECT district_id FROM districts WHERE LOWER(district_name) = %s LIMIT 1",
                        [new_district.lower()],
                    )
                    dist_row = cursor.fetchone()
                    if dist_row:
                        set_parts.append("district_id = %s")
                        set_params.append(dist_row[0])
                        audit_entries.append(DitLegacyAuditLog(
                            person_id=person_id,
                            field_name='District',
                            old_value=old_district or '',
                            new_value=new_district,
                            changed_by=changed_by,
                            changed_by_name=changed_by_name,
                        ))
        except (ProgrammingError, OperationalError):
            pass  # Skip district update if lookup fails

    # Handle photo upload
    if photo_file:
        photo_path = _PHOTOS_DIR / f'{person_id}.jpg'
        _PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        had_photo = photo_path.is_file()
        with open(photo_path, 'wb') as f:
            for chunk in photo_file.chunks():
                f.write(chunk)
        audit_entries.append(DitLegacyAuditLog(
            person_id=person_id,
            field_name='Passport Photo',
            old_value='(existing photo)' if had_photo else '(no photo)',
            new_value='(new photo uploaded)',
            changed_by=changed_by,
            changed_by_name=changed_by_name,
        ))

    if not set_parts and not audit_entries:
        return Response({'detail': 'No changes detected'}, status=200)

    # --- Execute the UPDATE ---
    if set_parts:
        try:
            with connections['dit_legacy'].cursor() as cursor:
                sql = f"UPDATE students SET {', '.join(set_parts)} WHERE student_id = %s"
                cursor.execute(sql, set_params + [person_id])
        except (ProgrammingError, OperationalError) as e:
            return Response({'detail': str(e)}, status=500)

    # --- Save audit log entries ---
    if audit_entries:
        DitLegacyAuditLog.objects.bulk_create(audit_entries)

    return Response({
        'detail': 'Updated successfully',
        'changes': len(audit_entries),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def person_audit_logs(request, person_id: str):
    """
    Get audit logs for a legacy DIT candidate.
    """
    from .models import DitLegacyAuditLog

    logs = DitLegacyAuditLog.objects.filter(person_id=person_id).values(
        'id', 'field_name', 'old_value', 'new_value',
        'changed_by_name', 'changed_at',
    )

    return Response({
        'person_id': person_id,
        'logs': list(logs),
        'count': len(logs),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_districts(request):
    """
    Get all districts from the legacy database.
    """
    sql = """
        SELECT district_id, district_name
        FROM districts
        ORDER BY district_name
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql)
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e), 'results': []}, status=500)

    return Response({'results': rows, 'count': len(rows)})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_institutions(request):
    """
    Get all training providers/institutions from the legacy database.
    Supports optional district filter.
    """
    district = request.query_params.get('district', '').strip()
    limit = request.query_params.get('limit')
    try:
        limit = max(1, min(int(limit), 500)) if limit else 200
    except ValueError:
        limit = 200

    params = []
    where = ["1=1"]

    if district:
        where.append("LOWER(d.district_name) LIKE %s")
        params.append(f"%{district.lower()}%")

    sql = f"""
        SELECT
            i.institution_id,
            i.institution_name,
            i.short_name,
            i.box_no,
            i.assement_phone_no AS phone,
            i.email,
            i.centre_category,
            i.modular AS offers_modular,
            i.workers_pas AS offers_workers_pas,
            d.district_name AS district
        FROM institutions i
        LEFT JOIN districts d ON d.district_id = i.district_id
        WHERE {' AND '.join(where)}
        ORDER BY i.institution_name
        LIMIT %s
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [*params, limit])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e), 'results': []}, status=500)

    return Response({'results': rows, 'count': len(rows)})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_courses(request):
    """
    Get all courses/occupations from the legacy database.
    """
    sql = """
        SELECT course_id, course_name, course_code, worker_pas_code
        FROM courses
        ORDER BY course_name
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql)
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e), 'results': []}, status=500)

    return Response({'results': rows, 'count': len(rows)})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_levels(request):
    """
    Get all assessment levels from the legacy database.
    """
    sql = """
        SELECT level_id, level_name
        FROM levels
        ORDER BY level_id
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql)
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e), 'results': []}, status=500)

    return Response({'results': rows, 'count': len(rows)})


@api_view(['GET'])
@permission_classes([AllowAny])
def stats(request):
    """
    Get statistics from the legacy database.
    """
    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM institutions")
            total_institutions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM registrations")
            total_registrations = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM courses")
            total_courses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT district_id) FROM students WHERE district_id > 0")
            districts_with_candidates = cursor.fetchone()[0]

    except (ProgrammingError, OperationalError) as e:
        return Response({'error': str(e)}, status=500)

    return Response({
        'total_candidates': total_students,
        'total_training_providers': total_institutions,
        'total_registrations': total_registrations,
        'total_occupations': total_courses,
        'districts_with_candidates': districts_with_candidates,
    })
