"""
DIT Legacy Data Extractor
=========================
Extracts candidate biodata, photos, and results from the old DIT PHP system
at http://216.104.197.69/dit_train/

Usage:
    python scripts/dit_extractor.py --phase collect_ids
    python scripts/dit_extractor.py --phase extract_data
    python scripts/dit_extractor.py --phase download_photos
    python scripts/dit_extractor.py --phase all

The script saves progress and can be resumed if interrupted.
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

# ── Configuration ──
BASE_URL = "http://216.104.197.69/dit_train/index.php"
USERNAME = "sbabirye"
PASSWORD = "333"

# Directories
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "dit_extract_data"
PHOTOS_DIR = DATA_DIR / "photos"
PROGRESS_FILE = DATA_DIR / "progress.json"
PERSON_IDS_FILE = DATA_DIR / "person_ids.csv"
BIODATA_FILE = DATA_DIR / "biodata.csv"
RESULTS_FILE = DATA_DIR / "results.csv"

# Rate limiting
REQUEST_DELAY = 0.15  # seconds between requests
MAX_RETRIES = 3
TIMEOUT = 30

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DATA_DIR / "extractor.log" if (DATA_DIR).exists() else "/tmp/dit_extractor.log"),
    ],
)
log = logging.getLogger(__name__)


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    # Re-add file handler now that dir exists
    for h in log.handlers:
        if isinstance(h, logging.FileHandler):
            log.removeHandler(h)
    log.addHandler(logging.FileHandler(DATA_DIR / "extractor.log"))


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {
        "collect_ids_page": 0,
        "collect_ids_done": False,
        "extract_data_index": 0,
        "extract_data_done": False,
        "download_photos_index": 0,
        "download_photos_done": False,
    }


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def create_session():
    """Login and return authenticated session."""
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (compatible; DIT-Extractor/1.0)"})
    r = s.post(f"{BASE_URL}/login", data={"username": USERNAME, "password": PASSWORD}, timeout=TIMEOUT)
    if "Log out" not in r.text:
        raise RuntimeError("Login failed!")
    log.info("Logged in successfully")
    return s


def safe_request(session, url, params=None, retries=MAX_RETRIES):
    """Make a request with retries and rate limiting."""
    for attempt in range(retries):
        try:
            time.sleep(REQUEST_DELAY)
            r = session.get(url, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r
            log.warning(f"Status {r.status_code} for {url} (attempt {attempt + 1})")
        except requests.RequestException as e:
            log.warning(f"Request error: {e} (attempt {attempt + 1})")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


# ──────────────────────────────────────────────────
# Phase 1: Collect person IDs from search pages
# ──────────────────────────────────────────────────
def collect_person_ids(session, progress):
    """Iterate through search result pages and collect all person_ids."""
    log.info("=== Phase 1: Collecting person IDs ===")

    if progress.get("collect_ids_done"):
        log.info("Already completed. Skipping.")
        return

    start_page = progress.get("collect_ids_page", 0) + 1
    total_pages = 4888  # Known from exploration

    # Open CSV in append mode
    file_exists = PERSON_IDS_FILE.exists()
    with open(PERSON_IDS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["person_id", "surname", "firstname", "othername", "gender",
                             "reg_number", "assessment_centre", "location", "occupation",
                             "level", "actual_assessment_date"])

        for page in range(start_page, total_pages + 1):
            r = safe_request(
                session,
                f"{BASE_URL}/CustomReports/show/search_people/Search",
                params={"limit_page": page},
            )
            if not r:
                log.error(f"Failed to fetch page {page} after retries. Stopping.")
                break

            soup = BeautifulSoup(r.text, "html.parser")

            # Re-login if session expired
            if "Log In" in (soup.find("title") or soup).get_text() and "Log out" not in r.text:
                log.warning("Session expired, re-logging in...")
                session = create_session()
                r = safe_request(
                    session,
                    f"{BASE_URL}/CustomReports/show/search_people/Search",
                    params={"limit_page": page},
                )
                if not r:
                    break
                soup = BeautifulSoup(r.text, "html.parser")

            # Parse table rows
            tables = soup.find_all("table")
            if not tables:
                log.warning(f"No tables on page {page}")
                continue

            main_table = tables[0]
            rows = main_table.find_all("tr")[1:]  # Skip header

            count = 0
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 6:
                    continue

                # Extract person_id from link
                link = row.find("a", href=re.compile(r"person"))
                if not link:
                    continue
                href = link.get("href", "")
                pid_match = re.search(r"person[%|]7C(\d+)", href) or re.search(r"person\|(\d+)", href)
                if not pid_match:
                    continue
                person_id = pid_match.group(1)

                # Extract table data
                cell_texts = [c.get_text(strip=True) for c in cells]
                # Columns: #, RegNumber, Surname, FirstName, OtherNames, Gender,
                #          AssessmentCentre, Location, AssessmentCentre2, Occupation, Level, ActualDate
                row_data = [person_id] + cell_texts[1:11] if len(cell_texts) >= 11 else [person_id] + cell_texts[1:]

                writer.writerow(row_data)
                count += 1

            progress["collect_ids_page"] = page
            save_progress(progress)

            if page % 50 == 0:
                log.info(f"Page {page}/{total_pages} - collected {count} IDs from this page")
                f.flush()

    progress["collect_ids_done"] = True
    save_progress(progress)

    # Count total collected
    if PERSON_IDS_FILE.exists():
        with open(PERSON_IDS_FILE) as f:
            total = sum(1 for _ in f) - 1  # minus header
        log.info(f"Phase 1 complete: {total} person IDs collected")


# ──────────────────────────────────────────────────
# Phase 2: Extract detailed biodata + photo IDs
# ──────────────────────────────────────────────────
def extract_person_data(session, person_id):
    """Extract biodata and photo_id from a person's detail page."""
    r = safe_request(session, f"{BASE_URL}/view", params={"id": f"person|{person_id}"})
    if not r:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    data = {"person_id": person_id, "photo_id": None}

    # Extract photo_id from img src
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "BinField" in src and "person_photo_passport" in src:
            match = re.search(r"person_photo_passport[%|]7C(\d+)", src) or re.search(
                r"person_photo_passport\|(\d+)", src
            )
            if match:
                data["photo_id"] = match.group(1)
            alt = img.get("alt", "")
            data["photo_filename"] = alt
            break

    # Extract field values using label -> value approach
    # Structure: <td><label>Surname</label>:</td><td><span class="form_field">Nababi</span></td>
    label_map = {
        "Surname": "surname",
        "First Name": "firstname",
        "Other Names": "othername",
        "Nationality": "nationality",
        "Is Candidate Disabled?": "is_disabled",
        "District of Birth": "district",
        "Home Sub County": "subcounty",
        "Home Village": "village",
        "Home Address": "home_address",
        "Date of Birth": "date_of_birth",
        "Gender": "gender",
        "Marital Status": "marital_status",
        "Identification Type": "id_type",
        "Identification Number": "id_number",
        "Assessment Centre": "assessment_centre",
        "Academic Level": "academic_level",
        "Qualification": "qualification",
        "Year Of Graduation": "year_of_graduation",
    }

    for label_tag in soup.find_all("label"):
        label_text = label_tag.get_text(strip=True)
        if label_text in label_map:
            td = label_tag.find_parent("td")
            if td:
                next_td = td.find_next_sibling("td")
                if next_td:
                    val_span = next_td.find("span", class_="form_field")
                    if val_span:
                        data[label_map[label_text]] = val_span.get_text(strip=True)

    # Extract assessment instances and exam results
    # Instances: spans with name="person_instance:*"
    # Exams: spans with name="person_exam:*"
    results = []

    # Find all person_instance divs (each contains one training instance)
    instance_divs = soup.find_all("div", id=re.compile(r"person_instance"))
    if not instance_divs:
        # Fallback: look for all instance spans
        instance_divs = [soup]

    for div in instance_divs:
        # Collect instance-level data
        instance_data = {}
        for span in div.find_all("span", class_="form_field"):
            name = span.get("name", "")
            val = span.get_text(strip=True)
            if name == "person_instance:provider_instance":
                instance_data["instance"] = val
            elif name == "person_instance:exam_number":
                instance_data["exam_number"] = val
            elif name == "person_instance:course_codes":
                instance_data["module_codes"] = val
            elif name == "person_instance:certificate_number":
                instance_data["certificate_number"] = val
            elif name == "person_instance:sponsored_by":
                instance_data["sponsored_by"] = val
            elif name == "person_instance:prefered_language":
                instance_data["language"] = val

        # Collect exam-level data (multiple per instance)
        # Each exam is in its own sub-div with person_exam fields
        exam_sections = div.find_all("span", attrs={"name": "person_exam:paper"})
        if exam_sections:
            for paper_span in exam_sections:
                exam_data = dict(instance_data)  # copy instance info
                exam_data["paper"] = paper_span.get_text(strip=True)
                # Find sibling exam fields in the same parent container
                container = paper_span.find_parent("div", class_="editRecord") or paper_span.find_parent("table") or paper_span.find_parent("div")
                if container:
                    for span in container.find_all("span", class_="form_field"):
                        name = span.get("name", "")
                        val = span.get_text(strip=True)
                        if name == "person_exam:exam_date":
                            exam_data["exam_date"] = val
                        elif name == "person_exam:results_section_a1":
                            exam_data["exam_mark"] = val
                        elif name == "person_exam:results":
                            exam_data["exam_results"] = val
                        elif name == "person_exam:exam_grade":
                            exam_data["exam_grade"] = val
                        elif name == "person_exam:exam_comment":
                            exam_data["exam_comment"] = val
                results.append(exam_data)
        elif instance_data:
            results.append(instance_data)

    # Fallback: extract all exam data as flat list from label pairs
    if not results:
        current_exam = {}
        for label_tag in soup.find_all("label"):
            text = label_tag.get_text(strip=True)
            td = label_tag.find_parent("td")
            if not td:
                continue
            next_td = td.find_next_sibling("td")
            if not next_td:
                continue
            val_span = next_td.find("span", class_="form_field")
            val = val_span.get_text(strip=True) if val_span else ""

            if text == "Instance":
                if current_exam and current_exam.get("paper"):
                    results.append(current_exam)
                current_exam = {"instance": val}
            elif text == "Exam Number":
                current_exam["exam_number"] = val
            elif text == "Assessment/Module Codes":
                current_exam["module_codes"] = val
            elif text == "Certificate Number":
                current_exam["certificate_number"] = val
            elif text == "Sponsored By":
                current_exam["sponsored_by"] = val
            elif text in ("Prefered Language", "Preferred Language"):
                current_exam["language"] = val
            elif text == "Exam Date":
                current_exam["exam_date"] = val
            elif text == "Paper":
                if current_exam.get("paper"):
                    results.append(dict(current_exam))
                current_exam["paper"] = val
                # Clear exam-specific fields for next paper
                for k in ("exam_date", "exam_mark", "exam_results", "exam_grade", "exam_comment"):
                    current_exam.pop(k, None)
            elif text == "Exam Mark":
                current_exam["exam_mark"] = val
            elif text == "Exam Results":
                current_exam["exam_results"] = val
            elif text == "Exam Grade":
                current_exam["exam_grade"] = val
            elif text == "Exam Comment":
                current_exam["exam_comment"] = val
        if current_exam and (current_exam.get("paper") or current_exam.get("instance")):
            results.append(current_exam)

    data["results"] = results
    return data


