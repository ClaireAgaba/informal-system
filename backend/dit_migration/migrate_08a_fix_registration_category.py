#!/usr/bin/env python
"""
Fix Script: Update registration_category for all candidates
Run: python dit_migration/migrate_08a_fix_registration_category.py [--dry-run]

Updates registration_category based on old DB values.
"""
from db_connection import get_old_connection, log

def fix_registration_category(dry_run=False):
    """Fix registration_category for all candidates"""
    from candidates.models import Candidate
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # First, let's see what categories exist in old DB
    cur.execute("""
        SELECT DISTINCT registration_category, COUNT(*) as cnt
        FROM eims_candidate
        GROUP BY registration_category
        ORDER BY cnt DESC
    """)
    print("\n=== Old DB Category Distribution ===")
    for row in cur.fetchall():
        print(f"  '{row['registration_category']}': {row['cnt']}")
    
    # Get all candidates with their registration_category
    cur.execute("SELECT id, registration_category FROM eims_candidate")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} candidates in old DB")
    
    # Map old categories to new
    category_map = {
        'Modular': 'modular',
        'modular': 'modular',
        'MODULAR': 'modular',
        'M': 'modular',
        'm': 'modular',
        '3': 'modular',
        3: 'modular',
        
        'Formal': 'formal',
        'formal': 'formal',
        'FORMAL': 'formal',
        'F': 'formal',
        'f': 'formal',
        '1': 'formal',
        1: 'formal',
        
        'Workers PAS': 'workers_pas',
        'Workers pas': 'workers_pas',
        'workers_pas': 'workers_pas',
        'workers pas': 'workers_pas',
        'Informal': 'workers_pas',
        'informal': 'workers_pas',
        'INFORMAL': 'workers_pas',
        'I': 'workers_pas',
        'i': 'workers_pas',
        '2': 'workers_pas',
        2: 'workers_pas',
    }
    
    # Count updates needed
    updates = {'modular': 0, 'formal': 0, 'workers_pas': 0, 'unknown': 0}
    to_update = []
    
    for row in rows:
        old_cat = row['registration_category']
        new_cat = category_map.get(old_cat)
        
        if new_cat:
            updates[new_cat] += 1
            to_update.append((row['id'], new_cat))
        else:
            updates['unknown'] += 1
            log(f"  Unknown category: '{old_cat}' for candidate {row['id']}")
    
    print("\n=== Update Summary ===")
    for cat, count in updates.items():
        print(f"  {cat}: {count}")
    
    if dry_run:
        print("\nDRY RUN - No changes made")
        return
    
    # Update candidates
    updated = {'modular': 0, 'formal': 0, 'workers_pas': 0}
    
    for candidate_id, new_cat in to_update:
        try:
            Candidate.objects.filter(id=candidate_id).update(registration_category=new_cat)
            updated[new_cat] += 1
            
            total = sum(updated.values())
            if total % 10000 == 0:
                log(f"  Progress: {total} candidates updated...")
        except Exception as e:
            log(f"  Error updating {candidate_id}: {e}")
    
    print("\n=== Updated ===")
    for cat, count in updated.items():
        print(f"  {cat}: {count}")
    
    log(f"✓ Total updated: {sum(updated.values())}")

def run(dry_run=False):
    """Run fix"""
    log("=" * 50)
    log("FIX: Registration Category")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
    
    fix_registration_category(dry_run=dry_run)
    
    if not dry_run:
        log("=" * 50)
        log("FIX COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
