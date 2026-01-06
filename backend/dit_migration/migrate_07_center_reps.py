#!/usr/bin/env python
"""
Migration Script 7: Center Representatives
Run: python dit_migration/migrate_07_center_reps.py [--dry-run]
"""
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_centerrepresentative columns:")
    try:
        for col in describe_old_table('eims_centerrepresentative'):
            print(f"  {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"  Error: {e}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    try:
        print(f"  eims_centerrepresentative: {get_old_table_count('eims_centerrepresentative')}")
    except:
        print("  eims_centerrepresentative: Table not found")

def migrate_center_reps(dry_run=False):
    """Migrate center representatives"""
    from users.models import CenterRepresentative, User
    from assessment_centers.models import AssessmentCenter, CenterBranch
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_centerrepresentative ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} center representatives in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            name = row.get('name') or row.get('fullname') or row.get('full_name')
            center_id = row.get('assessment_center_id') or row.get('center_id')
            print(f"  ID: {row['id']}, Name: {name}, Center ID: {center_id}, Email: {row.get('email')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            # Get name from various possible field names
            fullname = row.get('name') or row.get('fullname') or row.get('full_name') or ''
            fullname = fullname[:200]
            
            # Get center
            center_id = row.get('assessment_center_id') or row.get('center_id')
            if not center_id:
                skipped += 1
                continue
            
            try:
                center = AssessmentCenter.objects.get(id=center_id)
            except AssessmentCenter.DoesNotExist:
                skipped += 1
                continue
            
            # Get branch if exists
            branch = None
            branch_id = row.get('assessment_center_branch_id') or row.get('branch_id')
            if branch_id:
                try:
                    branch = CenterBranch.objects.get(id=branch_id)
                except CenterBranch.DoesNotExist:
                    pass
            
            contact = (row.get('contact') or row.get('phone') or '')[:15]
            account_status = row.get('account_status') or 'active'
            if account_status not in ['active', 'inactive', 'suspended']:
                account_status = 'active'
            
            # Generate email based on center number
            email = row.get('email') or f"{center.center_number.lower()}@uvtab.go.ug"
            
            # Check if center rep with this email already exists
            existing = CenterRepresentative.objects.filter(email=email).first()
            if existing:
                # Update existing
                existing.fullname = fullname
                existing.contact = contact
                existing.assessment_center = center
                existing.assessment_center_branch = branch
                existing.account_status = account_status
                existing.save()
            else:
                # Create user first
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={
                        'email': email,
                        'first_name': fullname.split()[0] if fullname else '',
                        'last_name': ' '.join(fullname.split()[1:]) if len(fullname.split()) > 1 else '',
                        'user_type': 'center_representative',
                        'phone_number': contact,
                        'is_staff': False,
                        'is_active': True
                    }
                )
                if created:
                    user.set_password('uvtab@2025')
                    user.save()
                
                # Create center rep
                CenterRepresentative.objects.create(
                    id=row['id'],
                    user=user,
                    fullname=fullname,
                    email=email,
                    contact=contact,
                    assessment_center=center,
                    assessment_center_branch=branch,
                    account_status=account_status,
                )
            migrated += 1
            
        except Exception as e:
            log(f"  Error migrating center rep {row['id']}: {e}")
            skipped += 1
    
    log(f"✓ Center representatives migrated: {migrated}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 7: Center Representatives")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_center_reps(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_center_reps()
                log("=" * 50)
                log("MIGRATION 7 COMPLETED!")
                log("=" * 50)
        except Exception as e:
            log(f"MIGRATION FAILED: {e}")
            raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
