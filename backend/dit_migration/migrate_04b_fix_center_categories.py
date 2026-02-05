#!/usr/bin/env python
"""
Fix Script: Update Assessment Center Categories from Old Database
Run: python dit_migration/migrate_04b_fix_center_categories.py [--dry-run]
"""
from db_connection import get_old_connection, log, describe_old_table
from django.db import transaction

def show_old_categories():
    """Show category data in old database"""
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check if there's a category field or category_id in assessment centers
    print("\n=== Old Assessment Center Structure ===")
    for col in describe_old_table('eims_assessmentcenter'):
        print(f"  {col['column_name']}: {col['data_type']}")
    
    # Try to find category info
    print("\n=== Checking for category data ===")
    
    # Check for category_id or category field
    try:
        cur.execute("""
            SELECT DISTINCT category_id, COUNT(*) as cnt 
            FROM eims_assessmentcenter 
            GROUP BY category_id
        """)
        rows = cur.fetchall()
        print("\nCategory ID distribution:")
        for row in rows:
            print(f"  category_id={row['category_id']}: {row['cnt']} centers")
    except Exception as e:
        print(f"No category_id field: {e}")
    
    # Check if there's a separate category table
    try:
        cur.execute("SELECT * FROM eims_assessmentcentercategory")
        rows = cur.fetchall()
        print("\nCategory table contents:")
        for row in rows:
            print(f"  {row}")
    except Exception as e:
        print(f"No category table found: {e}")
    
    # Try looking at center names/numbers for patterns
    print("\n=== Sample centers by pattern ===")
    cur.execute("""
        SELECT center_number, center_name, category_id 
        FROM eims_assessmentcenter 
        ORDER BY category_id, center_number 
        LIMIT 20
    """)
    for row in cur.fetchall():
        print(f"  {row['center_number']}: {row['center_name']} (cat_id: {row.get('category_id')})")
    
    cur.close()
    conn.close()

def get_category_mapping():
    """Get category mapping from old database"""
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Try to get the category table
    mapping = {}
    try:
        cur.execute("SELECT id, name FROM eims_assessmentcentercategory")
        rows = cur.fetchall()
        for row in rows:
            name = row['name'].lower()
            if 'tech' in name:
                mapping[row['id']] = 'TTI'
            elif 'work' in name:
                mapping[row['id']] = 'workplace'
            else:
                mapping[row['id']] = 'VTI'
        print(f"\nCategory mapping from table: {mapping}")
    except Exception as e:
        print(f"Could not get category table: {e}")
        # Try to infer from names
        mapping = {
            1: 'VTI',  # Adjust these based on actual data
            2: 'TTI',
            3: 'workplace',
        }
    
    cur.close()
    conn.close()
    return mapping

def fix_categories(dry_run=False):
    """Fix assessment center categories"""
    from assessment_centers.models import AssessmentCenter
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get category mapping
    category_mapping = get_category_mapping()
    
    # Get centers with their category_id
    cur.execute("SELECT id, center_number, category_id FROM eims_assessmentcenter")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} centers to update")
    
    updates = {'VTI': 0, 'TTI': 0, 'workplace': 0}
    
    for row in rows:
        old_category_id = row.get('category_id')
        new_category = category_mapping.get(old_category_id, 'VTI')
        
        if dry_run:
            updates[new_category] += 1
        else:
            try:
                center = AssessmentCenter.objects.get(id=row['id'])
                if center.assessment_category != new_category:
                    center.assessment_category = new_category
                    center.save()
                updates[new_category] += 1
            except AssessmentCenter.DoesNotExist:
                pass
    
    log(f"Category updates: {updates}")
    return updates

def run(dry_run=False):
    """Run fix"""
    log("=" * 50)
    log("FIX: Assessment Center Categories")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_categories()
        fix_categories(dry_run=True)
    else:
        try:
            with transaction.atomic():
                fix_categories()
                log("=" * 50)
                log("FIX COMPLETED!")
                log("=" * 50)
        except Exception as e:
            log(f"FIX FAILED: {e}")
            raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
