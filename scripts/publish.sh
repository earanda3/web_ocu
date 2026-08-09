#!/usr/bin/env bash
#
# publish.sh — publica els continguts nous a ocu.cat amb un sol pas.
#
# Què fa, en ordre:
#   ①  Converteix a Draco .glb qualsevol .stl nou o modificat de content/*/  (els
#      models 3D que ja tenen un .glb al dia se salten, així va ràpid).
#   ②  Regenera el manifest (content/manifest.json + manifest.js) perquè els
#      arxius nous (STL, PNG, PDF…) apareguin com a paraules a la web.
#   ③  Fa el commit i el push a main → GitHub Actions desplega sol a ocu.cat.
#
# Ús:
#   scripts/publish.sh                # missatge de commit automàtic
#   scripts/publish.sh "El meu text"  # missatge de commit personalitzat
#   NO_PUSH=1 scripts/publish.sh      # fes-ho tot MENYS el push (per provar)
#
set -euo pipefail

# Situa'ns a l'arrel del repositori (aquest script viu a scripts/).
cd "$(dirname "$0")/.."

MSG="${1:-Actualitza continguts (STL/PNG/PDF) — auto}"

echo "① Convertint STL nous o modificats a Draco .glb…"
# Tots els .stl dins de subcarpetes de content/ (evita fitxers solts a l'arrel).
# Bucle portable (macOS porta bash 3.2, sense `mapfile`); -print0 aguanta espais.
STL_FILES=()
while IFS= read -r -d '' f; do
  STL_FILES+=("$f")
done < <(find content -mindepth 2 -name '*.stl' -print0 2>/dev/null)
if [ "${#STL_FILES[@]}" -gt 0 ]; then
  python3 scripts/stl_to_glb.py "${STL_FILES[@]}"
else
  echo "  (cap .stl a content/*/)"
fi

echo ""
echo "② Regenerant el manifest…"
python3 scripts/generate_manifest.py

echo ""
echo "③ Preparant els canvis…"
# Només els continguts: imatges/PDF/.glb nous o esborrats + el manifest regenerat.
# (No toquem codi ni fitxers solts de l'arrel — això evita publicar coses per error.)
git add content/
if git diff --cached --quiet; then
  echo "✔ No hi ha res nou per publicar. Tot ja està al dia."
  exit 0
fi
echo "Canvis a publicar:"
git --no-pager diff --cached --stat

if [ "${NO_PUSH:-0}" = "1" ]; then
  echo ""
  echo "NO_PUSH=1 → em quedo aquí (no faig commit ni push). Desfés amb: git reset"
  exit 0
fi

git commit -m "$MSG"
git push origin main
echo ""
echo "✅ Publicat. ocu.cat s'actualitzarà tot sol en 3–4 minuts."
echo "   (Pots seguir el desplegament a GitHub → Actions.)"
