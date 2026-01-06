#!/usr/bin/env python
"""
Migration Script 8a-photos: Candidate Photos
Run: python dit_migration/migrate_08a_photos.py [--dry-run]

This copies candidate photos from the old system to the new system.
Old system media path: /home/deploy/uvtab_emis/media/
New system media path: /home/deploy/informal-system/backend/media/
"""
import os
import shutil
from db_connection import get_old_connection, log
from django.db import transaction

# Paths - adjust these based on your server setup
OLD_MEDIA_PATH = '/home/deploy/uvtab_emis/uvtab_emis/emis/media'
NEW_MEDIA_PATH = '/home/deploy/informal-system/backend/media'

def show_photo_columns():
    """Show what photo-related columns exist"""
    from db_connection import describe_old_table
    print("\n=== Photo-related columns in eims_candidate ===")
    for col in describe_old_table('eims_candidate'):
        col_name = col['column_name'].lower()
        if 'photo' in col_name or 'image' in col_name or 'pic' in col_name or 'passport' in col_name:
            print(f"  {col['column_name']}: {col['data_type']}")

def migrate_photos(dry_run=False, skip_existing=True):
    """Migrate candidate photos"""
    from candidates.models import Candidate
    
    # Get candidates that already have photos (to skip)
    existing_with_photos = set()
    if skip_existing:
        existing_with_photos = set(
            Candidate.objects.exclude(passport_photo='').exclude(passport_photo__isnull=True)
            .values_list('id', flat=True)
        )
        log(f"Found {len(existing_with_photos)} candidates with photos already (will skip)")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # First find the correct column name
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'eims_candidate' 
        AND (column_name LIKE '%photo%' OR column_name LIKE '%image%' OR column_name LIKE '%pic%')
    """)
    photo_cols = [row['column_name'] for row in cur.fetchall()]
    
    if not photo_cols:
        log("No photo columns found in eims_candidate table")
        cur.close()
        conn.close()
        return
    
    photo_col = photo_cols[0]  # Use first found photo column
    log(f"Using photo column: {photo_col}")
    
    # Get candidates with photos
    cur.execute(f"""
        SELECT id, {photo_col} as photo_path
        FROM eims_candidate 
        WHERE {photo_col} IS NOT NULL AND {photo_col} != ''
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Filter out candidates that already have photos
    if skip_existing:
        rows = [r for r in rows if r['id'] not in existing_with_photos]
    
    log(f"Found {len(rows)} candidates to process")
    
    if dry_run:
        print("\nSample photos (first 10):")
        for row in rows[:10]:
            print(f"  Candidate {row['id']}: {row['photo_path']}")
        return
    
    # Ensure destination directory exists
    dest_photo_dir = os.path.join(NEW_MEDIA_PATH, 'candidates', 'photos')
    os.makedirs(dest_photo_dir, exist_ok=True)
    
    copied = 0
    skipped = 0
    errors = []
    
    for row in rows:
        try:
            candidate_id = row['id']
            old_photo_rel_path = row['photo_path']
            
            if not old_photo_rel_path:
                skipped += 1
                continue
            
            # Build full old path
            old_photo_full_path = os.path.join(OLD_MEDIA_PATH, old_photo_rel_path)
            
            if not os.path.exists(old_photo_full_path):
                # Try without media prefix if path already includes it
                if old_photo_rel_path.startswith('media/'):
                    old_photo_full_path = os.path.join(OLD_MEDIA_PATH, old_photo_rel_path.replace('media/', '', 1))
                
                if not os.path.exists(old_photo_full_path):
                    skipped += 1
                    continue
            
            # Get filename and create new path - keep it short!
            filename = os.path.basename(old_photo_full_path)
            ext = os.path.splitext(filename)[1].lower() or '.jpg'
            # Use just candidate ID to keep path under 100 chars
            new_filename = f"{candidate_id}{ext}"
            new_photo_rel_path = f"candidates/photos/{new_filename}"
            new_photo_full_path = os.path.join(NEW_MEDIA_PATH, new_photo_rel_path)
            
            # Copy the file
            shutil.copy2(old_photo_full_path, new_photo_full_path)
            
            # Update candidate record
            try:
                candidate = Candidate.objects.get(id=candidate_id)
                candidate.passport_photo = new_photo_rel_path
                candidate.save(update_fields=['passport_photo'])
                copied += 1
            except Candidate.DoesNotExist:
                # Candidate not migrated yet
                skipped += 1
            
            if copied % 500 == 0:
                log(f"  Progress: {copied} photos copied...")
                
        except Exception as e:
            errors.append(f"Candidate {row['id']}: {e}")
            skipped += 1
            if len(errors) <= 10:
                log(f"  Error copying photo for candidate {row['id']}: {e}")
    
    log(f"✓ Photos copied: {copied}, skipped: {skipped}")
    if errors:
        log(f"  Errors: {len(errors)}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8a-photos: Candidate Photos")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        migrate_photos(dry_run=True)
    else:
        migrate_photos()
        log("=" * 50)
        log("PHOTO MIGRATION COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
