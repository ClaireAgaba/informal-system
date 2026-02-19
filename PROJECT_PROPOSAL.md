# PROJECT PROPOSAL

## UVTAB Electronic Management Information System (EMIS) – Informal Sector

---

**Prepared by:** Uganda Vocational Training and Assessment Board (UVTAB)
**Date:** February 2026
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Introduction](#2-introduction)
3. [Problem Statement](#3-problem-statement)
4. [Project Objectives](#4-project-objectives)
5. [Scope of the Project](#5-scope-of-the-project)
6. [System Features and Modules](#6-system-features-and-modules)
7. [Technical Architecture](#7-technical-architecture)
8. [Implementation Strategy](#8-implementation-strategy)
9. [Expected Outcomes and Benefits](#9-expected-outcomes-and-benefits)
10. [Risk Assessment and Mitigation](#10-risk-assessment-and-mitigation)
11. [Project Timeline](#11-project-timeline)
12. [Budget Estimate](#12-budget-estimate)
13. [Sustainability Plan](#13-sustainability-plan)
14. [Conclusion](#14-conclusion)

---

## 1. Executive Summary

The Uganda Vocational Training and Assessment Board (UVTAB) proposes the development and deployment of an **Electronic Management Information System (EMIS)** to digitize and streamline the management of candidates within the **Informal Sector** assessment programs. The system addresses the growing challenges of managing over **60,000 candidates** across multiple assessment centers nationwide using manual and fragmented processes.

The EMIS platform provides a centralized, web-based solution for candidate registration, assessment tracking, results management, transcript generation, payment processing, and awards certification. By automating these processes, the system significantly reduces administrative overhead, minimizes errors, enhances data integrity, and improves service delivery to candidates and assessment centers.

---

## 2. Introduction

### 2.1 Background

UVTAB is mandated to coordinate, regulate, and conduct assessments and award qualifications in the Business, Technical, Vocational Education and Training (BTVET) sub-sector in Uganda. The Informal Sector program specifically targets artisans and skilled workers who have acquired competencies through informal means — including apprenticeships, on-the-job training, and self-learning — and provides them a pathway to formal recognition of their skills.

The Informal Sector assessment program encompasses multiple registration categories including **Modular Assessments**, **Formal Assessments**, and **Worker's Prior Achievement Summary (PAS)** programs. Candidates are registered across numerous assessment centers throughout the country, each offering various occupational programs.

### 2.2 Existing System (EIMS) and Its Limitations

UVTAB currently operates an **Education Information Management System (EIMS)** that serves the formal education sector. However, the EIMS was designed around a **program-based structure** — where candidates are enrolled into defined academic programs with fixed curricula and progression paths.

The Informal Sector operates on a fundamentally different structure. Instead of programs, candidates are registered under **occupations** — each with its own set of modular units, competency-based assessments, and flexible completion timelines. The registration categories (Modular, Formal, Worker's PAS), assessment models, and award qualification criteria in the Informal Sector are structurally incompatible with the EIMS architecture.

Attempting to modify the existing EIMS to accommodate the Informal Sector's unique requirements would require extensive restructuring of the database schema, business logic, and user interface — introducing significant risk of destabilizing the already operational formal sector system. For this reason, a **purpose-built system** tailored to the Informal Sector's structure and workflows is the most viable and sustainable approach.

### 2.3 DIT Legacy Data

UVTAB inherited a significant volume of historical candidate records from the former **Directorate of Industrial Training (DIT)**. This legacy data — spanning years of candidate registrations, assessment results, and certifications — is critical for ongoing **verification of qualifications** issued under the DIT era. However, this data currently exists in outdated formats with no secure, centralized system for storage, retrieval, or verification.

The new EMIS provides a purpose-built repository to **migrate, store, and preserve** DIT legacy records in a structured and searchable database. This ensures that:
- Historical candidate records are **safely stored** and protected against data loss
- Employers, institutions, and regulatory bodies can **verify DIT-era qualifications** efficiently
- Legacy data is **integrated alongside current records**, providing a complete historical view of the Informal Sector assessment program

Without this system, the DIT legacy data remains at risk of degradation, loss, or inaccessibility — undermining UVTAB's ability to honor and verify qualifications issued under its predecessor institution.

### 2.4 Current Situation

As the number of candidates enrolled in the Informal Sector program continues to grow — now exceeding **60,000 registered candidates** — the lack of a dedicated system has become increasingly unsustainable. Data is scattered across spreadsheets, paper records, and disconnected systems, leading to inefficiencies, data inconsistencies, and delays in service delivery.

---

## 3. Problem Statement

The management of the Informal Sector assessment program currently faces the following critical challenges:

### 3.1 Fragmented Data Management
Candidate records, assessment results, and payment information are stored across multiple disconnected formats (paper files, Excel spreadsheets, and isolated databases), making it extremely difficult to maintain a single source of truth.

### 3.2 DIT Legacy Data at Risk
Historical records inherited from the former Directorate of Industrial Training (DIT) remain in outdated and insecure formats. There is no dedicated system to store, manage, or query this data, making it increasingly difficult to verify qualifications issued under the DIT era. The longer this data remains without a proper digital repository, the greater the risk of permanent data loss.

### 3.3 Slow and Error-Prone Manual Processes
Registration of candidates, recording of assessment results, and generation of transcripts are largely manual processes. This leads to:
- **Data entry errors** and duplicate records
- **Delays** in processing results and issuing transcripts
- **Inconsistencies** in candidate records across departments

### 3.4 Lack of Real-Time Visibility
Management and stakeholders have no real-time access to key metrics such as total enrollment figures, assessment completion rates, payment status, or transcript issuance progress. Decision-making relies on periodic manual reports that are often outdated by the time they are compiled.

### 3.5 Payment Tracking Difficulties
Tracking candidate payments across assessment centers is cumbersome. There is no integrated system to verify payment status in real-time, leading to disputes, delayed clearance, and revenue leakage.

### 3.6 Transcript and Award Management
The process of generating, printing, and distributing transcripts is manual and time-consuming. Tracking which transcripts have been printed, collected, and by whom is nearly impossible at scale.

### 3.7 Scalability Concerns
With the candidate base growing year-on-year, the current processes cannot scale to accommodate the increasing volume without a proportional increase in administrative staff and resources.

---

## 4. Project Objectives

### 4.1 General Objective
To develop and deploy a comprehensive, web-based Electronic Management Information System (EMIS) that digitizes and automates the end-to-end management of the Informal Sector assessment program.

### 4.2 Specific Objectives

1. **Centralize candidate data** into a single, secure, and accessible database, eliminating data fragmentation and inconsistencies.

2. **Migrate and preserve DIT legacy data** into a secure, structured digital repository, enabling reliable verification of historical qualifications and safeguarding records from the former Directorate of Industrial Training.

3. **Automate candidate registration** processes, including support for multiple registration categories (Modular, Formal, Worker's PAS) and enrollment periods.

4. **Digitize assessment and results management**, enabling efficient recording, verification, and retrieval of modular and formal assessment results.

5. **Integrate payment processing** with mobile money and other payment platforms (e.g., SchoolPay) to enable real-time payment verification and automated reconciliation.

6. **Automate transcript generation and tracking**, including printing, serial number assignment, collection status monitoring, and reprint management.

7. **Provide real-time dashboards and reports** to support data-driven decision-making at all levels of management.

8. **Implement role-based access control** to ensure data security and appropriate access levels for different user categories.

9. **Build a scalable platform** capable of handling the growing candidate base without performance degradation.

---

## 5. Scope of the Project

### 5.1 In Scope

- DIT legacy data migration, storage, and verification
- Candidate registration and profile management
- Assessment center and occupation management
- Assessment series and intake period management
- Modular and formal assessment results recording and management
- Payment processing and integration with third-party payment providers
- Transcript generation, printing, serial number assignment, and collection tracking
- Awards and certification management
- User management and role-based access control
- Dashboard and analytics
- Data import/export capabilities (Excel, PDF)
- API development for third-party integrations

### 5.2 Out of Scope

- Management of the Formal Sector (separate system)
- Hardware procurement for assessment centers
- Internet connectivity provision to assessment centers
- Training of assessment center staff (covered under a separate training plan)

---

## 6. System Features and Modules

### 6.1 DIT Legacy Data Module
- Migration of historical DIT candidate records into the system
- Structured storage of legacy registrations, results, and certifications
- Search and retrieval of DIT-era records for qualification verification
- Verification reports for employers, institutions, and regulatory bodies
- Data integrity checks and validation during migration

### 6.2 Candidate Management Module
- Candidate registration with personal details, passport photo, and biometric data
- Support for multiple registration categories: Modular, Formal, and Worker's PAS
- Unique registration number and payment code generation
- Candidate search, filtering, and bulk operations
- Candidate profile view with complete history

### 6.3 Assessment Centers Module
- Registration and management of assessment centers nationwide
- Center-level candidate enrollment tracking
- Center-specific reporting and analytics

### 6.4 Occupations Module
- Management of occupational programs and their curricula
- Mapping of occupations to assessment levels and award types
- Module/unit management for modular assessments

### 6.5 Assessment and Results Module
- Assessment series and intake period management
- Recording of modular assessment results (per module/unit)
- Recording of formal assessment results (per paper/level)
- Result verification and approval workflows
- Competency determination and award qualification logic

### 6.6 Awards and Transcripts Module
- Automated identification of candidates who qualify for awards
- Transcript generation with unique serial numbers
- Bulk transcript printing with print tracking
- Transcript collection tracking (collector name, phone, date)
- Transcript reprint management with reason logging
- Export capabilities for awards data

### 6.7 Payments Module
- Payment tracking per candidate
- Integration with **SchoolPay** mobile payment platform
  - Real-time balance inquiry API
  - Automated payment callback processing
  - Support for MTN Mobile Money and other channels
- Payment reconciliation and reporting
- Payment clearance verification

### 6.8 User Management Module
- Role-based access control (Admin, Staff, Assessor, Center Manager)
- User authentication with JWT tokens
- Activity logging and audit trails

### 6.9 Dashboard and Analytics
- Real-time statistics: total candidates, registrations by category, payment status
- Assessment completion rates and trends
- Center-level performance metrics
- Exportable reports

---

## 7. Technical Architecture

### 7.1 Technology Stack

| Component | Technology |
|---|---|
| **Frontend** | React.js with Tailwind CSS |
| **Backend** | Django REST Framework (Python) |
| **Database** | PostgreSQL / SQLite |
| **Web Server** | Nginx + Gunicorn |
| **Authentication** | JWT (JSON Web Tokens) |
| **Payment Integration** | SchoolPay API (REST) |
| **Hosting** | Dedicated server infrastructure |
| **Version Control** | Git |

### 7.2 Architecture Overview

The system follows a **client-server architecture** with a clear separation between the frontend and backend:

- **Frontend (Client):** A Single Page Application (SPA) built with React.js, providing a modern, responsive user interface accessible via web browsers on desktops, tablets, and mobile devices.

- **Backend (API Server):** A RESTful API built with Django REST Framework, handling all business logic, data validation, authentication, and database operations.

- **Database Layer:** A relational database storing all candidate records, assessment results, payment transactions, and system configurations.

- **Integration Layer:** Secure API endpoints for third-party integrations, including the SchoolPay payment gateway, with API key authentication and IP whitelisting.

### 7.3 Security Measures

- **HTTPS encryption** for all data in transit
- **JWT-based authentication** for user sessions
- **Role-based access control** for data authorization
- **API key authentication** for third-party integrations
- **IP whitelisting** for payment gateway endpoints
- **Input validation and sanitization** to prevent injection attacks
- **Regular data backups** and disaster recovery procedures

---

## 8. Implementation Strategy

### 8.1 Methodology
The project follows an **Agile development methodology** with iterative releases, allowing for continuous feedback and improvement.

### 8.2 Phases

#### Phase 1: Foundation (Months 1–2)
- Requirements gathering and analysis
- Database design and architecture setup
- Core candidate management module development
- User authentication and authorization

#### Phase 2: Core Modules (Months 3–4)
- Assessment centers and occupations modules
- Assessment results management (modular and formal)
- Basic reporting and data export

#### Phase 3: Awards and Transcripts (Months 5–6)
- Awards qualification logic and management
- Transcript generation and printing system
- Transcript collection tracking
- Advanced search and filtering

#### Phase 4: Payment Integration (Months 6–7)
- Payment tracking module
- SchoolPay API integration
- Payment reconciliation tools
- Automated payment notifications

#### Phase 5: Optimization and Launch (Months 7–8)
- Performance optimization for large datasets (60,000+ candidates)
- Server-side pagination and efficient data loading
- User acceptance testing (UAT)
- Production deployment and go-live
- Staff training and handover

---

## 9. Expected Outcomes and Benefits

### 9.1 Operational Efficiency
- **80% reduction** in time spent on candidate registration and data entry
- **Elimination of duplicate records** through system-enforced unique identifiers
- **Automated transcript generation** reducing processing time from weeks to minutes

### 9.2 Data Integrity
- Single source of truth for all candidate information
- Elimination of data inconsistencies across departments
- Complete audit trail for all system actions

### 9.3 Financial Management
- Real-time payment tracking and verification
- Automated reconciliation through SchoolPay integration
- Reduced revenue leakage through systematic payment clearance

### 9.4 Service Delivery
- Faster turnaround for results processing and transcript issuance
- Improved transparency for candidates regarding their assessment status
- Better stakeholder communication through real-time data access

### 9.5 Decision Making
- Real-time dashboards providing actionable insights
- Data-driven resource allocation across assessment centers
- Trend analysis for enrollment planning and forecasting

---

## 10. Risk Assessment and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| Internet connectivity issues at assessment centers | High | Medium | Offline data collection forms with batch upload capability |
| Resistance to change from staff | Medium | Medium | Comprehensive training program and change management |
| Data migration errors from existing records | Medium | High | Phased migration with validation checks and rollback procedures |
| Server downtime | Low | High | Redundant hosting, automated backups, and monitoring alerts |
| Security breach | Low | High | Multi-layered security, regular audits, and penetration testing |
| Scope creep | Medium | Medium | Strict change control process and clear scope documentation |
| Third-party integration failures (SchoolPay) | Low | Medium | Fallback manual payment recording; API monitoring and alerts |

---

## 11. Project Timeline

| Phase | Activity | Duration | Status |
|---|---|---|---|
| Phase 1 | Foundation & Core Setup | Months 1–2 | ✅ Completed |
| Phase 2 | Core Modules Development | Months 3–4 | ✅ Completed |
| Phase 3 | Awards & Transcripts | Months 5–6 | ✅ Completed |
| Phase 4 | Payment Integration (SchoolPay) | Months 6–7 | 🔄 In Progress |
| Phase 5 | Optimization & Production Launch | Months 7–8 | 🔄 In Progress |
| Phase 6 | Post-Launch Support & Enhancements | Ongoing | ⏳ Pending |

---

## 12. Budget Estimate

| Item | Description | Estimated Cost (UGX) |
|---|---|---|
| Software Development | Frontend and backend development | _To be determined_ |
| Server Infrastructure | Dedicated server hosting (annual) | _To be determined_ |
| Domain & SSL | Domain registration and SSL certificates | _To be determined_ |
| Third-Party Integrations | SchoolPay integration fees | _To be determined_ |
| Testing & QA | User acceptance testing and quality assurance | _To be determined_ |
| Training | Staff training across assessment centers | _To be determined_ |
| Maintenance & Support | Annual maintenance and support contract | _To be determined_ |
| Contingency | 10% of total project cost | _To be determined_ |
| **Total** | | **_To be determined_** |

> *Note: Detailed budget figures to be populated based on management approval and vendor quotations.*

---

## 13. Sustainability Plan

### 13.1 Technical Sustainability
- Built on open-source technologies (React, Django, PostgreSQL) with no vendor lock-in
- Well-documented codebase and API documentation for future maintainability
- Modular architecture allowing independent upgrades of components

### 13.2 Operational Sustainability
- Training of in-house technical staff for routine system administration
- Comprehensive user manuals and documentation
- Established support channels for issue reporting and resolution

### 13.3 Financial Sustainability
- Reduced operational costs through automation offset the system maintenance costs
- Revenue protection through improved payment tracking
- Scalable infrastructure that grows with the candidate base without proportional cost increases

---

## 14. Conclusion

The UVTAB Electronic Management Information System (EMIS) for the Informal Sector represents a critical step toward modernizing and scaling the management of vocational assessment programs in Uganda. With over 60,000 candidates currently enrolled and numbers growing annually, the need for a robust, digital solution is both immediate and strategic.

The system is already in advanced stages of development, with core modules deployed and operational in a production environment. The ongoing integration with SchoolPay for automated payment processing demonstrates the platform's capability to integrate with the broader financial ecosystem.

We respectfully request approval and support for the continued development, deployment, and scaling of this system to ensure UVTAB can effectively fulfill its mandate of certifying and recognizing the skills of Uganda's informal sector workforce.

---

**Prepared by:**
UVTAB – EMIS Development Team

**Contact:**
Agaba Claire Linda
Email: _[to be filled]_
Phone: _[to be filled]_
