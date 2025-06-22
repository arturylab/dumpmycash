#!/bin/bash

# Script simple para ejecutar todas las pruebas E2E de autenticación
echo "🧪 Ejecutando pruebas E2E de autenticación..."

# Verificar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar todas las pruebas
python -m pytest tests/e2e/test_auth.py -v

echo "✅ Pruebas completadas"
