# Reporte de Mejoras y Correcciones (Parte 2) — BookTracker

**Fecha:** 2026-10-29  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12)  
**Alcance:** Diagnóstico profundo de fallo en Google Books (HTTP 429), implementación de selector interactivo de libros en tiempo real, autocompletado avanzado de metadatos, soporte de notas personales del lector y arquitectura con fallback a Open Library.

---

## Índice

1. [Diagnóstico de la falla de portadas: ¿Por qué no aparecían? (HTTP 429 Quota Exceeded)](#1-diagnóstico-de-la-falla-de-portadas-por-qué-no-aparecían-http-429-quota-exceeded)
2. [¿Es necesario tener una cuenta / API Key de Google Books?](#2-es-necesario-tener-una-cuenta--api-key-de-google-books)
3. [Nuevos campos en el Modelo Book (Migración 0003)](#3-nuevos-campos-en-el-modelo-book-migración-0003)
4. [Endpoint AJAX y Buscador Predictivo en Tiempo Real](#4-endpoint-ajax-y-buscador-predictivo-en-tiempo-real)
5. [Arquitectura con Fallback Automático: Google Books + Open Library](#5-arquitectura-con-fallback-automático-google-books--open-library)
6. [Interfaz Enriquecida: Ficha Técnica, Badges y Notas del Usuario](#6-interfaz-enriquecida-ficha-técnica-badges-y-notas-del-usuario)
7. [Resumen de Archivos Modificados y Creados](#7-resumen-de-archivos-modificados-y-creados)
8. [Guía de Verificación y Uso](#8-guía-de-verificación-y-uso)

---

## 1. Diagnóstico de la falla de portadas: ¿Por qué no aparecían? (HTTP 429 Quota Exceeded)

### Causa exacta descubierta
Al inspeccionar las peticiones directas desde Python a la API de Google Books (`https://www.googleapis.com/books/v1/volumes?q=...`), se descubrió la respuesta exacta que Google estaba devolviendo al servidor:

```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'books.googleapis.com' for consumer 'project_number:624717413613'.",
    "status": "RESOURCE_EXHAUSTED",
    "details": [
      {
        "quota_limit_value": "0",
        "quota_limit": "defaultPerDayPerProject"
      }
    ]
  }
}
```

### Explicación técnica
1. **El pool anónimo de Google está bloqueado:** Cuando se realizan peticiones a `books.googleapis.com` sin una clave de API (`key=...`), Google agrupa todas las peticiones anónimas del mundo bajo un mismo proyecto compartido (`project_number:624717413613`). Google ha fijado el límite de ese pool en **0 consultas por día** (`quota_limit_value: 0`).
2. **Efecto en la aplicación anterior:** La función `create_book` intentaba consultar la API de Google Books de forma anónima, recibía un código **HTTP 429**, `response.json()` no contenía la clave `'items'`, por lo que la condición `if 'items' in response.json():` evaluaba como falso y el libro se guardaba sin portada ni metadatos de forma completamente silenciosa.

---

## 2. ¿Es necesario tener una cuenta / API Key de Google Books?

### Respuesta: **No es obligatorio, pero es recomendado si deseas usar la base de datos oficial de Google Books.**

Gracias a la solución implementada en este reporte:
- **Sin cuenta ni API Key:** La aplicación funciona al **100% de inmediato**. Si Google Books rechaza la consulta por cuota anónima (HTTP 429), el sistema activa automáticamente un **fallback a Open Library API** (el catálogo abierto más grande de Internet), descargando la portada oficial, número total de páginas exacto, autor, editorial e ISBN sin requerir registro ni tarjeta de crédito.
- **Con cuenta / API Key gratuita de Google (Opcional):** Si quieres usar directamente los servidores de Google Books con reseñas y valoraciones:
  1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
  2. Crea un proyecto (es 100% gratuito).
  3. Ve a **APIs y Servicios** > **Biblioteca**, busca **Books API** y presiona **Habilitar**.
  4. Ve a **Credenciales** > **Crear Credenciales** > **Clave de API (API Key)**.
  5. En tu terminal o en tu entorno, define la variable `GOOGLE_BOOKS_API_KEY="tu_clave_aqui"` o colócala en `BookTracker/settings.py`. La app la detectará automáticamente.

---

## 3. Nuevos campos en el Modelo Book (Migración 0003)

Para soportar toda la información de la **Opción 2**, se extendió el modelo `Book` en `books/models.py`:

| Campo nuevo | Tipo | Propósito |
|---|---|---|
| `category` | `CharField(200)` | Géneros literarios (ej. *Ficción, Filosofía, Novela*) |
| `isbn` | `CharField(20)` | Código ISBN-10 o ISBN-13 oficial |
| `publisher` | `CharField(200)` | Editorial del libro (ej. *Salamandra, Planeta*) |
| `published_date` | `CharField(20)` | Año o fecha de publicación original |
| `average_rating` | `FloatField` | Puntuación promedio de lectores (1 a 5 estrellas) |
| `ratings_count` | `IntegerField` | Número de votos de lectores |
| `preview_link` | `URLField(500)` | Enlace oficial para hojear el libro en línea |
| `user_notes` | `TextField` | **Notas personales y reseñas del usuario** sobre su lectura |

### Migración aplicada
Se generó y aplicó con éxito la migración `0003`:
```powershell
python manage.py makemigrations
# Generó: books/migrations/0003_book_average_rating_book_category_book_isbn_and_more.py
python manage.py migrate
# Aplicó: books.0003_book_average_rating_book_category_book_isbn_and_more... OK
```

---

## 4. Endpoint AJAX y Buscador Predictivo en Tiempo Real

Se creó un nuevo endpoint en el backend:
- **Ruta:** `/api/search-books/?q=<termino>`
- **Vista:** `search_google_books(request)`
- **Función:** Recibe la búsqueda del usuario (título o autor), consulta los catálogos y devuelve un arreglo JSON con hasta 5 opciones detalladas conteniendo:
  - Título y autor(es).
  - Portada en miniatura.
  - Total de páginas de la edición.
  - Género / Categorías.
  - Editorial y año.
  - Calificación con estrellas.

### Comportamiento en la interfaz (`create_book.html`)
1. **Debounce automático:** Al teclear en el campo de búsqueda, tras 500 ms de inactividad o al pulsar *Enter* / botón *Buscar*, se realiza la búsqueda sin recargar la página.
2. **Tarjetas interactivas:** Se muestran las portadas y datos de las ediciones encontradas.
3. **Selección con un clic:** Al hacer clic en una edición:
   - Los campos **Título**, **Autor** y **Páginas Totales** se autocompletan instantáneamente en el formulario.
   - Aparece un cuadro de **Previsualización de Portada y Metadatos** con botones para quitar la selección si se desea.
   - Campos ocultos (`hidden inputs`) almacenan la URL de la portada elegida, descripción y ficha técnica para que al enviar el formulario se guarden directamente en la base de datos sin llamadas repetidas.

---

## 5. Arquitectura con Fallback Automático: Google Books + Open Library

Para evitar que una caída o límite de cuota bloquee la aplicación, se implementó en `books/views.py` la función `_fetch_google_books`:

```
               [ Usuario busca un libro ]
                           │
             ¿Hay API Key de Google Books?
             ┌─────────────┴─────────────┐
             ▼                           ▼
        (Con API Key)             (Sin API Key)
   Consulta Google Books      Intenta Google Books
             │                           │
    ¿Éxito (HTTP 200)?          ¿Error o HTTP 429?
      ┌──────┴──────┐                    │
      ▼             ▼                    ▼
   [Usar Datos   [Fallback] ──────► [Consulta Open Library API]
  Google Books]                          │
                                ¿Éxito (HTTP 200)?
                                  ┌──────┴──────┐
                                  ▼             ▼
                             [Usar Datos    [Creación Manual
                            Open Library]     sin Portada]
```

Además, la descarga de la imagen física de portada (`_download_and_save_cover`) incluye:
- Cabecera `User-Agent` de navegador para evitar rechazos HTTP 403 por protección anti-scraping.
- Detección automática del formato de imagen (`.jpg` o `.png`).
- Guardado en la carpeta `media/covers/` y asignación al campo `cover` del modelo `Book`.

---

## 6. Interfaz Enriquecida: Ficha Técnica, Badges y Notas del Usuario

### A. Vista de Detalle (`book_detail.html`)
- **Ficha Técnica Oficial:** Muestra género con badge de color, editorial, fecha de publicación, ISBN formateado y calificación con estrellas.
- **Enlace a Muestra:** Botón directo *"📖 Ver muestra en Google Books"* (o enlace web del libro) para explorar páginas de muestra oficiales.
- **Sinopsis Editorial:** Sección destacada con la sinopsis oficial del libro.
- **Notas Personales del Usuario:** Sección dedicada para redactar notas de lectura, citas textuales o resumen personal mediante el campo `user_notes` en el formulario de edición.

### B. Vista de Biblioteca (`books.html`)
- Las tarjetas de los libros ahora exhiben badges visuales con:
  - Género o categoría principal.
  - Calificación promedio (ej. `⭐ 4.5`).
  - Barra de progreso porcentual dinámica.

---

## 7. Resumen de Archivos Modificados y Creados

| Archivo | Tipo de Cambio | Detalle |
|---|---|---|
| [`books/models.py`](books/models.py) | Modificado | Campos `category`, `isbn`, `publisher`, `published_date`, `average_rating`, `ratings_count`, `preview_link`, `user_notes` y longitudes ampliadas. |
| [`books/forms.py`](books/forms.py) | Modificado | Inclusión del campo `user_notes` con widget `Textarea` estilizado. |
| [`BookTracker/settings.py`](BookTracker/settings.py) | Modificado | Variable `GOOGLE_BOOKS_API_KEY` opcional con lectura de variables de entorno. |
| [`BookTracker/urls.py`](BookTracker/urls.py) | Modificado | Registro de la ruta `/api/search-books/`. |
| [`books/views.py`](books/views.py) | Modificado | Funciones `_fetch_google_books`, `search_google_books`, `_download_and_save_cover` y enriquecimiento robusto en `create_book`. |
| [`books/templates/create_book.html`](books/templates/create_book.html) | Reescrito | Buscador interactivo AJAX, previsualización de portada, autocompletado y campos ocultos de metadatos. |
| [`books/templates/book_detail.html`](books/templates/book_detail.html) | Reescrito | Muestra de sinopsis, ISBN, editorial, calificación, enlace de vista previa y cuadro de notas personales. |
| [`books/templates/books.html`](books/templates/books.html) | Modificado | Badges de género y calificación en tarjetas de libros. |
| [`books/migrations/0003_*.py`](books/migrations/0003_book_average_rating_book_category_book_isbn_and_more.py) | Creado | Migración de esquema aplicada en `db.sqlite3`. |
| [`BUGFIX_REPORT2.md`](BUGFIX_REPORT2.md) | Creado | Este reporte detallado de cambios y diagnóstico. |

---

## 8. Guía de Verificación y Uso

Para probar las nuevas capacidades interactivas en tu navegador:

1. Asegúrate de tener corriendo el servidor:
   ```powershell
   python manage.py runserver
   ```
2. Entra a **Create Book** (`http://127.0.0.1:8000/books/create/`).
3. En la caja superior de **"Buscar Libro en Línea"**, escribe el nombre de un libro (ej. *El principito*, *Cien años de soledad*, *Clean Code*).
4. Verás la lista de resultados con sus portadas oficiales y datos.
5. Haz clic en una edición:
   - Se completará automáticamente el título, autor y **total de páginas**.
   - Aparecerá la previsualización de la portada arriba del formulario.
6. Asigna tu meta o páginas leídas y presiona **Crear Libro**.
7. En tu biblioteca verás la portada oficial descargada en tu servidor y los badges de género/calificación.
8. Al entrar al libro, verás su ficha técnica completa, sinopsis y podrás escribir tus notas personales en el nuevo campo de notas.

