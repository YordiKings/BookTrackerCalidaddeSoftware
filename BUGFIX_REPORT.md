# Reporte de Bugs y Correcciones — BookTracker

**Fecha:** 2026-10-29  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12)  
**Alcance:** Bugs encontrados y corregidos en sesión de desarrollo activa

---

## Índice

1. [Bug #1 — Migración faltante para la API de Google Books](#bug-1--migración-faltante-para-la-api-de-google-books)
2. [Bug #2 — `AttributeError: NoneType` al actualizar un libro (Update Book)](#bug-2--attributeerror-nonetype-al-actualizar-un-libro-update-book)
3. [Bug #3 — Exception handling insuficiente en `create_book`](#bug-3--exception-handling-insuficiente-en-create_book)
4. [Resumen de cambios](#resumen-de-cambios)
5. [Estado actual del proyecto](#estado-actual-del-proyecto)

---

## Bug #1 — Migración faltante para la API de Google Books

### Descripción
La integración con la **API de Google Books** está completamente programada en `books/views.py`, pero los campos que debía guardar en base de datos (`cover`, `pdf_file`, `description`, `google_books_id`) no existían en la tabla `books_book` de SQLite.

### Causa raíz
El archivo de migración `0002` que agrega los nuevos campos al modelo `Book` había sido escrito en el modelo (`books/models.py`) pero **nunca fue generado ni aplicado** (`makemigrations` / `migrate`). La carpeta `books/migrations/` solo contenía `0001_initial.py`, por lo que la base de datos en ejecución era inconsistente con el modelo en código.

### Síntoma observado
Al crear un libro sin portada, la API era llamada, la portada se descargaba en memoria, pero al intentar guardarla con `.cover.save(...)` o acceder al campo `google_books_id`, Django lanzaba un `OperationalError: no such column: books_book.cover` silenciado internamente. El libro se registraba sin metadatos ni portada.

### Solución aplicada
Se ejecutaron los comandos de migración para sincronizar el esquema:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Esto generó y aplicó el archivo:
```
books/migrations/0002_book_cover_book_description_book_google_books_id_and_more.py
```

**Campos añadidos a la tabla `books_book`:**
| Campo | Tipo | Descripción |
|---|---|---|
| `cover` | `ImageField` | Portada del libro (subida manual o descargada de Google Books) |
| `pdf_file` | `FileField` | Archivo PDF del libro |
| `description` | `TextField` | Sinopsis obtenida de Google Books |
| `google_books_id` | `CharField(50)` | ID único del libro en Google Books |

### Archivos afectados
- `books/migrations/0002_book_cover_book_description_book_google_books_id_and_more.py` *(generado)*
- `db.sqlite3` *(migración aplicada)*

---

## Bug #2 — `AttributeError: NoneType` al actualizar un libro (Update Book)

### Descripción
Al presionar el botón **Update Book** en la página de detalle de un libro (`/books/<id>/`), la aplicación devolvía un **Internal Server Error 500** y no guardaba ningún cambio.

### Causa raíz
En `books/views.py`, dentro de la función `book_detail`, al momento de comparar el mes del último registro de lectura con el mes actual, se accedía al atributo `.month` del campo `date_most_pages_read` sin verificar previamente si ese campo no era `None`.

El campo `date_most_pages_read` en el modelo `Profile` es nullable (`null=True, blank=True`). Para un usuario recién registrado que actualiza un libro por primera vez, este campo nunca ha sido inicializado y su valor es `None`.

### Error exacto en terminal
```
Internal Server Error: /books/17/
Traceback (most recent call last):
  ...
  File "books/views.py", line 153, in book_detail
    if profile.date_most_pages_read.month != current_month:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'month'
```

### Código antes del fix

```python
# books/views.py  línea ~153 (ANTES - con bug)
if profile.date_most_pages_read.month != current_month:
    profile.pages_this_month = 0
```

### Código después del fix

```python
# books/views.py  línea ~153 (DESPUÉS - corregido)
if profile.date_most_pages_read and profile.date_most_pages_read.month != current_month:
    profile.pages_this_month = 0
```

### Explicación del fix
Se agrega un **guard clause** con `and` en cortocircuito de Python: primero evalúa si el campo es truthy (es decir, que no sea `None`). Solo si existe un valor, continúa comparando el mes. Esto garantiza que un usuario nuevo o uno que nunca haya completado una sesión de lectura pueda actualizar sus libros sin errores.

### Archivos afectados
- [`books/views.py`](books/views.py) — función `book_detail`, sección de actualización de métricas del perfil

---

## Bug #3 — Exception handling insuficiente en `create_book`

### Descripción
El bloque `try/except` que envuelve la lógica de creación de un libro en la función `create_book` solo capturaba `ValueError`. Si la llamada a la **API de Google Books** fallaba con un error de red (`ConnectionError`, `Timeout`, `RequestException`), la excepción no era capturada, el libro **no se guardaba**, y el usuario veía un error genérico 500 sin mensajes útiles.

### Dos correcciones aplicadas

#### 3a. Aislamiento de la llamada a Google Books en su propio try/except

La lógica de Google Books se envolvió en un `try/except Exception` interno, independiente del bloque principal de guardado del libro. Esto garantiza que **si la API falla, el libro igual se guarda** con los datos que el usuario ingresó manualmente.

```python
# ANTES (código frágil: si la API falla, el libro no se guarda)
try:
    new_book = form.save(commit=False)
    response = requests.get(...)            # <-- Si esto lanza, salta al except ValueError
    ...
    new_book.save()
except ValueError:
    return render(request, 'create_book.html', {'error': '...'})
```

```python
# DESPUÉS (robusto: la API se intenta, pero su fallo no afecta el guardado)
try:
    new_book = form.save(commit=False)
    
    # Bloque aislado de la API de Google Books
    try:
        gb_response = requests.get(..., timeout=5)
        if gb_response.status_code == 200 and 'items' in gb_response.json():
            ...
    except Exception:
        # Si falla la red/timeout/API, el libro se guarda igual sin portada
        pass
    
    new_book.save()   # Siempre se ejecuta
    ...
except (ValueError, Exception) as e:
    return render(request, 'create_book.html', {'error': '...'})
```

#### 3b. Timeout añadido a las peticiones HTTP

Se añadió `timeout=5` a ambas llamadas HTTP (`requests.get`) para que la aplicación no quede colgada indefinidamente si la API de Google Books no responde:

```python
gb_response = requests.get(url, timeout=5)      # búsqueda del libro
img_response = requests.get(cover_url, timeout=5)  # descarga de portada
```

### Archivos afectados
- [`books/views.py`](books/views.py) — función `create_book`, sección de integración con Google Books

---

## Resumen de cambios

| # | Bug | Archivo | Línea(s) | Severidad |
|---|---|---|---|---|
| 1 | Migración faltante — campos de Google Books inexistentes en BD | `books/migrations/0002_*` | — | 🔴 **Crítico** |
| 2 | `AttributeError: NoneType` en `.month` al actualizar libro | `books/views.py` | ~153 | 🔴 **Crítico** |
| 3a | `create_book` no aísla errores de la API de Google Books | `books/views.py` | ~72–99 | 🟠 **Alto** |
| 3b | Sin timeout en peticiones HTTP a Google Books | `books/views.py` | ~77, ~90 | 🟡 **Medio** |

---

## Estado actual del proyecto

### ✅ Funcionando correctamente

- **Portadas:** Se muestran en tarjetas (`books.html`) y en detalle (`book_detail.html`), tanto las subidas manualmente como las descargadas de Google Books.
- **API de Google Books:** Se consulta automáticamente al crear un libro. Descarga la sinopsis (`description`) y la portada oficial si el usuario no subió una. Ahora es resiliente a fallos de red.
- **Actualización de libros (`Update Book`):** Corregido el crash al actualizar por primera vez en un perfil sin historial de lectura.
- **Métricas de perfil:** Se actualizan correctamente el récord diario, el acumulado mensual y el promedio diario de páginas leídas.
- **Base de datos:** Migración `0002` aplicada — todos los campos del modelo `Book` están sincronizados con SQLite.

### ❌ Pendiente de implementar

| Funcionalidad | Estado | Descripción |
|---|---|---|
| **Visor de PDF interactivo** | Pendiente | El `<iframe>` actual solo muestra el PDF estático con el visor nativo del navegador. Falta integrar una librería como **PDF.js** para tener controles dentro de la app. |
| **Sincronización páginas ↔ PDF** | Pendiente | No hay comunicación entre la página en que se encuentra el usuario dentro del PDF y el campo `pages_read` en Django. Requiere implementar un listener de eventos de página en JS + un endpoint AJAX para actualizar el progreso en tiempo real. |

