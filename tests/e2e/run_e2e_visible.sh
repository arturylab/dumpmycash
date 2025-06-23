#!/bin/bash

# Script para ejecutar pruebas E2E en modo VISIBLE (navegador Chrome se muestra)
echo "🌟 Ejecutando pruebas E2E en modo VISIBLE con Chrome..."
echo "=================================================="
echo "ℹ️  Podrás ver el navegador Chrome ejecutando las pruebas en tiempo real"
echo ""

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

# Preguntar qué pruebas ejecutar
echo "¿Qué pruebas quieres ejecutar en modo visible?"
echo "1) Solo carga de página (rápido)"
echo "2) Login exitoso (recomendado para ver la funcionalidad)"
echo "3) Pruebas de registro (modal y validación)" 
echo "4) Todas las pruebas (completo pero largo)"
echo "5) Prueba específica (manual)"
echo ""
read -p "Elige una opción (1-5): " choice

case $choice in
    1)
        echo "🧪 Ejecutando prueba de carga de página..."
        python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_login_page_loads -v -s
        ;;
    2)
        echo "🧪 Ejecutando prueba de login exitoso..."
        python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_login -v -s
        ;;
    3)
        echo "🧪 Ejecutando pruebas de registro..."
        python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_register_modal_opens tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_registration_via_modal -v -s
        ;;
    4)
        echo "🧪 Ejecutando TODAS las pruebas..."
        echo "⚠️  Esto tomará varios minutos y abrirá múltiples ventanas de Chrome"
        read -p "¿Continuar? (y/n): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            python -m pytest tests/e2e/test_auth.py -v -s
        else
            echo "❌ Cancelado por el usuario"
            exit 0
        fi
        ;;
    5)
        echo "Pruebas disponibles:"
        echo "- test_login_page_loads"
        echo "- test_successful_login"
        echo "- test_failed_login_invalid_credentials"
        echo "- test_failed_login_empty_fields"
        echo "- test_register_modal_opens"
        echo "- test_successful_registration_via_modal"
        echo "- test_registration_validation_errors"
        echo "- test_duplicate_registration"
        echo "- test_remember_me_functionality"
        echo "- test_password_visibility_toggle"
        echo ""
        read -p "Introduce el nombre de la prueba: " test_name
        echo "🧪 Ejecutando prueba: $test_name"
        python -m pytest "tests/e2e/test_auth.py::TestAuthenticationSelenium::$test_name" -v -s
        ;;
    *)
        echo "❌ Opción inválida. Ejecutando prueba por defecto (login exitoso)..."
        python -m pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_login -v -s
        ;;
esac

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Prueba(s) completada(s) exitosamente!"
    echo "🎉 Pudiste observar la ejecución en tiempo real en Chrome"
else
    echo ""
    echo "❌ Algunas pruebas fallaron. Revisa los detalles arriba."
    exit 1
fi

echo ""
echo "📋 Información adicional:"
echo "- Las pruebas se ejecutaron en modo VISIBLE"
echo "- Chrome se abrió y mostró la interacción real con la aplicación"
echo "- La base de datos de prueba se limpió automáticamente"
echo "- El servidor de prueba se ejecutó en puerto temporal"
echo ""
echo "💡 Consejos:"
echo "- Para modo headless (invisible), usa: ./test_auth_e2e.sh"
echo "- Para depuración detallada, modifica las pausas en test_auth.py"
echo "- Para ver logs del servidor, agrega -s al comando pytest"
