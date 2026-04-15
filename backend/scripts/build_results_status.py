"""
Build a MySQL table `students_with_results` for efficient status filtering.
A student is 'Completed' ONLY if they have actual exam results (marks) in
the extracted results.csv.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/build_results_status.py

This creates/updates the table `students_with_results` in dit_legacy DB.
"""
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')

import django
django.setup()

from django.db import connections

DATA_DIR = Path(__file__).resolve().parent / 'dit_extract_data'
RESULTS_FILE = DATA_DIR / 'results.csv'
MAPPING_FILE = DATA_DIR / 'photo_mapping.json'


def build_results_status():
    # Step 1: Load photo_mapping (student_id → old_person_id) and build reverse
    print("Loading photo_mapping.json...")
    mapping = json.load(open(MAPPING_FILE))
    reverse = defaultdict(list)  # old_person_id → [student_ids]
    for sid, old_pid in mapping.items():
        reverse[str(old_pid)].append(str(sid))
    print(f"  {len(mapping)} mappings, {len(reverse)} unique old person_ids")

    # Step 2: Find all old_person_ids that have actual results (marks) in results.csv
    print("Scanning results.csv for person_ids with marks...")
    pids_with_marks = set()
    with open(RESULTS_FILE) as f:
        for row in csv.DictReader(f):
            mark = (row.get('exam_mark', '') or '').strip()
            grade = (row.get('exam_grade', '') or '').strip()
            result = (row.get('exam_results', '') or '').strip()
            if mark or grade or result:
                pid = row.get('person_id', '').strip()
                if pid:
                    pids_with_marks.add(pid)
    print(f"  {len(pids_with_marks)} old person_ids have exam marks")

    # Step 3: Map to student_ids
    student_ids_with_results = set()
    for pid in pids_with_marks:
        for sid in reverse.get(pid, []):
            student_ids_with_results.add(int(sid))
    print(f"  {len(student_ids_with_results)} MySQL student_ids have results")

    # Step 4: Create/populate MySQL table
    print("Creating students_with_results table...")
    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS students_with_results")
        cursor.execute("""
            CREATE TABLE students_with_results (
                student_id INT PRIMARY KEY
            ) ENGINE=InnoDB
        """)

        # Batch insert
        batch_size = 5000
        ids_list = sorted(student_ids_with_results)
        for i in range(0, len(ids_list), batch_size):
            batch = ids_list[i:i + batch_size]
            placeholders = ','.join(['(%s)'] * len(batch))
            cursor.execute(
                f"INSERT INTO students_with_results (student_id) VALUES {placeholders}",
                batch,
            )
            if (i + batch_size) % 50000 == 0:
                print(f"  Inserted {min(i + batch_size, len(ids_list))}/{len(ids_list)}")

    print(f"\nDone! {len(student_ids_with_results)} student_ids in students_with_results table")

    # Verify
    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM students_with_results")
        count = cursor.fetchone()[0]
        print(f"Verification: {count} rows in table")


if __name__ == '__main__':
    build_results_status()
