"""
Build a mapping from MySQL student_id → old PHP person_id for photo lookups.
Two databases have different ID spaces but overlapping candidates.
Matches via name + normalised DOB.

Old system DOB format: "22 January 1991"
MySQL DOB format:      "1991-01-22"

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
import re
import sys
from datetime import datetime
from pathlib import Path

# Django setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')

import django
django.setup()

from django.db import connections

DATA_DIR = Path(__file__).resolve().parent / 'dit_extract_data'
BIODATA_FILE = DATA_DIR / 'biodata.csv'
RESULTS_FILE = DATA_DIR / 'results.csv'
PHOTOS_DIR = DATA_DIR / 'photos'
OUTPUT_FILE = DATA_DIR / 'photo_mapping.json'


def norm(s):
    """Normalize a string for matching: strip, lowercase, collapse whitespace."""
    return re.sub(r'\s+', ' ', (s or '').strip().lower())


def parse_old_dob(s):
    """Parse '22 January 1991' → '1991-01-22', or return '' on failure."""
    s = (s or '').strip()
    if not s:
        return ''
    for fmt in ('%d %B %Y', '%d %b %Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ''


def norm_reg(s):
    """Normalize a registration number: strip, lowercase, remove all whitespace."""
    return re.sub(r'\s+', '', (s or '').strip().lower())


def build_mapping():
    # Step 1: Load biodata.csv indexes (ALL records, not just those with photos)
    print("Loading biodata.csv...")
    by_reg = {}        # normalized reg_number → old_person_id (best)
    by_name_dob = {}   # (surname, firstname, dob_iso) → old_person_id
    by_name3 = {}      # (surname, firstname, othername) → old_person_id
    by_name2 = {}      # (surname, firstname) → [old_person_ids]

    with open(BIODATA_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get('person_id', '').strip()
            if not pid:
                continue
            surname = norm(row.get('surname', ''))
            firstname = norm(row.get('firstname', ''))
            othername = norm(row.get('othername', ''))
            dob_raw = (row.get('date_of_birth', '') or '').strip()
            dob_iso = parse_old_dob(dob_raw)
            reg = norm_reg(row.get('id_number', ''))

            # Registration number index (strongest match)
            if reg:
                if reg not in by_reg:
                    by_reg[reg] = pid

            if not surname and not firstname:
                continue

            # Name + DOB
            if dob_iso:
                key = (surname, firstname, dob_iso)
                if key not in by_name_dob:
                    by_name_dob[key] = pid

            # Name triple
            if othername:
                key3 = (surname, firstname, othername)
                if key3 not in by_name3:
                    by_name3[key3] = pid

            # Name pair (allow duplicates)
            key2 = (surname, firstname)
            by_name2.setdefault(key2, []).append(pid)

    print(f"  Unique reg numbers: {len(by_reg)}")
    print(f"  Unique (surname,firstname,dob) keys: {len(by_name_dob)}")
    print(f"  Unique (surname,firstname,othername) keys: {len(by_name3)}")
    print(f"  Unique (surname,firstname) keys: {len(by_name2)}")

    # Step 1b: Build certificate_number → old_person_id index from results.csv
    print("Loading results.csv for certificate number index...")
    by_cert = {}  # normalized cert_number → old_person_id
    if RESULTS_FILE.is_file():
        with open(RESULTS_FILE) as f:
            for row in csv.DictReader(f):
                cert = norm_reg(row.get('certificate_number', ''))
                pid = row.get('person_id', '').strip()
                if cert and pid and cert not in by_cert:
                    by_cert[cert] = pid
    print(f"  Unique certificate numbers: {len(by_cert)}")

    # Step 2: Query MySQL students table and match
    print("Querying MySQL students table...")
    mapping = {}   # student_id → old_person_id
    batch_size = 10000
    offset = 0
    matched_reg = 0
    matched_cert = 0
    matched_dob = 0
    matched_name3 = 0
    matched_name2 = 0
    total = 0

    with connections['dit_legacy'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        print(f"  Total students in MySQL: {total_students}")

        while offset < total_students:
            cursor.execute("""
                SELECT student_id,
                       COALESCE(surname, ''),
                       COALESCE(firstname, ''),
                       COALESCE(othername, ''),
                       COALESCE(dob, ''),
                       COALESCE(nsin, ''),
                       COALESCE(certificate_no, '')
                FROM students
                ORDER BY student_id
                LIMIT %s OFFSET %s
            """, [batch_size, offset])

            for student_id, surname, firstname, othername, dob, nsin, cert_no in cursor.fetchall():
                total += 1
                sid = str(student_id)
                nsin_clean = norm_reg(nsin)
                surname = norm(surname)
                firstname = norm(firstname)
                othername = norm(othername)
                dob_str = str(dob).strip() if dob else ''
                if dob_str in ('', 'None', '0000-00-00'):
                    dob_str = ''

                cert_clean = norm_reg(cert_no)

                # Priority 0: NSIN / registration number
                if nsin_clean and nsin_clean in by_reg:
                    mapping[sid] = by_reg[nsin_clean]
                    matched_reg += 1
                    continue

                # Priority 0.5: Certificate number (from results.csv)
                if cert_clean and cert_clean in by_cert:
                    mapping[sid] = by_cert[cert_clean]
                    matched_cert += 1
                    continue

                # Priority 1: surname + firstname + DOB
                if dob_str:
                    key = (surname, firstname, dob_str)
                    if key in by_name_dob:
                        mapping[sid] = by_name_dob[key]
                        matched_dob += 1
                        continue

                # Priority 2: surname + firstname + othername
                if othername:
                    key3 = (surname, firstname, othername)
                    if key3 in by_name3:
                        mapping[sid] = by_name3[key3]
                        matched_name3 += 1
                        continue

                # Priority 3: surname + firstname (only if unique)
                key2 = (surname, firstname)
                candidates = by_name2.get(key2, [])
                if len(candidates) == 1:
                    mapping[sid] = candidates[0]
                    matched_name2 += 1

            offset += batch_size
            if offset % 50000 == 0:
                total_matched = matched_reg + matched_cert + matched_dob + matched_name3 + matched_name2
                print(f"  Processed {offset}/{total_students} ({total_matched} matched)")

    total_matched = matched_reg + matched_cert + matched_dob + matched_name3 + matched_name2
    print(f"\nDone! Matched {total_matched}/{total} students ({total_matched*100//max(total,1)}%)")
    print(f"  By NSIN/reg number: {matched_reg}")
    print(f"  By certificate number: {matched_cert}")
    print(f"  By name+DOB: {matched_dob}")
    print(f"  By name+othername: {matched_name3}")
    print(f"  By name only (unique): {matched_name2}")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(mapping, f)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    build_mapping()
