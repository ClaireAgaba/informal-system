"""
Thorough integrity audit of the DIT legacy MySQL database.
Checks for missing data, orphan records, and cross-references with dashboard.
"""
import os, sys, builtins
from pathlib import Path

# Force unbuffered print
_orig_print = builtins.print
def print(*args, **kwargs):
    kwargs['flush'] = True
    _orig_print(*args, **kwargs)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')

import django
django.setup()

from django.db import connections


def run():
    cur = connections['dit_legacy'].cursor()

    print("=" * 60)
    print("DIT LEGACY DATABASE INTEGRITY AUDIT")
    print("=" * 60)

    # ── STUDENTS ──
    print("\n── STUDENTS TABLE ──")
    cur.execute("SELECT COUNT(*) FROM students")
    total = cur.fetchone()[0]
    print(f"Total students: {total:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE (firstname IS NULL OR firstname = '') AND (surname IS NULL OR surname = '')")
    print(f"  No name (first+surname blank): {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE firstname IS NULL OR firstname = ''")
    print(f"  No firstname: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE surname IS NULL OR surname = ''")
    print(f"  No surname: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE dob IS NULL OR dob = '' OR dob = '0000-00-00'")
    print(f"  No date of birth: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE (nsin IS NULL OR nsin = '')")
    print(f"  No NSIN: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE gender IS NULL OR gender = ''")
    print(f"  No gender: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE certificate_no IS NOT NULL AND certificate_no != ''")
    print(f"  Has certificate_no: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE district_id IS NULL OR district_id = 0")
    print(f"  No district: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE nin IS NOT NULL AND nin != ''")
    print(f"  Has NIN: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE telephone IS NOT NULL AND telephone != ''")
    print(f"  Has phone: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM students WHERE email IS NOT NULL AND email != ''")
    print(f"  Has email: {cur.fetchone()[0]:,}")

    # Duplicate NSINs
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT nsin, COUNT(*) c FROM students
            WHERE nsin IS NOT NULL AND nsin != ''
            GROUP BY nsin HAVING c > 1
        ) t
    """)
    dup_nsin = cur.fetchone()[0]
    cur.execute("""
        SELECT SUM(c) FROM (
            SELECT nsin, COUNT(*) c FROM students
            WHERE nsin IS NOT NULL AND nsin != ''
            GROUP BY nsin HAVING c > 1
        ) t
    """)
    dup_nsin_rows = cur.fetchone()[0] or 0
    print(f"  Duplicate NSINs: {dup_nsin:,} unique values affecting {dup_nsin_rows:,} rows")

    # Duplicate certificate numbers
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT certificate_no, COUNT(*) c FROM students
            WHERE certificate_no IS NOT NULL AND certificate_no != ''
            GROUP BY certificate_no HAVING c > 1
        ) t
    """)
    dup_cert = cur.fetchone()[0]
    cur.execute("""
        SELECT SUM(c) FROM (
            SELECT certificate_no, COUNT(*) c FROM students
            WHERE certificate_no IS NOT NULL AND certificate_no != ''
            GROUP BY certificate_no HAVING c > 1
        ) t
    """)
    dup_cert_rows = cur.fetchone()[0] or 0
    print(f"  Duplicate certificate_nos: {dup_cert:,} unique values affecting {dup_cert_rows:,} rows")

    # ── REGISTRATION LINKAGE ──
    print("\n── REGISTRATION LINKAGE ──")
    cur.execute("SELECT COUNT(*) FROM students_registration")
    sr = cur.fetchone()[0]
    print(f"students_registration rows: {sr:,}")

    cur.execute("SELECT COUNT(DISTINCT student_id) FROM students_registration")
    print(f"  Unique students with registrations: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(*) FROM students s
        LEFT JOIN students_registration sr ON sr.student_id = s.student_id
        WHERE sr.student_registration_id IS NULL
    """)
    print(f"  Students with ZERO registrations: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM registrations")
    print(f"registrations rows: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(*) FROM students_registration sr
        LEFT JOIN registrations r ON r.registration_id = sr.registration_id
        WHERE r.registration_id IS NULL
    """)
    print(f"  student_registrations pointing to MISSING registration: {cur.fetchone()[0]:,}")

    # Registrations with no students
    cur.execute("""
        SELECT COUNT(*) FROM registrations r
        LEFT JOIN students_registration sr ON sr.registration_id = r.registration_id
        WHERE sr.student_registration_id IS NULL
    """)
    print(f"  Registrations with ZERO students: {cur.fetchone()[0]:,}")

    # ── INSTITUTIONS ──
    print("\n── INSTITUTIONS ──")
    cur.execute("SELECT COUNT(*) FROM institutions")
    print(f"Total institutions: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(*) FROM registrations r
        LEFT JOIN institutions i ON i.institution_id = r.institution_id
        WHERE i.institution_id IS NULL
    """)
    print(f"  Registrations pointing to MISSING institution: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(*) FROM institutions i
        LEFT JOIN registrations r ON r.institution_id = i.institution_id
        WHERE r.registration_id IS NULL
    """)
    print(f"  Institutions with ZERO registrations: {cur.fetchone()[0]:,}")

    # Institution category breakdown
    cur.execute("""
        SELECT ic.centre_category, COUNT(*) 
        FROM institutions ic
        WHERE ic.centre_category IS NOT NULL AND ic.centre_category != ''
        GROUP BY ic.centre_category
        ORDER BY COUNT(*) DESC
    """)
    print("  Institution categories:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]:,}")

    # ── COURSES ──
    print("\n── COURSES ──")
    cur.execute("SELECT COUNT(*) FROM courses")
    print(f"Total courses: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(*) FROM registrations r
        LEFT JOIN courses c ON c.course_id = r.course_id
        WHERE r.course_id IS NOT NULL AND r.course_id > 0 AND c.course_id IS NULL
    """)
    print(f"  Registrations pointing to MISSING course: {cur.fetchone()[0]:,}")

    # ── DISTRICTS ──
    print("\n── DISTRICTS ──")
    cur.execute("SELECT COUNT(*) FROM districts")
    print(f"Total districts: {cur.fetchone()[0]:,}")

    cur.execute("""
        SELECT COUNT(DISTINCT s.district_id) FROM students s
        LEFT JOIN districts d ON d.district_id = s.district_id
        WHERE s.district_id > 0 AND d.district_id IS NULL
    """)
    print(f"  Student district_ids missing from districts table: {cur.fetchone()[0]:,}")

    # ── EMPTY TABLES (potential missing data) ──
    print("\n── EMPTY/SUSPICIOUS TABLES ──")
    cur.execute("SELECT COUNT(*) FROM result_bks")
    print(f"result_bks (result books): {cur.fetchone()[0]:,}  ⚠️")
    cur.execute("SELECT COUNT(*) FROM result_books")
    print(f"result_books: {cur.fetchone()[0]:,}  ⚠️")
    cur.execute("SELECT COUNT(*) FROM student_paper_registration")
    print(f"student_paper_registration: {cur.fetchone()[0]:,}  ⚠️")
    cur.execute("SELECT COUNT(*) FROM payment_docment_approval")
    print(f"payment_docment_approval: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM search_Stu")
    print(f"search_Stu: {cur.fetchone()[0]:,}")

    # ── DASHBOARD CROSS-CHECK ──
    print("\n── DASHBOARD CROSS-CHECK (vs live system screenshot) ──")
    print("  Expected from dashboard:")
    print("    Occupations: 313")
    print("    Assessment Centers: 6,411")
    print("    Vocational Centers: 2,299")
    print("    Secondary Schools: 3,527")
    print("    Primary Schools: 18")
    print("    Incomplete Registrations: 9,192")

    cur.execute("SELECT COUNT(*) FROM courses")
    db_courses = cur.fetchone()[0]
    print(f"\n  DB courses: {db_courses:,} {'✓' if db_courses == 313 else '✗ MISMATCH'}")

    cur.execute("SELECT COUNT(*) FROM institutions")
    db_inst = cur.fetchone()[0]
    print(f"  DB institutions: {db_inst:,} {'✓' if db_inst == 6411 else '✗ MISMATCH'}")

    # Check institution categories for dashboard counts
    cur.execute("SELECT centre_category, COUNT(*) FROM institutions GROUP BY centre_category")
    cats = {str(r[0]).strip().lower(): r[1] for r in cur.fetchall()}
    print(f"  Institution categories in DB: {cats}")

    # Incomplete registrations check
    cur.execute("SELECT COUNT(*) FROM registrations WHERE completed = 0 OR completed IS NULL")
    incomplete = cur.fetchone()[0]
    print(f"  Incomplete registrations (completed=0/NULL): {incomplete:,} (dashboard says 9,192)")

    # Invoices
    cur.execute("SELECT COUNT(*) FROM invoices")
    print(f"  Total invoices: {cur.fetchone()[0]:,}")

    # ── MARK SHEETS ──
    print("\n── MARK SHEETS & RESULTS ──")
    cur.execute("SELECT COUNT(*) FROM mark_sheets")
    print(f"mark_sheets rows: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM certificate_printed")
    print(f"certificate_printed rows: {cur.fetchone()[0]:,}")

    # ── ACADEMIC DOCUMENTS ──
    print("\n── ACADEMIC DOCUMENTS ──")
    cur.execute("SELECT COUNT(*) FROM academic_documents")
    print(f"academic_documents rows: {cur.fetchone()[0]:,}")

    # ── USERS ──
    print("\n── USERS ──")
    cur.execute("SELECT COUNT(*) FROM users")
    print(f"Total users: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM user_log")
    print(f"User log entries: {cur.fetchone()[0]:,}")

    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    run()