def extract_all_data(session, progress):
    """Extract biodata for all collected person IDs."""
    log.info("=== Phase 2: Extracting biodata ===")

    if progress.get("extract_data_done"):
        log.info("Already completed. Skipping.")
        return

    if not PERSON_IDS_FILE.exists():
        log.error("person_ids.csv not found. Run collect_ids first.")
        return

    # Load unique person IDs
    person_ids = set()
    with open(PERSON_IDS_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            person_ids.add(row["person_id"])
    person_ids = sorted(person_ids, key=int)
    log.info(f"Total unique person IDs: {len(person_ids)}")

    start_index = progress.get("extract_data_index", 0)

    # Open CSV files
    bio_exists = BIODATA_FILE.exists() and start_index > 0
    results_exists = RESULTS_FILE.exists() and start_index > 0

    bio_f = open(BIODATA_FILE, "a", newline="")
    res_f = open(RESULTS_FILE, "a", newline="")
    bio_writer = csv.writer(bio_f)
    res_writer = csv.writer(res_f)

    bio_fields = [
        "person_id", "photo_id", "photo_filename", "surname", "firstname", "othername",
        "nationality", "is_disabled", "district", "subcounty", "village", "home_address",
        "date_of_birth", "gender", "marital_status", "id_type", "id_number",
        "assessment_centre", "academic_level", "qualification", "year_of_graduation",
    ]
    res_fields = [
        "person_id", "instance", "exam_number", "module_codes", "certificate_number",
        "sponsored_by", "language", "exam_date", "paper", "exam_mark",
        "exam_results", "exam_grade", "exam_comment",
    ]

    if not bio_exists:
        bio_writer.writerow(bio_fields)
    if not results_exists:
        res_writer.writerow(res_fields)

    try:
        for i, pid in enumerate(person_ids[start_index:], start=start_index):
            data = extract_person_data(session, pid)
            if data is None:
                log.warning(f"Failed to extract person {pid}")
                continue

            # Write biodata
            bio_row = [data.get(f, "") for f in bio_fields]
            bio_writer.writerow(bio_row)

            # Write results
            for result in data.get("results", []):
                res_row = [pid] + [result.get(f, "") for f in res_fields[1:]]
                res_writer.writerow(res_row)

            progress["extract_data_index"] = i + 1
            if (i + 1) % 100 == 0:
                save_progress(progress)
                bio_f.flush()
                res_f.flush()
                log.info(f"Extracted {i + 1}/{len(person_ids)} candidates")

            # Re-login periodically to avoid session expiry
            if (i + 1) % 2000 == 0:
                try:
                    session = create_session()
                except Exception:
                    log.warning("Re-login failed, continuing with current session")

    except KeyboardInterrupt:
        log.info("Interrupted. Progress saved.")
    finally:
        bio_f.close()
        res_f.close()
        save_progress(progress)

    progress["extract_data_done"] = True
    save_progress(progress)
    log.info("Phase 2 complete")


# ──────────────────────────────────────────────────
# Phase 3: Download passport photos
# ──────────────────────────────────────────────────
def download_photo(session, person_id, photo_id):
    """Download a single photo and save it."""
    photo_path = PHOTOS_DIR / f"{person_id}.jpg"
    if photo_path.exists() and photo_path.stat().st_size > 0:
        return True  # Already downloaded

    r = safe_request(
        session,
        f"{BASE_URL}/BinField",
        params={"formid": f"person_photo_passport|{photo_id}", "field": "image"},
    )
    if not r or len(r.content) < 100:
        return False

    with open(photo_path, "wb") as f:
        f.write(r.content)
    return True


def download_all_photos(session, progress):
    """Download photos for all candidates with photo_ids."""
    log.info("=== Phase 3: Downloading photos ===")

    if progress.get("download_photos_done"):
        log.info("Already completed. Skipping.")
        return

    if not BIODATA_FILE.exists():
        log.error("biodata.csv not found. Run extract_data first.")
        return

    # Load person_id -> photo_id mapping
    photo_map = []
    with open(BIODATA_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("photo_id"):
                photo_map.append((row["person_id"], row["photo_id"]))

    log.info(f"Total candidates with photos: {len(photo_map)}")

    start_index = progress.get("download_photos_index", 0)
    downloaded = 0
    failed = 0

    try:
        for i, (pid, photo_id) in enumerate(photo_map[start_index:], start=start_index):
            success = download_photo(session, pid, photo_id)
            if success:
                downloaded += 1
            else:
                failed += 1

            progress["download_photos_index"] = i + 1
            if (i + 1) % 100 == 0:
                save_progress(progress)
                log.info(f"Photos: {i + 1}/{len(photo_map)} (downloaded={downloaded}, failed={failed})")

            # Re-login periodically
            if (i + 1) % 2000 == 0:
                try:
                    session = create_session()
                except Exception:
                    log.warning("Re-login failed")

    except KeyboardInterrupt:
        log.info("Interrupted. Progress saved.")
    finally:
        save_progress(progress)

    progress["download_photos_done"] = True
    save_progress(progress)
    log.info(f"Phase 3 complete: {downloaded} downloaded, {failed} failed")


# ──────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="DIT Legacy Data Extractor")
    parser.add_argument(
        "--phase",
        choices=["collect_ids", "extract_data", "download_photos", "all", "status"],
        required=True,
        help="Which phase to run",
    )
    parser.add_argument("--reset", action="store_true", help="Reset progress for the given phase")
    args = parser.parse_args()

    ensure_dirs()
    progress = load_progress()

    if args.phase == "status":
        print(json.dumps(progress, indent=2))
        if PERSON_IDS_FILE.exists():
            with open(PERSON_IDS_FILE) as f:
                total = sum(1 for _ in f) - 1
            print(f"Person IDs collected: {total}")
        if BIODATA_FILE.exists():
            with open(BIODATA_FILE) as f:
                total = sum(1 for _ in f) - 1
            print(f"Biodata extracted: {total}")
        photo_count = len(list(PHOTOS_DIR.glob("*.jpg")))
        print(f"Photos downloaded: {photo_count}")
        return

    if args.reset:
        if args.phase == "collect_ids":
            progress["collect_ids_page"] = 0
            progress["collect_ids_done"] = False
            if PERSON_IDS_FILE.exists():
                PERSON_IDS_FILE.unlink()
        elif args.phase == "extract_data":
            progress["extract_data_index"] = 0
            progress["extract_data_done"] = False
        elif args.phase == "download_photos":
            progress["download_photos_index"] = 0
            progress["download_photos_done"] = False
        save_progress(progress)
        log.info(f"Reset progress for {args.phase}")

    session = create_session()

    if args.phase in ("collect_ids", "all"):
        collect_person_ids(session, progress)

    if args.phase in ("extract_data", "all"):
        extract_all_data(session, progress)

    if args.phase in ("download_photos", "all"):
        download_all_photos(session, progress)


if __name__ == "__main__":
    main()
