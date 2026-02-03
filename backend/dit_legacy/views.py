from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response


def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@api_view(['GET'])
def search(request):
    q = (request.query_params.get('q') or '').strip()
    gender = (request.query_params.get('gender') or '').strip()
    district = (request.query_params.get('district') or '').strip()
    training_provider = (request.query_params.get('training_provider') or '').strip()
    limit = request.query_params.get('limit')
    try:
        limit = max(1, min(int(limit), 200)) if limit else 50
    except ValueError:
        limit = 50

    params = []
    where = ["1=1"]

    if q:
        q_like = f"%{q.lower()}%"
        where.append(
            "("
            "LOWER(COALESCE(`reg_no+id_num`, '')) LIKE %s "
            "OR LOWER(COALESCE(`primary_form+firstname`, '')) LIKE %s "
            "OR LOWER(COALESCE(`primary_form+othername`, '')) LIKE %s "
            "OR LOWER(COALESCE(`primary_form+surname`, '')) LIKE %s"
            ")"
        )
        params.extend([q_like, q_like, q_like, q_like])

    if gender:
        where.append("LOWER(COALESCE(`demographic+gender`, '')) = %s")
        params.append(gender.lower())

    if district:
        where.append("LOWER(COALESCE(`trainingprovider+district`, '')) LIKE %s")
        params.append(f"%{district.lower()}%")

    if training_provider:
        where.append("LOWER(COALESCE(`trainingprovider+name`, '')) LIKE %s")
        params.append(f"%{training_provider.lower()}%")

    sql = f"""
        SELECT
            `primary_form+id` AS person_id,
            `primary_form+firstname` AS first_name,
            `primary_form+othername` AS other_name,
            `primary_form+surname` AS surname,
            `demographic+gender` AS gender,
            `demographic+birth_date` AS birth_date,
            `reg_no+id_num` AS registration_number,
            `person_instance+certificate_number` AS certificate_number,
            `trainingprovider+name` AS training_provider,
            `trainingprovider+district` AS district
        FROM zebra_search_person
        WHERE {' AND '.join(where)}
        ORDER BY last_modified DESC
        LIMIT %s
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [*params, limit])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError):
        fallback_params = []
        fallback_where = ["1=1"]

        if q:
            q_like = f"%{q.lower()}%"
            fallback_where.append(
                "(LOWER(COALESCE(p.firstname, '')) LIKE %s "
                "OR LOWER(COALESCE(p.othername, '')) LIKE %s "
                "OR LOWER(COALESCE(p.surname, '')) LIKE %s)"
            )
            fallback_params.extend([q_like, q_like, q_like])

        fallback_sql = f"""
            SELECT
                p.id AS person_id,
                p.firstname AS first_name,
                p.othername AS other_name,
                p.surname AS surname,
                NULL AS gender,
                NULL AS birth_date,
                NULL AS registration_number,
                NULL AS certificate_number,
                NULL AS training_provider,
                NULL AS district
            FROM hippo_person p
            WHERE {' AND '.join(fallback_where)}
            ORDER BY p.id DESC
            LIMIT %s
        """

        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(fallback_sql, [*fallback_params, limit])
            rows = _dictfetchall(cursor)

    return Response({'results': rows, 'count': len(rows)})


@api_view(['GET'])
def person_detail(request, person_id: str):
    sql = """
        SELECT
            p.id AS person_id,
            p.firstname AS first_name,
            p.othername AS other_name,
            p.surname AS surname,
            p.nationality AS nationality,
            p.residence AS residence,
            p.village AS village,
            p.subcounty AS subcounty,
            p.home_address AS home_address,
            p.is_disabled AS is_disabled,
            p.disability AS disability,
            s.`demographic+gender` AS gender,
            s.`demographic+birth_date` AS birth_date,
            s.`reg_no+id_num` AS registration_number,
            s.`person_instance+certificate_number` AS certificate_number,
            s.`trainingprovider+name` AS training_provider,
            s.`trainingprovider+district` AS district,
            s.`trainingprovider+ownership` AS ownership,
            s.`provider_instance+level` AS level,
            s.`provider_instance+actual_date` AS actual_date
        FROM hippo_person p
        LEFT JOIN zebra_search_person s ON s.`primary_form+id` = p.id
        WHERE p.id = %s
        LIMIT 1
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [person_id])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError):
        fallback_sql = """
            SELECT
                p.id AS person_id,
                p.firstname AS first_name,
                p.othername AS other_name,
                p.surname AS surname,
                p.nationality AS nationality,
                p.residence AS residence,
                p.village AS village,
                p.subcounty AS subcounty,
                p.home_address AS home_address,
                p.is_disabled AS is_disabled,
                p.disability AS disability,
                NULL AS gender,
                NULL AS birth_date,
                NULL AS registration_number,
                NULL AS certificate_number,
                NULL AS training_provider,
                NULL AS district,
                NULL AS ownership,
                NULL AS level,
                NULL AS actual_date
            FROM hippo_person p
            WHERE p.id = %s
            LIMIT 1
        """

        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(fallback_sql, [person_id])
            rows = _dictfetchall(cursor)

    if not rows:
        return Response({'detail': 'Not found'}, status=404)

    return Response(rows[0])


