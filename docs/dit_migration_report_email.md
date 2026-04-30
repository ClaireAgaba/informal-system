**Subject: DIT Legacy Data Migration — Status Report, Findings & Recommendations**

---

Dear Team,

I am writing to provide a comprehensive status report on the DIT (Directorate of Industrial Training) legacy data migration exercise. This report covers the work completed, key findings, data corrections applied, and recommendations for the way forward.

---

## 1. Background

The DIT assessment and certification data historically resided across two separate systems:

- **Old PHP System** — A web-based application that stored candidate biographical data, passport photos, and detailed exam results (paper-level marks, grades, and comments). Candidates were identified by an internal `person_id`.
- **MySQL Registration Database** — A separate MySQL database containing candidate registration records, institution details, courses, and certificate numbers. Candidates are identified by `student_id`.

These two systems had overlapping candidate records but no direct link between them. The migration objective was to unify this data into a single accessible platform within the new EMIS Informal system, ensuring that candidate profiles display complete information — including photos and exam results — regardless of which legacy system originally held the data.

---

## 2. Data Volumes

| Dataset | Count |
|---|---|
| Total candidates (MySQL database) | **579,766** |
| Candidates with certificate numbers assigned | 461,845 |
| Training providers/institutions | 6,411 |
| Assessment registrations | 46,251 |
| Courses/Occupations | 313 |
| Districts represented | 341 |
| Candidate records in old PHP system (biodata) | **238,145** |
| Passport photos extracted from old system | **220,596** |
| Detailed exam result rows extracted | **318,810** |
| Unique candidates with exam results | 236,971 |
| Total extracted data backed up on server | **1.1 GB** (of which 888 MB are photos) |

---

## 3. Work Completed

### 3.1 Data Extraction from Old PHP System

We developed automated extraction scripts to systematically crawl the old PHP system and extract:

- **Biographical data** (name, date of birth, gender, registration numbers) for all 238,145 candidates, saved as `biodata.csv`.
- **Passport photos** for 220,596 candidates, saved as individual JPEG files identified by the old `person_id`.
- **Detailed exam results** — 318,810 rows covering paper names, marks, grades, and examiner comments for 236,971 candidates, saved as `results.csv`.

All extracted data is stored as a **permanent backup** on our server at `/home/deploy/informal-system/backend/scripts/dit_extract_data/`, ensuring we retain an independent copy of the old system's data.

### 3.2 Cross-System Identity Mapping

Since the two systems use different ID spaces (`person_id` vs `student_id`) with no shared key, we built an automated mapping process that links records across systems using multiple matching strategies, applied in priority order:

1. **Registration/NSIN number match** — Exact match on the candidate's registration number (NSIN). This was the strongest and most reliable link. *Matched: 210,857 candidates.*
2. **Certificate number match** — Matching the certificate number from the MySQL database against certificate numbers recorded in the extracted exam results. *Matched: 16,485 additional candidates.*
3. **Name + Date of Birth match** — Matching on surname, first name, and date of birth. *Matched: 16,899 additional candidates.*
4. **Full name match (three names)** — Matching on surname, first name, and other name. *Matched: 624 additional candidates.*
5. **Name pair match (unique only)** — Matching on surname and first name, accepted only where the combination uniquely identifies one candidate in the old system. *Matched: 33,287 additional candidates.*

**Total mapped: 278,152 out of 579,766 MySQL candidates (48%)** now have a verified link to their old system record, enabling photo and exam result retrieval.

### 3.3 System Integration

The new EMIS Informal platform now serves unified candidate profiles that combine:

- Registration and biographical data from the MySQL database
- Passport photos served via the cross-system mapping (photo displays automatically if a mapping exists)
- Detailed exam results (paper-level marks and grades) from the extracted CSV data
- Full search capability across both datasets with filtering by name, registration number, district, training provider, and completion status

---

## 4. SQL Dump Verification

Before finalising this report, we conducted a thorough integrity audit of the MySQL database dump received from DIT, cross-referencing it against the live DIT eRegistration dashboard.

### 4.1 Dashboard Cross-Check

