#!/bin/bash
# Script de despliegue DocAI Platform (producción)
set -e
cd "$(dirname "$0")"
echo "=== DocAI Platform - Despliegue ==="

# Crear venv si no existe
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "Instalando dependencias..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Crear directorios
mkdir -p input output
echo "✅ Directorios input/ output/ listos"

# Verificar que el proyecto está completo
if [ -f "src/docai_platform.py" ] && [ -f "src/document_processor.py" ] && [ -f "src/config.py" ]; then
    echo "✅ Archivos del proyecto verificados"
else
    echo "❌ Faltan archivos del proyecto"
    exit 1
fi

echo ""
echo "=== Despliegue completado ==="
echo "Para ejecutar:"
echo "  cd $(pwd) && source .venv/bin/activate && python3 src/docai_platform.py"
echo ""
echo "O con un archivo directamente:"
echo "  python3 src/docai_platform.py --process input/test_document.docx"
echo ""
