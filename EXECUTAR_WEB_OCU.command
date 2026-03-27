#!/bin/bash

# Script per iniciar Web OCU en localhost
# Navega al directori del projecte
cd "$(dirname "$0")"

# Mata qualsevol procés de server.py que estigui corrent
pkill -f "python3 server.py" 2>/dev/null

# Espera un moment per assegurar que el port s'allibera
sleep 1

# Inicia el servidor en segon pla
echo "Iniciant servidor Web OCU..."
python3 server.py &
SERVER_PID=$!

# Espera que el servidor estigui llest
sleep 2

# Obre el navegador
echo "Obrint navegador a http://localhost:8000..."
open http://localhost:8000

echo ""
echo "========================================="
echo "Servidor Web OCU iniciat correctament!"
echo "PID del servidor: $SERVER_PID"
echo "URL: http://localhost:8000"
echo "========================================="
echo ""
echo "Per aturar el servidor:"
echo "  - Tanca aquesta finestra, o"
echo "  - Prem Ctrl+C, o"
echo "  - Executa: kill $SERVER_PID"
echo ""

# Manté el script corrent per veure els logs del servidor
wait $SERVER_PID