| Metric | Live Dashboard | Our Database | Match |
|---|---|---|---|
| Occupations | 313 | 313 | ✅ |
| Total Assessment Centers | 6,411 | 6,411 | ✅ |
| Vocational Centers | 2,299 | 2,299 | ✅ |
| Secondary Schools | 3,527 | 3,527 | ✅ |
| Primary Schools | 18 | 18 | ✅ |
| Incomplete Registrations | 9,192 | 9,191 | ✅ (off by 1) |

The SQL dump matches the live dashboard across all key metrics. The candidate and institution master data appears to be a complete dump.

### 4.2 Data Completeness — Students Table

| Field | Records with Data | Missing | % Complete |
|---|---|---|---|
| First name | 579,733 | 33 | 99.99% |
| Surname | 579,764 | 2 | 99.99% |
| Date of birth | 579,238 | 528 | 99.91% |
| Gender | 579,763 | 3 | 99.99% |
| NSIN (registration number) | 461,957 | 117,809 | 79.7% |
| Certificate number | 461,845 | 117,921 | 79.7% |
| District | 579,737 | 29 | 99.99% |
| NIN (national ID) | 19,252 | 560,514 | 3.3% |
| Phone number | 165,393 | 414,373 | 28.5% |
| Email | 5,140 | 574,626 | 0.9% |

Core biographical data (name, DOB, gender, district) is near-complete. However, **117,809 candidates (20%) have no NSIN**, and contact information capture rates are very low — reflecting that these fields were not mandatory in the old system.

### 4.3 Empty Results Tables — Critical Gap in the SQL Dump

The following tables, which should contain detailed exam results (marks and grades per paper), are **completely empty** in the SQL dump:

| Table | Expected Content | Rows |
|---|---|---|
| result_bks | Result book metadata | **0** |
| result_books | Result books | **0** |
| student_paper_registration | Paper-level exam registrations | **0** |

**This is the most significant finding.** The SQL dump provided to us contains **no exam results data at all**. All 318,810 rows of exam results currently available in the system were obtained only because we independently extracted them from the old PHP web application. Without that separate extraction, we would have candidate records with no exam results.

### 4.4 Registration Coverage Gap

The registrations table only contains records from **2020 onwards** (46,251 registrations), despite the students table containing 579,766 candidates — many of whom would have been registered before 2020. Historical registration records (pre-2020) are not present in the SQL dump.

| Year | Registrations |
|---|---|
| 2020 | 319 |
| 2021 | 3,637 |
| 2022 | 8,447 |
| 2023 | 19,376 |
| 2024 | 12,113 |
| 2025 | 2,351 |
| 2026 | 2 |

---

## 5. Data Quality Issues

### 5.1 Duplicate NSIN Numbers — ⚠️ Serious

**9,274 unique NSIN values are shared by 21,938 student records** — these are different people who have been assigned the same registration number. For example, NSIN `MAC/6018/254/CF/05/24/001` is assigned to 11 completely different candidates (different names, different certificate numbers). This indicates a systematic issue in the registration number assignment process that needs to be addressed at source.

### 5.2 Duplicate Certificate Numbers — ⚠️ Serious

**7,675 unique certificate numbers are shared by 15,716 student records.** Multiple candidates have been assigned the same certificate number. This undermines the integrity of certificate verification.

### 5.3 Certificate Number ≠ Completion (Critical Finding)

**Finding:** The old registration system automatically assigned certificate numbers (`certificate_no`) to candidates at the point of registration, **not** upon successful completion of assessment. This meant that **461,845 candidates** appeared to have "Completed" status when filtered by certificate number.

**Reality:** Only **254,856 candidates** (44% of total) actually have verified exam results with marks and grades recorded.

**Correction applied:** We updated the status determination logic across the system:
- **Before:** Status was derived from the presence of a certificate number → "Completed" if certificate_no exists.
- **After:** Status is derived from the presence of actual exam results (marks/grades) → "Completed" only if the candidate has recorded exam marks.
- A dedicated `students_with_results` table was created and populated to enable efficient filtering at the database level.

**Impact:** **206,989 candidates** were corrected from "Completed" back to "In Progress", reflecting their true assessment status.

### 5.4 Orphan Records

| Issue | Count |
|---|---|
| Students with zero registration links | 4,317 |
| Student-registration rows pointing to missing registration | 385 |
| Registrations with zero student links | 1,463 |
| Registrations pointing to missing institution | 183 |
| Registrations pointing to missing course | 46 |

