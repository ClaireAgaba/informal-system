#!/usr/bin/env python
"""
Migration Script 9: Complaints
Run: python dit_migration/migrate_09_complaints.py [--dry-run]

Migrates complaints from old system to new system.
"""
import argparse
from db_connection import get_old_connection, log, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old complaints data"""
    print("\n=== Old Table Structure ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check for complaints table
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%complaint%'
    """)
    tables = cur.fetchall()
    print("\nComplaint-related tables:")
    for t in tables:
        print(f"  {t['table_name']}")
    
    # Check eims_complaint structure if exists
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'eims_complaint'
    """)
    if cur.fetchone():
        print("\neims_complaint columns:")
        for col in describe_old_table('eims_complaint'):
            print(f"  {col['column_name']}: {col['data_type']}")
        
        cur.execute('SELECT COUNT(*) as count FROM eims_complaint')
        print(f"\nTotal complaints in old system: {cur.fetchone()['count']}")
        
        # Sample data
        cur.execute('SELECT * FROM eims_complaint LIMIT 3')
        rows = cur.fetchall()
        print("\nSample complaints:")
        for row in rows:
            print(f"  {dict(row)}")
    else:
        print("\nNo eims_complaint table found")
    
    cur.close()
    conn.close()

def count_records():
    """Count complaint records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'eims_complaint'
    """)
    if cur.fetchone():
        cur.execute('SELECT COUNT(*) as count FROM eims_complaint')
        old_count = cur.fetchone()['count']
        print(f"Old complaints: {old_count}")
    else:
        print("No eims_complaint table found in old system")
        old_count = 0
    
    cur.close()
    conn.close()
    
    # New system count
    from complaints.models import Complaint
    new_count = Complaint.objects.count()
    print(f"New complaints: {new_count}")
    
    return old_count

def migrate_complaints(dry_run=False):
    """Migrate complaints from old to new system"""
    from complaints.models import Complaint, ComplaintCategory
    from assessment_centers.models import AssessmentCenter
    from assessment_series.models import AssessmentSeries
    from occupations.models import Occupation
    from users.models import User
    
    log("Starting complaints migration...")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check if complaints table exists
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'eims_complaint'
    """)
    if not cur.fetchone():
        log("No eims_complaint table found - nothing to migrate")
        cur.close()
        conn.close()
        return
    
    # Get old complaints
    cur.execute('SELECT * FROM eims_complaint ORDER BY id')
    old_complaints = cur.fetchall()
    log(f"Found {len(old_complaints)} complaints to migrate")
    
    if not old_complaints:
        log("No complaints to migrate")
        cur.close()
        conn.close()
        return
    
    # Build mappings
    centers_by_id = {c.id: c for c in AssessmentCenter.objects.all()}
    series_by_id = {s.id: s for s in AssessmentSeries.objects.all()}
    occupations_by_id = {o.id: o for o in Occupation.objects.all()}
    users_by_id = {u.id: u for u in User.objects.all()}
    
    # Get or create a default category
    default_category, _ = ComplaintCategory.objects.get_or_create(
        name='General',
        defaults={'description': 'General complaints migrated from old system'}
    )
    
    # Get or create a default user for old complaints without user
    default_user = User.objects.filter(is_superuser=True).first()
    if not default_user:
        default_user = User.objects.first()
    
    created = 0
    skipped_exists = 0
    skipped_no_center = 0
    skipped_no_series = 0
    skipped_no_occupation = 0
    errors = 0
    
    for old in old_complaints:
        try:
            # Get related objects
            center = centers_by_id.get(old.get('exam_center_id') or old.get('center_id'))
            series = series_by_id.get(old.get('exam_series_id') or old.get('series_id'))
            occupation = occupations_by_id.get(old.get('program_id') or old.get('occupation_id'))
            created_by = users_by_id.get(old.get('created_by_id') or old.get('user_id'))
            
            if not center:
                skipped_no_center += 1
                continue
            if not series:
                skipped_no_series += 1
                continue
            if not occupation:
                skipped_no_occupation += 1
                continue
            
            if not created_by:
                created_by = default_user
            
            # Check if already migrated (by ticket number if exists)
            ticket = old.get('ticket_number') or old.get('ticket')
            if ticket and Complaint.objects.filter(ticket_number=ticket).exists():
                skipped_exists += 1
                continue
            
            if dry_run:
                created += 1
                continue
            
            with transaction.atomic():
                complaint = Complaint(
                    category=default_category,
                    exam_center=center,
                    exam_series=series,
                    program=occupation,
                    phone=old.get('phone', '') or '',
                    issue_description=old.get('issue_description') or old.get('description') or old.get('complaint') or '',
                    status=old.get('status', 'new') or 'new',
                    team_response=old.get('team_response') or old.get('response') or '',
                    created_by=created_by,
                )
                # Set ticket number if provided
                if ticket:
                    complaint.ticket_number = ticket
                complaint.save()
                
                # Update timestamps if available
                if old.get('created_at'):
                    Complaint.objects.filter(id=complaint.id).update(created_at=old['created_at'])
                
                created += 1
                
        except Exception as e:
            errors += 1
            log(f"Error migrating complaint {old.get('id')}: {e}")
    
    cur.close()
    conn.close()
    
    log(f"\n=== Migration Summary ===")
    log(f"Created: {created}")
    log(f"Skipped (exists): {skipped_exists}")
    log(f"Skipped (no center): {skipped_no_center}")
    log(f"Skipped (no series): {skipped_no_series}")
    log(f"Skipped (no occupation): {skipped_no_occupation}")
    log(f"Errors: {errors}")
    
    if dry_run:
        log("\n*** DRY RUN - No changes made ***")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate complaints')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without making changes')
    parser.add_argument('--structure', action='store_true', help='Show old table structure')
    parser.add_argument('--count', action='store_true', help='Show record counts')
    args = parser.parse_args()
    
    if args.structure:
        show_old_structure()
    elif args.count:
        count_records()
    else:
        migrate_complaints(dry_run=args.dry_run)
