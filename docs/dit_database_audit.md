# DIT Legacy Database — Integrity Audit Report

**Date:** 17 April 2026  
**Database:** dit_legacy (MySQL/MariaDB)  
**Source:** SQL dump provided from DIT eRegistration system

---

## 1. Dashboard Cross-Check

Comparison of live DIT eRegistration dashboard (http://41.186.86.12:8000) against the SQL dump we received:

| Metric | Dashboard | Our DB | Match |
|---|---|---|---|
| Occupations | 313 | 313 | ✅ |
| Total Assessment Centers | 6,411 | 6,411 | ✅ |
| Vocational Centers | 2,299 | 2,299 | ✅ |
| Secondary Schools | 3,527 | 3,527 | ✅ |
| Primary Schools | 18 | 18 | ✅ |
| Incomplete Registrations | 9,192 | 9,191 | ✅ (off by 1) |

**Conclusion:** The SQL dump matches the live dashboard figures across all key metrics. The candidate and institution master data appears to be a complete dump.

---

## 2. Data Completeness — Students Table (579,766 records)

| Field | Has Data | Missing | % Complete |
|---|---|---|---|
| First name | 579,733 | 33 | 99.99% |
| Surname | 579,764 | 2 | 99.99% |
| Both names blank | — | 1 | — |
| Date of birth | 579,238 | 528 | 99.91% |
| Gender | 579,763 | 3 | 99.99% |
| NSIN (reg number) | 461,957 | 117,809 | 79.68% |
| Certificate number | 461,845 | 117,921 | 79.66% |
| District | 579,737 | 29 | 99.99% |
| NIN (national ID) | 19,252 | 560,514 | 3.32% |
| Phone number | 165,393 | 414,373 | 28.53% |
| Email | 5,140 | 574,626 | 0.89% |

**Key observations:**
- Core biographical data (name, DOB, gender, district) is near-complete — good.
- **117,809 candidates (20%) have no NSIN** — these were registered without being assigned a registration number.
- NIN, phone, and email capture rates are very low (3%, 29%, 1% respectively), likely because these fields were not mandatory in the old system.

---

## 3. Data Quality Issues

### 3.1 Duplicate NSIN Numbers — ⚠️ SERIOUS

**9,274 unique NSIN values are shared by 21,938 student records.** These are different people assigned the same registration number.

Example — NSIN `MAC/6018/254/CF/05/24/001` is assigned to **11 different people:**

| student_id | Name | Certificate No |
|---|---|---|
| 467657 | Agaba Norman | CF 24050295 |
| 469028 | Barekye Edward | CF 24050322 |
| 470052 | Asiimwe Mary | CF 24050832 |
| 471451 | Abindabyamu Siyadora | CF 24050269 |
| 471950 | Abalozo Nathan | CF 24050715 |
| ... | *(6 more people)* | ... |

This indicates a systematic issue in the registration number assignment process.

### 3.2 Duplicate Certificate Numbers — ⚠️ SERIOUS

**7,675 unique certificate numbers are shared by 15,716 student records.** Multiple candidates have been assigned the same certificate number.

### 3.3 Certificate Number ≠ Completion

As previously reported, certificate numbers were auto-assigned at registration, not upon completion. Of 461,845 candidates with certificate numbers, only **254,856 (55%)** have actual exam results with marks.

---

## 4. Referential Integrity Issues

### 4.1 Orphan Records

| Issue | Count | Severity |
|---|---|---|
| Students with ZERO registration links | 4,317 | Medium |
| student_registration rows pointing to MISSING registration | 385 | Medium |
| Registrations with ZERO student links | 1,463 | Low |
| Registrations pointing to MISSING institution | 183 | Low |
| Registrations pointing to MISSING course | 46 | Low |
| Student district_ids not in districts table | 3 | Low |
| Institutions with ZERO registrations | 3,089 | Info |

**4,317 students** exist in the students table but have no corresponding entry in `students_registration`. These are "ghost" records with no assessment history linkage.

**385 student_registration records** point to registration IDs that don't exist in the `registrations` table — broken foreign keys.

---

## 5. CRITICAL: Empty Tables — Results Data Missing from SQL Dump

The following tables are **completely empty** (0 rows):

| Table | Expected Content | Rows |
|---|---|---|
| **result_bks** | Result book metadata | **0** |
| **result_books** | Result books | **0** |
| **student_paper_registration** | Paper-level exam registrations | **0** |
| payment_docment_approval | Payment approvals | 0 |
| search_Stu | Search cache | 0 |

**This is the most significant finding.** The `result_bks`, `result_books`, and `student_paper_registration` tables — which should contain the detailed exam results (marks, grades per paper) — were **not included in the SQL dump** or were empty in the source system.

This means the SQL dump alone provides **no exam results data**. All 318,810 rows of exam results currently in the system were obtained only because we independently extracted them from the old PHP web application.

**Without the separate extraction from the old PHP system, we would have candidate records with no exam results at all.**

---

## 6. Registration Data Coverage

### By Year
| Year | Registrations |
|---|---|
| 2020 | 319 |
| 2021 | 3,637 |
| 2022 | 8,447 |
| 2023 | 19,376 |
| 2024 | 12,113 |
| 2025 | 2,351 |
| 2026 | 2 |
| **Total** | **46,251** |

The system only has registration records from 2020 onwards. Historical registrations (pre-2020) are not in this database.

### Assessment Levels
| Level | Name |
|---|---|
| 1 | Modular |
| 2 | Workers Pas |
| 3 | Level I |
| 4 | Level II |
| 5 | Level III |
| 6 | Level IV |
| 7 | Level V |

### Other Tables Present
| Table | Rows | Notes |
|---|---|---|
| academic_documents | 163,929 | Uploaded documents |
| mark_sheets | 364 | Very few mark sheet uploads |
| certificate_printed | 6,290 | Certificates confirmed printed |
| invoices | 14,418 | Payment invoices |
| users | 5,394 | System users |
| user_log | 190,321 | Audit trail |
| institution_course | 576,608 | Institution-course mappings |

---

## 7. Summary of Concerns

### Must Address Before Report Submission
1. **Results tables are empty** — confirm whether DIT's source system also had empty tables, or if the SQL dump was incomplete.
2. **Duplicate NSINs (9,274 values, 21,938 rows)** — these are different people with identical registration numbers. Needs clarification from DIT.
3. **Duplicate certificate numbers (7,675 values, 15,716 rows)** — same certificate number assigned to multiple people. Needs clarification.

### Informational
4. Referential integrity gaps (orphan records) are relatively minor compared to the 580K total.
5. Low NIN/phone/email capture rates reflect the old system's data collection practices.
6. Registration records only cover 2020–2026 (46,251 registrations for 579,766 students).
7. 117,809 students (20%) have no NSIN at all.
