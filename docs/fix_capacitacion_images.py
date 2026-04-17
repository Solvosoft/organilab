#!/usr/bin/env python3
"""
Copies images from docs/source/_static/ into docs/source/_extra/capacitacion/img/
and rewrites every src attribute in capacitacion HTML files to use
that local directory instead of the broken ../../_static/ paths.
"""
import os
import re
import shutil
from pathlib import Path

DOCS_DIR = Path(__file__).parent
SOURCE_STATIC = DOCS_DIR / "source" / "_static"
CAP_DIR = DOCS_DIR / "source" / "_extra" / "capacitacion"
IMG_DIR = CAP_DIR / "img"

# Matches src=".../_static/(gif/)?filename.ext"
SRC_PATTERN = re.compile(
    r'src="[^"]*/_static/(?:gif/)?([^/"]+\.(gif|png|jpg|jpeg|svg|webp))"',
    re.IGNORECASE,
)


def collect_images():
    IMG_DIR.mkdir(exist_ok=True)
    count = 0
    for f in SOURCE_STATIC.glob("*.png"):
        shutil.copy2(f, IMG_DIR / f.name)
        count += 1
    gif_dir = SOURCE_STATIC / "gif"
    if gif_dir.exists():
        for f in gif_dir.glob("*.gif"):
            shutil.copy2(f, IMG_DIR / f.name)
            count += 1
    return count


def fix_html_files():
    updated = 0
    for html_file in CAP_DIR.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8")

        rel_img = os.path.relpath(IMG_DIR, html_file.parent).replace(os.sep, "/")

        def replace_src(m):
            return f'src="{rel_img}/{m.group(1)}"'

        new_content = SRC_PATTERN.sub(replace_src, content)
        if new_content != content:
            html_file.write_text(new_content, encoding="utf-8")
            updated += 1
    return updated


if __name__ == "__main__":
    if not SOURCE_STATIC.exists():
        print(f"ERROR: {SOURCE_STATIC} does not exist.")
        raise SystemExit(1)
    img_count = collect_images()
    html_count = fix_html_files()
    print(f"  Copied {img_count} images → {IMG_DIR.relative_to(DOCS_DIR.parent)}")
    print(f"  Updated {html_count} HTML files in {CAP_DIR.relative_to(DOCS_DIR.parent)}")