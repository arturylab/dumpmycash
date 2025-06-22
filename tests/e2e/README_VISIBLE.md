# 🌟 Pruebas E2E en Modo Visible

## Descripción

Esta configuración te permite ejecutar las pruebas End-to-End (E2E) con **Chrome en modo visible**, para que puedas observar en tiempo real cómo Selenium interactúa con tu aplicación web.

## ¿Por qué modo visible?

- **👀 Observación en tiempo real**: Ves exactamente lo que hace el navegador
- **🐛 Depuración fácil**: Detecta problemas visuales o de timing
- **📚 Aprendizaje**: Entiende cómo funcionan las pruebas E2E
- **✅ Verificación visual**: Confirma que la UI se comporta correctamente

## Configuración actual

La configuración del driver en `conftest.py` está optimizada para modo visible:

```python
# Modo visible (navegador se muestra)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # ❌ Deshabilitado
chrome_options.add_argument("--start-maximized")  # ✅ Ventana maximizada
chrome_options.add_experimental_option("detach", True)  # ✅ Mantener abierto para debug
```

## Cómo ejecutar

### Opción 1: Script interactivo (Recomendado)
```bash
./run_e2e_visible.sh
```

Este script te permite elegir qué pruebas ejecutar:
1. **Solo carga de página** (rápido, 10 segundos)
2. **Login exitoso** (recomendado, muestra funcionalidad completa)
3. **Pruebas de registro** (modal y validación)
4. **Todas las pruebas** (completo pero largo)
5. **Prueba específica** (manual)

### Opción 2: Comando directo
```bash
# Una prueba específica
pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_successful_login -v -s

# Todas las pruebas
pytest tests/e2e/test_auth.py -v -s
```

## Qué observarás

### 1. Carga de página (`test_login_page_loads`)
- ✅ Chrome se abre y navega a la página de login
- ✅ Verifica elementos de la interfaz
- ✅ Confirma que el logo y formularios están presentes

### 2. Login exitoso (`test_successful_login`)
- ✅ Llena el formulario de login automáticamente
- ✅ Hace clic en "Log in"
- ✅ Redirige al dashboard
- ✅ Verifica que el usuario está logueado

### 3. Registro en modal (`test_successful_registration_via_modal`)
- ✅ Abre el modal de registro
- ✅ Llena el formulario de registro
- ✅ Submite el formulario
- ✅ Verifica registro exitoso haciendo login

### 4. Validación de errores (`test_registration_validation_errors`)
- ✅ Intenta registro con contraseña débil
- ✅ Muestra mensajes de validación
- ✅ Verifica que la validación funciona

## Pausas agregadas para observación

Las pruebas incluyen pausas estratégicas para mejor observación:

```python
def test_login_page_loads(self, driver, live_server_flask):
    driver.get(f"{live_server_flask}/login")
    time.sleep(2)  # ⏸️ Pausa para observar carga
    
    # ... verificaciones ...
    
    time.sleep(1)  # ⏸️ Pausa para observar resultado
```

## Consejos para observación

### 🚀 Para ver mejor las interacciones:
1. **Ejecuta una prueba a la vez** para enfocar tu atención
2. **Usa el script interactivo** para elegir qué observar
3. **Aumenta las pausas** en `test_auth.py` si necesitas más tiempo

### 🔧 Para depuración:
```python
# Agregar pausas adicionales
time.sleep(5)  # Pausa de 5 segundos

# Capturar pantalla para debug
driver.save_screenshot("debug.png")

# Imprimir información de debug
print(f"URL actual: {driver.current_url}")
print(f"Título: {driver.title}")
```

### 🏃‍♂️ Para ejecución rápida:
```bash
# Solo verificar que funciona
pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_login_page_loads -v
```

## Diferencias con modo headless

| Característica | Modo Visible | Modo Headless |
|----------------|-------------|---------------|
| **Velocidad** | ⚡ Más lento | ⚡⚡⚡ Muy rápido |
| **Observación** | ✅ Completa | ❌ No visible |
| **Depuración** | ✅ Fácil | 🔧 Requiere logs |
| **CI/CD** | ❌ No apto | ✅ Ideal |
| **Aprendizaje** | ✅ Excelente | ❌ Limitado |

## Solución de problemas

### Chrome no se abre
```bash
# Verificar que Chrome está instalado
google-chrome --version

# O en macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

### Pruebas muy lentas
- Reduce las pausas en `test_auth.py`
- Ejecuta pruebas individuales en lugar del conjunto completo

### Ventana muy pequeña
La configuración incluye `--start-maximized` para ventana completa

### Navegador se cierra muy rápido
```python
# Agregar al final de la prueba para mantener abierto
input("Presiona Enter para cerrar el navegador...")
```

## Cambiar de vuelta a headless

Si quieres volver al modo headless, descomenta esta línea en `conftest.py`:

```python
chrome_options.add_argument("--headless")  # Descomentar para modo headless
```

## Comandos útiles

```bash
# Ejecutar con más verbose
pytest tests/e2e/test_auth.py -v -s --tb=short

# Ejecutar solo pruebas que fallan
pytest tests/e2e/test_auth.py --lf

# Ejecutar con output detallado
pytest tests/e2e/test_auth.py -v -s --capture=no
```

¡Disfruta observando tus pruebas E2E en acción! 🎬

## 🎉 Estado Actual - COMPLETADO

### ✅ Todas las Pruebas de Autenticación son Completamente Visibles

**10/10 pruebas pasan exitosamente** con pausas de observación implementadas:

1. **test_login_page_loads** ✅ - Carga de página con pausas
2. **test_successful_login** ✅ - Login exitoso con pausas por campo
3. **test_failed_login_invalid_credentials** ✅ - Login fallido con pausas de error
4. **test_failed_login_empty_fields** ✅ - Validación campos vacíos con pausas
5. **test_register_modal_opens** ✅ - Apertura modal con pausas completas
6. **test_successful_registration_via_modal** ✅ - Registro exitoso con pausas detalladas
7. **test_registration_validation_errors** ✅ - Validación contraseña débil con pausas
8. **test_duplicate_registration** ✅ - Manejo duplicados con pausas de error
9. **test_remember_me_functionality** ✅ - Funcionalidad "Recordarme" con pausas
10. **test_password_visibility_toggle** ✅ - Toggle visibilidad con pausas por cambio

### 🕐 Pausas Implementadas

**Cada prueba incluye pausas estratégicas para observación completa:**

- **1 segundo**: Carga inicial de páginas
- **0.5 segundos**: Entre cada entrada de datos en campos
- **1-2 segundos**: Apertura y cierre de modales
- **2-3 segundos**: Observación de validaciones y mensajes de error/éxito
- **2 segundos**: Observación de redirecciones y resultados finales
- **0.5-1 segundo**: Cambios de estado (toggles, checkboxes)

### 🚀 Listo para Uso

El sistema de pruebas E2E visibles está **completamente implementado y funcionando**. Puedes:

- Ejecutar `./run_e2e_visible.sh` para el menú interactivo
- Observar cada paso de autenticación en tiempo real
- Depurar problemas visualmente
- Demostrar funcionalidad paso a paso
- Desarrollar nuevas pruebas usando el patrón establecido

**Total tiempo promedio de ejecución visible**: ~2.5 minutos para todas las pruebas