These are relatively minor compared to the 580K total but indicate referential integrity gaps in the source database.

---

## 6. Migration Outcomes

### 6.1 Unmapped Candidates

Of the 579,766 candidates in MySQL, **301,614 (52%)** could not be mapped to the old PHP system. This falls into two categories:

- Candidates who were registered only in MySQL and never existed in the old system (majority)
- Candidates who exist in both systems but could not be matched due to name discrepancies, missing registration numbers, or data entry inconsistencies

For these candidates, no passport photo or detailed exam results from the old system are available. Photos can be uploaded manually through the candidate detail page.

### 6.2 Candidates with Results but No Photo

Some mapped candidates (approximately 17,556) have exam results but no passport photo on file in the old system. The photo was either never captured or was lost.

---

## 7. Recommendations

1. **Request a complete SQL dump with results data** — The current dump is missing all exam results tables. DIT should clarify whether these tables were intentionally excluded, were empty in the source system, or were accidentally omitted. If results data exists in the registration database, a supplementary dump should be provided.

2. **Resolve duplicate NSIN numbers** — The 9,274 duplicate NSINs affecting 21,938 candidates need to be corrected at source. Each candidate must have a unique registration number. This should be a prerequisite before any further certificate issuance.

3. **Resolve duplicate certificate numbers** — The 7,675 duplicate certificate numbers affecting 15,716 records similarly need correction. Duplicate certificate numbers compromise the authenticity of issued certificates.

4. **Result verification for "In Progress" candidates** — The 206,989 candidates corrected to "In Progress" should be reviewed to determine:
   - Which candidates actually completed assessment but their results were never entered
   - Which candidates genuinely did not complete their assessment
   - Whether any paper-based result records exist that should be digitised

5. **Data cleanup for unmapped candidates** — A focused exercise to manually review and link high-priority unmapped candidates (e.g., those with recent registrations or pending certificate collection) could recover additional matches.

6. **Photo capture campaign** — For candidates without photos, institutions could be tasked with collecting and uploading current passport photos through the system's upload functionality.

7. **Periodic re-run of mapping** — As data quality improves (e.g., registration numbers are corrected, names are standardised), the mapping script should be re-run to capture additional matches. The process is automated and takes approximately 30 seconds to execute.

8. **Old system decommissioning** — With all critical data now extracted and backed up on our server (biodata, photos, and exam results totalling 1.1 GB), the old PHP system can be considered for decommissioning once stakeholders confirm the migrated data is complete and accurate.

---

## 8. Way Forward

| Action | Priority | Timeline |
|---|---|---|
| Clarify missing results tables with DIT / request supplementary dump | **High** | Immediate |
| DIT to address duplicate NSIN and certificate number issues | **High** | Immediate |
| Stakeholder review of corrected completion statuses | High | Immediate |
| Identify and resolve high-priority unmapped candidates | Medium | 2–4 weeks |
| Photo upload campaign through training providers | Medium | Ongoing |
| Verify and digitise any missing paper-based results | Medium | 4–8 weeks |
| Final data reconciliation and sign-off | High | Upon completion of above |
| Old system decommissioning decision | Low | After sign-off |

---

## 9. Summary

We have successfully extracted and unified data from two independent legacy systems into a single platform. The migration covered **579,766 candidates**, with **278,152 (48%)** fully linked across systems, **220,596 passport photos** preserved, and **318,810 exam result records** made accessible. All legacy data is independently backed up on our server (1.1 GB).

A thorough audit of the SQL dump confirmed that the candidate and institution master data is complete and matches the live dashboard. However, the audit also revealed:

- **Exam results tables are empty** in the SQL dump — all results data was obtained solely through our independent extraction from the old PHP system
- **9,274 duplicate NSIN numbers** affecting 21,938 candidate records
- **7,675 duplicate certificate numbers** affecting 15,716 records
- **206,989 candidates** incorrectly showing as "Completed" have been corrected to "In Progress" after discovering that certificate numbers were auto-assigned at registration, not upon completion

The system is now live and serving unified candidate profiles with search, filtering, photo display, and exam result viewing capabilities. The above data quality issues require attention from DIT before the migration can be considered fully reconciled.

Please do not hesitate to reach out if you need any clarification or further details on any aspect of this report.

Kind regards
