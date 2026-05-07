import os
import glob
from PIL import Image

def find_images():
    # The views.py _signature_paths looks in settings.MEDIA_ROOT / 'images'
    # Or static dirs. Let's just find anything named coat or uvtab
    paths = glob.glob('/Users/fbamwe/Documents/code/informal-system/backend/media/**/*.png', recursive=True)
    paths += glob.glob('/Users/fbamwe/Documents/code/informal-system/backend/media/**/*.jpg', recursive=True)
    paths += glob.glob('/Users/fbamwe/Documents/code/informal-system/backend/static/**/*.png', recursive=True)
    paths += glob.glob('/Users/fbamwe/Documents/code/informal-system/backend/static/**/*.jpg', recursive=True)
    
    for p in paths:
        if 'coat' in p.lower() or 'uvtab' in p.lower():
            try:
                img = Image.open(p)
                print(f"File: {p}")
                print(f"  Mode: {img.mode}, Size: {img.size}")
                if 'A' in img.mode:
                    alpha = img.split()[-1]
                    extrema = alpha.getextrema()
                    print(f"  Alpha extrema: {extrema}")
                else:
                    print(f"  No alpha channel!")
            except Exception as e:
                print(f"Error reading {p}: {e}")

find_images()
