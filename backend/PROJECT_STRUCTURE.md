# EMIS Project Structure

```
informal system/
├── manage.py                      # Django management script
├── setup.sh                       # Setup automation script
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Project overview
├── ARCHITECTURE.md                # System architecture documentation
├── DEVELOPMENT.md                 # Development guide
├── PROJECT_STRUCTURE.md           # This file
│
├── venv/                          # Virtual environment (not in git)
│
├── emis/                          # Main Django project
│   ├── __init__.py
│   ├── settings.py                # Project settings
│   ├── urls.py                    # Main URL configuration
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
│
├── users/                         # User management app
│   ├── __init__.py
│   ├── apps.py                    # App configuration
│   ├── models.py                  # User model (custom)
│   ├── admin.py                   # Admin interface
│   ├── views.py                   # API views
│   ├── serializers.py             # DRF serializers
│   └── urls.py                    # App URLs
│
├── candidates/                    # Candidate management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # Candidate model
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── occupations/                   # Occupation/trade management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # Occupation, OccupationUnit models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── assessment_centers/            # Assessment center management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # AssessmentCenter, CenterStaff models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── assessment_series/             # Assessment series management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # AssessmentSeries, CandidateRegistration models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── results/                       # Results management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # AssessmentResult, FinalResult models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── awards/                        # Certificate/awards management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # Certificate model
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── reports/                       # Reports management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # Report model
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── complaints/                    # Complaints management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # Complaint model
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── uvtab_fees/                    # Fee and payment management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # FeeStructure, Payment models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── statistics/                    # Statistics management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # SystemStatistic model
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
├── configurations/                # System configuration app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                  # SystemConfiguration, EmailTemplate models
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
│
└── dit_migration/                 # Data migration app
    ├── __init__.py
    ├── apps.py
    ├── models.py                  # MigrationLog, LegacyDataMapping models
    ├── admin.py
    ├── views.py
    ├── serializers.py
    └── urls.py
```

## Directories to be Created (After Setup)

```
informal system/
├── media/                         # User uploaded files
│   ├── profiles/                  # User profile pictures
│   ├── candidates/                # Candidate documents
│   │   ├── photos/
│   │   └── documents/
│   ├── certificates/              # Generated certificates
│   │   └── qr/                    # QR codes
│   ├── complaints/                # Complaint documents
│   └── reports/                   # Generated reports
│
├── static/                        # Static files (CSS, JS, images)
│   └── admin/                     # Admin interface assets
│
└── staticfiles/                   # Collected static files (production)
```

## Key Files Explained

### Configuration Files

- **manage.py**: Django's command-line utility for administrative tasks
- **setup.sh**: Automated setup script for initial project configuration
- **requirements.txt**: Python package dependencies
- **.env.example**: Template for environment variables
- **.gitignore**: Files and directories to exclude from version control

### Documentation Files

- **README.md**: Project overview and quick start guide
- **ARCHITECTURE.md**: Detailed system architecture and design decisions
- **DEVELOPMENT.md**: Development guidelines and common tasks
- **PROJECT_STRUCTURE.md**: This file - project structure overview

### Main Project (emis/)

- **settings.py**: Django settings (database, apps, middleware, etc.)
- **urls.py**: Main URL routing configuration
- **wsgi.py**: WSGI server configuration for deployment
- **asgi.py**: ASGI server configuration for async support

### App Structure (Each App)

Each of the 13 apps follows the same structure:

- **apps.py**: App configuration and metadata
- **models.py**: Database models (tables)
- **admin.py**: Django admin interface configuration
- **views.py**: API views and business logic
- **serializers.py**: Data serialization/deserialization
- **urls.py**: App-specific URL routing

## Database Models Summary

### users
- User (custom user model with roles)

### candidates
- Candidate (linked to User)

### occupations
- Occupation
- OccupationUnit

### assessment_centers
- AssessmentCenter
- CenterStaff

### assessment_series
- AssessmentSeries
- CandidateRegistration

### results
- AssessmentResult
- FinalResult

### awards
- Certificate

### reports
- Report

### complaints
- Complaint

### uvtab_fees
- FeeStructure
- Payment

### statistics
- SystemStatistic

### configurations
- SystemConfiguration
- EmailTemplate

### dit_migration
- MigrationLog
- LegacyDataMapping

## API Endpoints Summary

All endpoints are prefixed with `/api/`:

- `/api/users/` - User management
- `/api/candidates/` - Candidate operations
- `/api/occupations/` - Occupation and units
- `/api/assessment-centers/` - Centers and staff
- `/api/assessment-series/` - Series and registrations
- `/api/results/` - Assessment and final results
- `/api/awards/` - Certificates
- `/api/reports/` - Report generation
- `/api/complaints/` - Complaint handling
- `/api/uvtab-fees/` - Fees and payments
- `/api/statistics/` - System statistics
- `/api/configurations/` - System configs and templates
- `/api/dit-migration/` - Migration logs and mappings

## Total Files Created

- **13 Django apps** (each with 7 files)
- **Main project** (5 files)
- **Configuration files** (5 files)
- **Documentation files** (4 files)
- **Setup script** (1 file)

**Total: 105+ files** organized in a clean, modular structure.
