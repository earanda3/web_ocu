#!/bin/bash

# Script per executar la Web OCU
# Ús: ./executar_web_ocu.sh

# Colors per la sortida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}   Iniciant Web OCU${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Verificar si python3 està instal·lat
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no està instal·lat"
    exit 1
fi

# Obtenir el directori on es troba aquest script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Anar al directori del script
cd "$SCRIPT_DIR"

# Verificar si index.html existeix
if [ ! -f "index.html" ]; then
    echo "Error: No s'ha trobat index.html en aquest directori"
    exit 1
fi

# Iniciar el servidor web
echo -e "${GREEN}✓${NC} Servidor iniciat a: ${BLUE}http://localhost:8001${NC}"
echo ""
echo "Controls de la intro:"
echo "  - Prem ${GREEN}ENTER${NC} per saltar la introducció"
echo "  - Doble-tap (mòbil) per saltar la introducció"
echo ""
echo "Prem ${GREEN}Ctrl+C${NC} per aturar el servidor"
echo ""
echo -e "${BLUE}================================${NC}"
echo ""

# Iniciar el servidor Python en el directori actual
python3 -m http.server 8001
