from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


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
    regno = (request.query_params.get('regno') or '').strip()
    gender = (request.query_params.get('gender') or '').strip()
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
    Get passport photo for a legacy DIT candidate.
    Photos are stored in the students.passport field as file paths.
    """
    sql = """
        SELECT passport
        FROM students
        WHERE student_id = %s
        LIMIT 1
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [person_id])
            row = cursor.fetchone()
    except (ProgrammingError, OperationalError) as e:
        return Response({'detail': str(e)}, status=500)

    if not row or not row[0] or row[0] == 'none':
        return Response({'detail': 'No photo found for this candidate'}, status=404)

    return Response({'detail': 'Photo path found', 'path': row[0]})


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
        return Response({'person_id': person_id, 'error': str(e), 'results': [], 'count': 0}, status=500)

    return Response({'person_id': person_id, 'results': rows, 'count': len(rows)})


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
