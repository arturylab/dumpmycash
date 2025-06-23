#!/bin/bash

# Script para ejecutar pruebas E2E de autenticación con Selenium
# Este script ejecuta las pruebas de Selenium para verificar la funcionalidad de login y registro

echo "🚀 Ejecutando pruebas E2E de autenticación con Selenium..."
echo "=================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar que las dependencias estén instaladas
echo "🔍 Verificando dependencias..."
python -c "import selenium, webdriver_manager" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Dependencias faltantes. Instalando..."
    pip install selenium webdriver-manager
fi

echo "✅ Dependencias verificadas"
echo ""

# Ejecutar pruebas específicas con descripciones
echo "🧪 Ejecutando pruebas de carga de página..."
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_login_page_loads -v

echo ""
echo "🧪 Ejecutando pruebas de login..."
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_login -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_failed_login_invalid_credentials -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_failed_login_empty_fields -v

echo ""
echo "🧪 Ejecutando pruebas de registro..."
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_register_modal_opens -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_registration_via_modal -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_registration_validation_errors -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_duplicate_registration -v

echo ""
echo "🧪 Ejecutando pruebas de funcionalidades adicionales..."
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_remember_me_functionality -v
python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_password_visibility_toggle -v

echo ""
echo "🎯 Ejecutando TODAS las pruebas E2E de autenticación..."
echo "=================================================="
python -m pytest tests/e2e/test_auth.py -v --tb=short

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Todas las pruebas E2E de autenticación pasaron correctamente!"
    echo "🎉 La funcionalidad de login y registro está funcionando como esperado"
else
    echo ""
    echo "❌ Algunas pruebas fallaron. Revisa los detalles arriba."
    exit 1
fi

echo ""
echo "📊 Resumen de cobertura de pruebas:"
echo "- ✅ Carga de página de login"
echo "- ✅ Login exitoso y fallido"
echo "- ✅ Validación de campos de login"
echo "- ✅ Apertura y funcionalidad del modal de registro"
echo "- ✅ Registro exitoso y validación de errores"
echo "- ✅ Manejo de usuarios duplicados"
echo "- ✅ Funcionalidad de 'recordarme'"
echo "- ✅ Toggle de visibilidad de contraseña"
echo ""
echo "🔧 Configuración utilizada:"
echo "- Chrome en modo headless"
echo "- Base de datos de prueba aislada (SQLite)"
echo "- Servidor Flask en puerto dinámico"
echo "- WebDriver gestionado automáticamente"
echo ""
echo "📝 Para más información, consulta tests/e2e/README.md"
