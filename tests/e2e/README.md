# Selenium E2E Tests for Authentication

## Descripción

Este directorio contiene pruebas end-to-end (E2E) utilizando Selenium para verificar la funcionalidad de autenticación de la aplicación DumpMyCash. Las pruebas se ejecutan en Chrome en modo headless y utilizan una base de datos de prueba aislada.

## Configuración

### Dependencias necesarias

Las siguientes dependencias deben estar instaladas:
- `selenium`: WebDriver para automatización del navegador
- `webdriver-manager`: Gestión automática del driver de Chrome

```bash
pip install selenium webdriver-manager
```

### Estructura de archivos

- `conftest.py`: Configuración de fixtures y servidor de pruebas
- `test_auth.py`: Pruebas de autenticación (login y registro)

## Configuración de pruebas

### Base de datos de prueba

Las pruebas utilizan una base de datos SQLite separada (`test_selenium.db`) para aislar los datos de prueba del entorno principal. Esta base de datos se crea y limpia automáticamente para cada sesión de pruebas.

### Servidor de prueba

Un servidor Flask se ejecuta en un puerto dinámico durante las pruebas, utilizando threading para evitar conflictos de serialización. El servidor se inicia automáticamente y se limpia al finalizar las pruebas.

### Configuración de Chrome

Chrome se ejecuta en modo headless con las siguientes opciones:
- `--headless`: Ejecución sin interfaz gráfica
- `--no-sandbox`: Necesario para algunos entornos CI/CD
- `--disable-dev-shm-usage`: Evita problemas de memoria compartida
- `--disable-gpu`: Deshabilita aceleración de GPU
- `--window-size=1920,1080`: Tamaño de ventana consistente

## Pruebas implementadas

### Pruebas de Login

1. **test_login_page_loads**: Verifica que la página de login carga correctamente
2. **test_successful_login**: Prueba login exitoso con credenciales válidas
3. **test_failed_login_invalid_credentials**: Login fallido con credenciales inválidas
4. **test_failed_login_empty_fields**: Validación de campos vacíos
5. **test_remember_me_functionality**: Funcionalidad del checkbox "recordarme"

### Pruebas de Registro

6. **test_register_modal_opens**: Apertura del modal de registro
7. **test_successful_registration_via_modal**: Registro exitoso a través del modal
8. **test_registration_validation_errors**: Validación de errores de registro
9. **test_duplicate_registration**: Manejo de registros duplicados
10. **test_password_visibility_toggle**: Toggle de visibilidad de contraseña

## Fixtures disponibles

### `selenium_app`
Aplicación Flask configurada para pruebas con base de datos de prueba.

### `live_server_flask`
Servidor Flask en vivo que se ejecuta en un puerto dinámico.

### `selenium_db`
Base de datos de prueba que se limpia entre cada prueba.

### `driver`
Instancia de ChromeDriver configurada en modo headless.

### `auth_helper`
Clase helper con métodos útiles para pruebas de autenticación:
- `create_user()`: Crear usuario directamente en la base de datos
- `navigate_to_login()`: Navegar a la página de login
- `is_logged_in()`: Verificar si el usuario está logueado
- `get_flash_messages()`: Obtener mensajes flash de la página

## Ejecución de pruebas

### Ejecutar todas las pruebas de autenticación E2E
```bash
pytest tests/e2e/test_auth.py -v
```

### Ejecutar una prueba específica
```bash
pytest tests/e2e/test_auth.py::TestAuthenticationSelenium::test_login_page_loads -v
```

### Ejecutar pruebas con más detalle
```bash
pytest tests/e2e/test_auth.py -v -s
```

## Troubleshooting

### Problemas comunes

1. **ChromeDriver no encontrado**: El webdriver-manager se encarga automáticamente de descargar la versión correcta de ChromeDriver.

2. **Elemento no clickeable**: Las pruebas incluyen esperas explícitas y fallbacks de JavaScript para elementos que pueden estar interceptados.

3. **Timeouts**: Las pruebas tienen timeouts configurados apropiadamente, pero pueden necesitar ajustes en entornos más lentos.

4. **Puerto ocupado**: El servidor de prueba encuentra automáticamente un puerto libre.

### Depuración

Para depurar pruebas, puedes:
1. Remover el argumento `--headless` del fixture `driver` en `conftest.py`
2. Agregar `time.sleep()` en puntos críticos
3. Usar `driver.save_screenshot('debug.png')` para capturar el estado de la página

## Integración con CI/CD

Las pruebas están configuradas para ejecutarse en entornos headless y son compatibles con sistemas CI/CD. Asegúrate de que Chrome esté instalado en el entorno de ejecución.

## Mantenimiento

Al agregar nuevas características de autenticación:
1. Agregar pruebas correspondientes en `test_auth.py`
2. Actualizar fixtures si es necesario
3. Documentar nuevas funcionalidades en este README
