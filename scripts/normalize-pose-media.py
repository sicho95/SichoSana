#!/usr/bin/env python3
"""Direction photo SichoSana : normalisation sans déformer les postures ni supprimer les crédits."""
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageDraw

FOLDER=Path("static/media/poses")
SIZE=(1080,720)
OUTER=(244,243,236)

def normalize(path):
    with Image.open(path) as original:
        original=ImageOps.exif_transpose(original).convert("RGB")
        original.thumbnail((1010,640),Image.Resampling.LANCZOS)
        # Une même dominante lin/sauge, des proportions fixes, et aucune coupe
        # qui rendrait la démonstration anatomique trompeuse.
        original=ImageEnhance.Color(original).enhance(.75)
        original=ImageEnhance.Contrast(original).enhance(.97)
        overlay=Image.new("RGB",original.size,(241,239,226))
        original=Image.blend(original,overlay,.045)
        canvas=Image.new("RGB",SIZE,OUTER)
        x=(SIZE[0]-original.width)//2
        y=(SIZE[1]-original.height)//2
        canvas.paste(original,(x,y))
        canvas.save(path,format="PNG",optimize=True,compress_level=9)
    print("PHOTO_NORMALISEE",path.name)

for source in sorted(FOLDER.glob("*.png")):
    normalize(source)
