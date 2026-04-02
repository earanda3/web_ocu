#!/usr/bin/env python3
"""
Generates content/manifest.json by scanning the content/ directory.
Each subfolder becomes one interactive word on the web.

File type detection:
  .stl              → 3D viewer (right-click)
  .pdf              → PDF viewer (click)
  .png .jpg .jpeg
  .gif .webp .avif  → image spawn on canvas (click)

Run manually:  python3 scripts/generate_manifest.py
Run in CI:     automatically via GitHub Actions before deploy
"""

import os
import json

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content')
MANIFEST_PATH = os.path.join(CONTENT_DIR, 'manifest.json')

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif'}
STL_EXTS   = {'.stl'}
PDF_EXTS   = {'.pdf'}
SKIP_FILES = {'.ds_store', '.gitkeep', '.gitignore', 'manifest.json'}


def classify(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in STL_EXTS:
        return 'stl'
    if ext in PDF_EXTS:
        return 'pdf'
    if ext in IMAGE_EXTS:
        return 'image'
    return None


def main():
    if not os.path.isdir(CONTENT_DIR):
        print(f"ERROR: {CONTENT_DIR} does not exist")
        return

    manifest = []

    for folder_name in sorted(os.listdir(CONTENT_DIR)):
        folder_path = os.path.join(CONTENT_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        if folder_name.startswith('.'):
            continue

        files_by_type = {'stl': [], 'pdf': [], 'image': []}

        for filename in sorted(os.listdir(folder_path)):
            if filename.lower() in SKIP_FILES or filename.startswith('.'):
                continue
            ftype = classify(filename)
            if ftype:
                files_by_type[ftype].append(filename)

        all_files = files_by_type['stl'] + files_by_type['pdf'] + files_by_type['image']
        types = [t for t in ('stl', 'pdf', 'image') if files_by_type[t]]

        manifest.append({
            'word':   folder_name,
            'folder': f'content/{folder_name}',
            'types':  types,
            'files':  {
                'stl':   files_by_type['stl'],
                'pdf':   files_by_type['pdf'],
                'image': files_by_type['image'],
            },
        })

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Also write manifest.js for synchronous loading (no async fetch needed)
    js_path = os.path.join(CONTENT_DIR, 'manifest.js')
    js_payload = json.dumps(manifest, indent=2, ensure_ascii=False)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(f'window.CONTENT_MANIFEST = {js_payload};\n')

    print(f"manifest.json + manifest.js generated — {len(manifest)} entries:")
    for entry in manifest:
        counts = ', '.join(
            f"{len(entry['files'][t])} {t}"
            for t in entry['types']
        ) or 'empty'
        print(f"  [{entry['word']}] {counts}")


if __name__ == '__main__':
    main()
