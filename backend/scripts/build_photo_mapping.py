"""
Build a mapping from MySQL student_id → old PHP person_id for photo lookups.
Matches via name + date_of_birth from biodata.csv against MySQL students table.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/build_photo_mapping.py

Outputs: scripts/dit_extract_data/photo_mapping.json
    { "student_id": "old_person_id", ... }
"""
import csv
import json
import os
import sys
from pathlib import Path

# Django setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')

import django
django.setup()

from django.db import connections

DATA_DIR = Path(__file__).resolve().parent / 'dit_extract_data'
BIODATA_FILE = DATA_DIR / 'biodata.csv'
OUTPUT_FILE = DATA_DIR / 'photo_mapping.json'


def normalize(s):
    """Normalize a string for matching."""
    return (s or '').strip().lower()


def build_mapping():
    # Step 1: Load biodata.csv → old_person_id keyed by (surname, firstname, dob)
    print("Loading biodata.csv...")
    old_by_name = {}  # (surname_lower, firstname_lower, dob) → old_person_id
    old_by_id = {}    # old_person_id → (surname, firstname, dob)
    with open(BIODATA_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get('person_id', '').strip()
            if not pid:
                continue
            surname = normalize(row.get('surname', ''))
            firstname = normalize(row.get('firstname', ''))
            dob = normalize(row.get('date_of_birth', ''))
            old_by_id[pid] = (surname, firstname, dob)
            # Key by name+dob for matching
            if surname or firstname:
                key = (surname, firstname, dob)
                if key not in old_by_name:
                    old_by_name[key] = pid
                # Also try with just surname+firstname (no dob) as fallback
    print(f"  Loaded {len(old_by_id)} old person records")

    # Step 2: Query MySQL students table in batches
    print("Querying MySQL students table...")
    mapping = {}  # student_id → old_person_id
    batch_size = 5000
    offset = 0
    matched = 0
    total = 0

    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        print(f"  Total students in MySQL: {total_students}")

        while offset < total_students:
            cursor.execute("""
                SELECT student_id,
                       LOWER(COALESCE(surname, '')),
                       LOWER(COALESCE(firstname, '')),
                       COALESCE(dob, '')
                FROM students
                ORDER BY student_id
                LIMIT %s OFFSET %s
            """, [batch_size, offset])

            for student_id, surname, firstname, dob in cursor.fetchall():
                total += 1
                surname = surname.strip()
                firstname = firstname.strip()
                dob_str = str(dob).strip() if dob else ''

                # Try exact match with dob
                key = (surname, firstname, dob_str)
                if key in old_by_name:
                    mapping[str(student_id)] = old_by_name[key]
                    matched += 1
                    continue

                # Try without dob
                key_no_dob = (surname, firstname, '')
                if key_no_dob in old_by_name:
                    mapping[str(student_id)] = old_by_name[key_no_dob]
                    matched += 1

            offset += batch_size
            if offset % 50000 == 0:
                print(f"  Processed {offset}/{total_students} ({matched} matched)")

    print(f"\nDone! Matched {matched}/{total} students ({matched*100//max(total,1)}%)")

    # Save mapping
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(mapping, f)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    build_mapping()
