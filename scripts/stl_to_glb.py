#!/usr/bin/env python3
"""
Convert STL models to Draco-compressed glTF (.glb) for the web STL viewer.

Why: the raw STL models are huge (6–60 MB each) but the web viewer needs them
small for mobile. Draco compresses the *same* triangles losslessly-ish
(position quantization), so ALL detail is preserved for close-up zoom — unlike
mesh decimation, which destroys these intricate multi-shell models.

Typical result: ~20–40x smaller with no visible quality loss.

Usage:
    python3 scripts/stl_to_glb.py                 # convert every .stl in content/ocu3D/
    python3 scripts/stl_to_glb.py path/to/a.stl   # convert specific file(s)

Requirements:
    pip install trimesh
    npm i -g gltf-pipeline   (or npx will fetch it on demand)

Notes:
    - Normals are NOT stored; the viewer recomputes them on load (smaller files,
      consistent shading).
    - quantizePositionBits=14 → grid of 1/16384 of the model's size, i.e.
      imperceptible even when zoomed in very close. Raise to 16 for CAD-grade.
"""
import os
import sys
import glob
import subprocess
import tempfile
# NOTE: `trimesh` is imported lazily (only when a model actually needs converting),
# so routine runs with nothing new to convert don't require it to be installed.

QUANT_POSITION_BITS = 14
COMPRESSION_LEVEL = 7  # 0..10, higher = smaller + slower (quality unaffected)
DEFAULT_DIR = os.path.join(os.path.dirname(__file__), "..", "content", "ocu3D")


def is_up_to_date(stl_path: str) -> bool:
    """True if a .glb already exists and is newer than its .stl source."""
    glb_path = os.path.splitext(stl_path)[0] + ".glb"
    return (
        os.path.exists(glb_path)
        and os.path.getmtime(glb_path) >= os.path.getmtime(stl_path)
    )


def _require_trimesh():
    try:
        import trimesh
        return trimesh
    except ImportError:
        sys.exit(
            "\nERROR: falta el paquet 'trimesh', necessari per convertir STL a .glb.\n"
            "Instal·la'l una sola vegada amb:\n"
            "    pip3 install trimesh\n"
            "(Si dóna problemes amb Python 3.14, digues-m'ho i et munto un entorn amb python3.12.)\n"
        )


def convert(stl_path: str) -> None:
    trimesh = _require_trimesh()
    base, _ = os.path.splitext(stl_path)
    glb_path = base + ".glb"
    mesh = trimesh.load(stl_path, process=False)
    faces = len(mesh.faces)

    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
        tmp_glb = tmp.name
    try:
        mesh.export(tmp_glb)  # uncompressed glb
        subprocess.run(
            [
                "npx", "--yes", "gltf-pipeline@4",
                "-i", tmp_glb, "-o", glb_path, "-d",
                "--draco.compressionLevel", str(COMPRESSION_LEVEL),
                "--draco.quantizePositionBits", str(QUANT_POSITION_BITS),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        if os.path.exists(tmp_glb):
            os.remove(tmp_glb)

    src_mb = os.path.getsize(stl_path) / 1048576
    out_mb = os.path.getsize(glb_path) / 1048576
    print(f"  {os.path.basename(stl_path):<42} {src_mb:6.1f} MB -> {out_mb:5.2f} MB "
          f"({src_mb/out_mb:4.1f}x)  {faces} tris")


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    files = args if args else sorted(glob.glob(os.path.join(DEFAULT_DIR, "*.stl")))
    if not files:
        print("No .stl files found.")
        return

    # Skip models that already have an up-to-date .glb (unless --force) so re-runs
    # are fast — only newly added or edited .stl files get re-converted.
    todo = [f for f in files if force or not is_up_to_date(f)]
    skipped = len(files) - len(todo)
    if skipped:
        print(f"{skipped} model(s) already up to date — skipping.")
    if not todo:
        print("Nothing to convert.")
        return
    print(f"Converting {len(todo)} model(s) to Draco .glb "
          f"(qp={QUANT_POSITION_BITS}, level={COMPRESSION_LEVEL})…")
    for f in todo:
        convert(f)
    print("Done.")


if __name__ == "__main__":
    main()
