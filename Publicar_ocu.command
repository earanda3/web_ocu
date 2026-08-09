#!/usr/bin/env bash
#
# Publicar_ocu.command — fes-hi DOBLE CLIC per publicar els continguts nous a ocu.cat.
#
# Deixa els teus arxius nous a la carpeta que toqui dins de content/
# (per exemple content/ocu3D/ per als .stl, content/newtro/ per als .png)
# i després fes doble clic en aquest fitxer. La resta és automàtica.
#
# Aquest fitxer no es publica a la web (queda exclòs del desplegament).
#
cd "$(dirname "$0")"
echo "════════════════════════════════════════════"
echo "  Publicant continguts a ocu.cat"
echo "════════════════════════════════════════════"
echo ""
bash scripts/publish.sh
STATUS=$?
echo ""
if [ $STATUS -ne 0 ]; then
  echo "⚠️  Alguna cosa ha fallat (codi $STATUS). Mira els missatges de sobre."
fi
echo ""
echo "Pots tancar aquesta finestra."
# Manté la finestra oberta encara que s'executi amb doble clic.
read -n 1 -s -r -p "Prem qualsevol tecla per sortir…"
echo ""
