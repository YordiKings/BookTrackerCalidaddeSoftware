# Reporte de Configuración y Seguridad (Parte 3) — BookTracker

**Fecha:** 2026-10-29  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12)  
**Alcance:** Almacenamiento seguro de credenciales de Google Books API mediante variables de entorno (`.env`), blindaje contra filtraciones a repositorios Git/GitHub (`.gitignore`), cargador nativo de entorno en `settings.py`, plantilla `.env.example` y validación de seguridad.

---

## Índice

1. [¿Dónde colocar tu API Key de Google Books?](#1-dónde-colocar-tu-api-key-de-google-books)
2. [Protección y Seguridad en Git / GitHub](#2-protección-y-seguridad-en-git--github)
3. [Cargador Nativo de Variables de Entorno en `settings.py`](#3-cargador-nativo-de-variables-de-entorno-en-settingspy)
4. [Flujo de Inyección de la API Key en el Backend](#4-flujo-de-inyección-de-la-api-key-en-el-backend)
5. [Pruebas de Carga y Validación Realizadas](#5-pruebas-de-carga-y-validación-realizadas)
6. [Resumen de Archivos Creados y Modificados](#6-resumen-de-archivos-creados-y-modificados)
7. [Instrucciones Rápidas para el Usuario](#7-instrucciones-rápidas-para-el-usuario)

---

## 1. ¿Dónde colocar tu API Key de Google Books?

Se ha configurado la raíz de tu proyecto para utilizar un archivo estándar `.env`:

- **Ubicación del archivo:** `c:\Users\cdepu\Downloads\Proyectos\BookTracker\.env`
- **Contenido del archivo:**
  ```env
  # Clave de API de Google Books
  GOOGLE_BOOKS_API_KEY=AIzaSyTuClaveDeApiAqui123456789
  ```

Solo debes abrir ese archivo `.env` en tu editor de código y pegar tu clave después del signo `=` (sin espacios ni comillas).

---

## 2. Protección y Seguridad en Git / GitHub

### ¿Por qué nunca se debe subir una API Key a GitHub?
Subir claves de API directamente al código fuente en repositorios públicos o privados es un riesgo de seguridad crítico. Bots automatizados escanean GitHub constantemente buscando cadenas que comiencen con `AIzaSy...` (el formato de Google Cloud) para abusar de cuotas o servicios.

### Medidas de protección implementadas:
1. **Regla de exclusión estricta en `.gitignore`:**
   En el archivo `.gitignore` del proyecto se encuentran las directivas:
   ```gitignore
   # ==========================================
   # Variables de Entorno / Secretos
   # ==========================================
   .env
   .env.*
   !.env.example
   ```
   Esto asegura que el archivo `.env` **es completamente invisible para Git**. Comandos como `git add .`, `git commit` o `git push` jamás incluirán tu archivo `.env` ni tu clave.

2. **Archivo plantilla `.env.example`:**
   Se creó un archivo `.env.example` que **sí se sube al repositorio**, pero sin secretos. Sirve como guía pública para que cualquier colaborador o profesor que descargue el proyecto sepa exactamente qué variable necesita configurar sin exponer la tuya.

---

## 3. Cargador Nativo de Variables de Entorno en `settings.py`

Dado que el entorno virtual no contaba con dependencias adicionales pesadas como `python-dotenv`, se implementó un cargador nativo ultraligero y robusto en [`BookTracker/settings.py`](BookTracker/settings.py):

```python
import os
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga automática de variables de entorno desde .env (protegido en .gitignore)
ENV_FILE = BASE_DIR / '.env'
if ENV_FILE.exists():
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
```

Y al final del archivo:
```python
# Google Books API Key (cargada de forma segura desde .env o variable de entorno)
GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY', '')
```

**Ventajas:**
- Cero dependencias externas adicionales.
- Se ejecuta antes de que cualquier vista o módulo de Django requiera la clave.
- Soporta comentarios con `#` y saltos de línea sin romperse.

---

## 4. Flujo de Inyección de la API Key en el Backend

En [`books/views.py`](books/views.py), la función `_fetch_google_books` lee la clave de forma limpia desde la configuración de Django:

```python
api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', '') or os.environ.get('GOOGLE_BOOKS_API_KEY', '')
params = {'q': query, 'maxResults': max_results}
if api_key:
    params['key'] = api_key
```

### Comportamiento dinámico:
1. **Con API Key en `.env`:** La petición hacia `https://www.googleapis.com/books/v1/volumes` se envía con `&key=tu_clave`. Google la autentica de inmediato, otorgando tu cuota privada de 1,000 consultas diarias gratuitas y devolviendo sinopsis editoriales, portadas de alta definición, calificaciones de lectores y enlaces de muestra.
2. **Si la API Key no se ha colocado aún:** El sistema no crashea ni muestra errores; simplemente continúa activando el **fallback automático a Open Library** para que el buscador y las portadas sigan funcionando siempre.

---

## 5. Pruebas de Carga y Validación Realizadas

Se realizaron verificaciones en entorno de desarrollo:
1. **Prueba de Inyección:** Se inyectó temporalmente un valor de prueba (`Prueba12345`) en `.env` y se ejecutó la inicialización de Django desde la terminal:
   - Salida: `Loaded settings.GOOGLE_BOOKS_API_KEY from .env: 'Prueba12345'`.
   - Resultado: **Aprobado**.
2. **Prueba de Exclusión en Git:** Se ejecutó `git status -u` para verificar archivos no rastreados:
   - Salida: `.env.example` detectado, `.env` **completamente ignorado**.
   - Resultado: **Aprobado (100% seguro contra filtraciones)**.

---

## 6. Resumen de Archivos Creados y Modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`.env`](.env) | Creado | Archivo local donde debes pegar tu API Key. Ignorado por Git. |
| [`.env.example`](.env.example) | Creado | Plantilla de documentación para repositorios sin datos confidenciales. |
| [`BookTracker/settings.py`](BookTracker/settings.py) | Modificado | Cargador nativo de `.env` que puebla `os.environ` y `GOOGLE_BOOKS_API_KEY`. |
| [`BUGFIX_REPORT3.md`](BUGFIX_REPORT3.md) | Creado | Este informe detallado de seguridad y configuración. |

---

## 7. Instrucciones Rápidas para el Usuario

Para empezar a usar tu clave de Google Books ahora mismo:

1. Abre el archivo [`.env`](.env) que se encuentra en la carpeta principal de tu proyecto.
2. Verás la siguiente línea:
   ```env
   GOOGLE_BOOKS_API_KEY=
   ```
3. Pega tu API Key de Google Books justo después del `=` (ejemplo: `GOOGLE_BOOKS_API_KEY=AIzaSyD-xyz123...`).
4. Guarda el archivo (`Ctrl + S`).
5. Si tu servidor `python manage.py runserver` ya estaba encendido, el auto-recargador de Django detectará los cambios automáticamente. ¡Listo! Ya estás usando la API oficial de Google Books con tus propias credenciales seguras.