def _fetch_marksheet(table_name: str, person_id: str, limit: int = 200):
    sql = f"""
        SELECT
            last_modified,
            `reg_no+id_num` AS registration_number,
            `primary_form+actual_date` AS actual_date,
            `primary_form+level` AS level,
            `primary_form+location` AS location,
            `training_provider+name` AS training_provider,
            `training_provider+district` AS district,
            `training+training_classification` AS training_classification,
            `primary_form+module_assessed` AS module_assessed,
            `primary_form+second_module_assessed` AS second_module_assessed,
            `paper_i+paper` AS paper_i_paper,
            `paper_i+results` AS paper_i_results,
            `paper_i+exam_grade` AS paper_i_grade,
            `paper_i+exam_comment` AS paper_i_comment,
            `paper_ii+paper` AS paper_ii_paper,
            `paper_ii+results` AS paper_ii_results,
            `paper_ii+exam_grade` AS paper_ii_grade,
            `paper_ii+exam_comment` AS paper_ii_comment,
            `paper_iii+paper` AS paper_iii_paper,
            `paper_iii+results` AS paper_iii_results,
            `paper_iii+exam_grade` AS paper_iii_grade,
            `paper_iv+paper` AS paper_iv_paper,
            `paper_iv+results` AS paper_iv_results,
            `paper_iv+exam_grade` AS paper_iv_grade
        FROM `{table_name}`
        WHERE `person+id` = %s
        ORDER BY last_modified DESC
        LIMIT %s
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(sql, [person_id, limit])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError):
        return []

    out = []
    for r in rows:
        papers = []
        for key in ['i', 'ii', 'iii', 'iv']:
            paper = r.get(f'paper_{key}_paper')
            results = r.get(f'paper_{key}_results')
            grade = r.get(f'paper_{key}_grade')
            comment = r.get(f'paper_{key}_comment')
            if paper is None and results is None and grade is None and comment is None:
                continue
            papers.append({
                'paper': paper,
                'results': results,
                'grade': grade,
                'comment': comment,
            })

        out.append({
            'source_table': table_name,
            'last_modified': r.get('last_modified'),
            'registration_number': r.get('registration_number'),
            'actual_date': r.get('actual_date'),
            'level': r.get('level'),
            'location': r.get('location'),
            'training_provider': r.get('training_provider'),
            'district': r.get('district'),
            'training_classification': r.get('training_classification'),
            'module_assessed': r.get('module_assessed'),
            'second_module_assessed': r.get('second_module_assessed'),
            'papers': papers,
        })

    return out


def _guess_image_content_type(blob: bytes) -> str:
    if not blob:
        return 'application/octet-stream'
    if blob.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    if blob.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if blob[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    return 'application/octet-stream'


def _fetch_person_photo_md5(person_id: str):
    candidates = [
        ('zebra_marksheet_modular', 'md5'),
        ('zebra_marksheet_practical', 'md5'),
        ('zebra_marksheet_theory_and_practical', 'md5'),
        ('zebra_marksheet_multiple', 'md5'),
    ]

    for table, col in candidates:
        sql = f"""
            SELECT {col} AS md5
            FROM `{table}`
            WHERE `person+id` = %s AND {col} IS NOT NULL
            ORDER BY last_modified DESC
            LIMIT 1
        """
        try:
            with connections['dit_legacy'].cursor() as cursor:
                cursor.execute(sql, [person_id])
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
        except (ProgrammingError, OperationalError):
            continue

    # Some dumps use last_md5 (e.g. modular/multiple).
    candidates_last = [
        ('zebra_marksheet_modular', 'last_md5'),
        ('zebra_marksheet_multiple', 'last_md5'),
    ]

    for table, col in candidates_last:
        sql = f"""
            SELECT {col} AS md5
            FROM `{table}`
            WHERE `person+id` = %s AND {col} IS NOT NULL
            ORDER BY last_modified DESC
            LIMIT 1
        """
        try:
            with connections['dit_legacy'].cursor() as cursor:
                cursor.execute(sql, [person_id])
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
        except (ProgrammingError, OperationalError):
            continue

    return None


_PHOTO_BLOB_CANDIDATES = None


def _get_photo_blob_candidates():
    global _PHOTO_BLOB_CANDIDATES
    if _PHOTO_BLOB_CANDIDATES is not None:
        return _PHOTO_BLOB_CANDIDATES

    schema = connections['dit_legacy'].settings_dict.get('NAME')

    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND DATA_TYPE IN ('blob','mediumblob','longblob','tinyblob')
            """,
            [schema],
        )
        blob_cols = _dictfetchall(cursor)

    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND DATA_TYPE IN ('binary','varbinary')
              AND CHARACTER_MAXIMUM_LENGTH = 16
            """,
            [schema],
        )
        key_cols = _dictfetchall(cursor)

    blob_by_table = {}
    for b in blob_cols:
        t = b.get('TABLE_NAME')
        c = b.get('COLUMN_NAME')
        if not t or not c:
            continue
        blob_by_table.setdefault(t, []).append(c)

    key_by_table = {}
    for k in key_cols:
        t = k.get('TABLE_NAME')
        c = k.get('COLUMN_NAME')
        if not t or not c:
            continue
        key_by_table.setdefault(t, []).append(c)

    candidates = []
    for table, blobs in blob_by_table.items():
        keys = key_by_table.get(table) or []
        if not keys:
            continue

        def blob_rank(name: str) -> int:
            n = (name or '').lower()
            if n in ('photo', 'image', 'data', 'content', 'file', 'blob'):
                return 0
            if 'photo' in n or 'image' in n:
                return 1
            return 2

        def key_rank(name: str) -> int:
            n = (name or '').lower()
            if n == 'md5':
                return 0
            if n == 'last_md5':
                return 1
            if 'md5' in n or 'hash' in n or 'checksum' in n:
                return 2
            return 3

        blobs_sorted = sorted(blobs, key=blob_rank)
        keys_sorted = sorted(keys, key=key_rank)

        for key_col in keys_sorted:
            for blob_col in blobs_sorted:
                candidates.append({'table': table, 'key_col': key_col, 'blob_col': blob_col})

    _PHOTO_BLOB_CANDIDATES = candidates
    return candidates


def _fetch_photo_blob_by_md5(md5_bytes: bytes):
    if isinstance(md5_bytes, memoryview):
        md5_bytes = md5_bytes.tobytes()
    elif hasattr(md5_bytes, 'tobytes'):
        try:
            md5_bytes = md5_bytes.tobytes()
        except Exception:
            pass

    for c in _get_photo_blob_candidates():
        table = c.get('table')
        key_col = c.get('key_col')
        blob_col = c.get('blob_col')
        if not table or not key_col or not blob_col:
            continue

        q = f"SELECT `{blob_col}` FROM `{table}` WHERE `{key_col}` = %s LIMIT 1"
        try:
            with connections['dit_legacy'].cursor() as cursor:
                cursor.execute(q, [md5_bytes])
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
        except (ProgrammingError, OperationalError):
            continue

    return None


@api_view(['GET'])
def person_photo(request, person_id: str):
    md5_bytes = _fetch_person_photo_md5(person_id)
    if not md5_bytes:
        return Response({'detail': 'No photo reference found for this candidate'}, status=404)

    if isinstance(md5_bytes, memoryview):
        md5_bytes = md5_bytes.tobytes()

    try:
        blob = _fetch_photo_blob_by_md5(md5_bytes)
    except (ProgrammingError, OperationalError):
        blob = None

    if not blob:
        md5_hex = md5_bytes.hex() if isinstance(md5_bytes, (bytes, bytearray)) else None
        return Response(
            {
                'detail': 'Photo reference found but image bytes are missing from current DB import',
                'md5': md5_hex,
            },
            status=404,
        )

    content_type = _guess_image_content_type(blob)
    resp = HttpResponse(blob, content_type=content_type)
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp


def _fetch_hippo_exams(person_id: str, limit: int = 500):
    rich_sql = """
        SELECT
            e.last_modified,
            e.exam_date,
            e.paper AS paper_id,
            p.name AS paper_name,
            e.results AS mark,
            e.exam_grade AS grade_id,
            g.name AS grade_name,
            e.exam_comment
        FROM hippo_person_exam e
        JOIN hippo_person_instance i ON i.id = e.parent
        LEFT JOIN hippo_paper p ON p.id = e.paper
        LEFT JOIN hippo_exam_grade g ON g.id = e.exam_grade
        WHERE i.parent = %s
        ORDER BY e.last_modified DESC
        LIMIT %s
    """

    minimal_sql = """
        SELECT
            e.last_modified,
            e.exam_date,
            e.paper AS paper_id,
            NULL AS paper_name,
            e.results AS mark,
            e.exam_grade AS grade_id,
            NULL AS grade_name,
            e.exam_comment
        FROM hippo_person_exam e
        JOIN hippo_person_instance i ON i.id = e.parent
        WHERE i.parent = %s
        ORDER BY e.last_modified DESC
        LIMIT %s
    """

    try:
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(rich_sql, [person_id, limit])
            rows = _dictfetchall(cursor)
    except (ProgrammingError, OperationalError):
        with connections['dit_legacy'].cursor() as cursor:
            cursor.execute(minimal_sql, [person_id, limit])
            rows = _dictfetchall(cursor)

    out = []
    for r in rows:
        paper_label = r.get('paper_name') or r.get('paper_id')
        grade_label = r.get('grade_name') or r.get('grade_id')
        out.append({
            'source_table': 'hippo_person_exam',
            'last_modified': r.get('last_modified'),
            'registration_number': None,
            'actual_date': r.get('exam_date'),
            'level': None,
            'location': None,
            'training_provider': None,
            'district': None,
            'training_classification': None,
            'module_assessed': None,
            'second_module_assessed': None,
            'papers': [
                {
                    'paper': paper_label,
                    'results': r.get('mark'),
                    'grade': grade_label,
                    'comment': r.get('exam_comment'),
                }
            ],
            'result_type': 'exam',
        })

    return out


@api_view(['GET'])
def person_results(request, person_id: str):
    limit = request.query_params.get('limit')
    try:
        limit = max(1, min(int(limit), 500)) if limit else 200
    except ValueError:
        limit = 200

    results = []

    # Primary fallback: hippo_person_exam is heavily populated in the sample and links to person via hippo_person_instance.
    try:
        results.extend(_fetch_hippo_exams(person_id, limit=limit))
    except (ProgrammingError, OperationalError):
        pass

    # Secondary (optional) sources: zebra_marksheet_* tables, if present.
    tables = [
        ('zebra_marksheet_modular', 'modular'),
        ('zebra_marksheet_multiple', 'multiple'),
        ('zebra_marksheet_practical', 'practical'),
        ('zebra_marksheet_theory_and_practical', 'theory_and_practical'),
    ]

    for table, result_type in tables:
        rows = _fetch_marksheet(table, person_id, limit=limit)
        for r in rows:
            r['result_type'] = result_type
        results.extend(rows)

    results.sort(key=lambda x: x.get('last_modified') or '', reverse=True)

    return Response({'person_id': person_id, 'results': results, 'count': len(results)})
