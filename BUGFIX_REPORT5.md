# Reporte de Visor PDF Interactivo y Sincronización de Lectura (Parte 5) — BookTracker

**Fecha:** 2026-10-30  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12)  
**Alcance:** Sustitución del visor estático por un lector interactivo HTML5 con Mozilla PDF.js, resolución del conflicto entre páginas impresas vs. páginas del PDF digital, endpoint asíncrono de progreso y sincronización en tiempo real con el perfil del usuario.

---

## Índice

1. [Problema previo: Visor estático y ausencia de sincronización](#1-problema-previo-visor-estático-y-ausencia-de-sincronización)
2. [Resolución del conflicto de páginas: Edición Impresa vs. PDF Digital](#2-resolución-del-conflicto-de-páginas-edición-impresa-vs-pdf-digital)
3. [Arquitectura del Visor Interactivo con Mozilla PDF.js](#3-arquitectura-del-visor-interactivo-con-mozilla-pdfjs)
4. [Endpoint AJAX en el Backend: `update_pdf_progress`](#4-endpoint-ajax-en-el-backend-update_pdf_progress)
5. [Controles y Experiencia de Lectura para el Usuario](#5-controles-y-experiencia-de-lectura-para-el-usuario)
6. [Actualización Reactiva en Tiempo Real en la Interfaz](#6-actualización-reactiva-en-tiempo-real-en-la-interfaz)
7. [Pruebas Automatizadas y Validación Empírica](#7-pruebas-automatizadas-y-validación-empírica)
8. [Resumen de Archivos Modificados](#8-resumen-de-archivos-modificados)

---

## 1. Problema previo: Visor estático y ausencia de sincronización

### Diagnóstico técnico
En versiones anteriores, el detalle del libro (`book_detail.html`) utilizaba una etiqueta genérica `<iframe src="{{ book.pdf_file.url }}">`.

Esta aproximación presentaba serias limitaciones:
1. **Aislamiento por Sandbox del Navegador:** Los navegadores ejecutan el visualizador de PDF dentro del `<iframe>` en un contexto restringido (cross-origin / sandbox de plugins). JavaScript no puede escuchar eventos de scroll, clics o cambios de página dentro del visor nativo.
2. **Seguimiento 100% manual y desconectado:** El usuario debía salir del PDF, calcular mentalmente en qué página iba, teclear el número a mano en el formulario de edición y dar clic en *Update Book*.
3. **Incompatibilidad móvil:** Muchos navegadores en smartphones y tablets no soportan la visualización de PDFs dentro de un `<iframe>`, forzando la descarga inmediata del archivo en lugar de mostrarlo en pantalla.

---

## 2. Resolución del conflicto de páginas: Edición Impresa vs. PDF Digital

### El dilema
Un usuario puede buscar un libro como *"El principito"* mediante la API de Google Books, la cual reporta **110 páginas** (correspondientes a la edición física con prólogo e ilustraciones impresas). Sin embargo, el archivo PDF que el usuario sube a la plataforma puede ser una versión digital condensada, un extracto o un PDF formateado a diferente tipografía que cuenta con solo **25 páginas**.

Si el sistema mantuviera las 110 páginas de la API pero el PDF solo llega hasta la página 25:
- Al terminar de leer el PDF, el progreso quedaría estancado en un falso `22% (25/110)`.
- El libro nunca se marcaría como completado automáticamente.
- La tabla de proyección de páginas por día se calcularía con base en páginas inexistentes.

### Regla de resolución implementada: **"El PDF manda sobre la API"**
Se estableció una jerarquía inteligente de fuentes de datos:

```
                           [ Estado del Libro ]
                                    │
                       ¿El usuario subió un archivo PDF?
                       ┌────────────┴────────────┐
                       ▼                         ▼
                     [ SÍ ]                    [ NO ]
            El total de páginas se     Se mantiene el total de
            ajusta al conteo real      páginas de la API para
             del archivo PDF           seguimiento manual
            (pdfDoc.numPages)
```

1. Cuando el visor abre el documento, extrae el número exacto de páginas reales del archivo binario (`pdfDoc.numPages`).
2. Si este número difiere de `book.pages_total`, se envía automáticamente una sincronización al backend para actualizar `pages_total = numPages`.
3. Se muestra una notificación amigable al lector indicando que el total de páginas fue calibrado de acuerdo al documento que está visualizando.

---

## 3. Arquitectura del Visor Interactivo con Mozilla PDF.js

Se integró **Mozilla PDF.js (v3.11.174)** cargado desde CDN oficial, eliminando toda dependencia de plugins del navegador y garantizando renderizado nativo sobre un elemento `<canvas>` de HTML5.

### Flujo de Inicialización y Renderizado:
1. **Configuración del Worker:** Se inicializa `GlobalWorkerOptions.workerSrc` en un subproceso asíncrono para evitar bloquear el hilo principal de la interfaz de usuario.
2. **Carga Asíncrona:** Se ejecuta `pdfjsLib.getDocument(url).promise`.
3. **Reanudación de Sesión:** El visor consulta `book.pages_read`. Si el usuario ya había avanzado hasta la página 8 en una sesión previa, el visor abre automáticamente en la página 8 (o en la 1 si es un libro nuevo).
4. **Renderizado en Canvas:** La función `renderPage(num)` obtiene el viewport con la escala actual y dibuja la página sobre el `<canvas id="pdfCanvas">` aplicando sombreado y bordes suaves.

---

## 4. Endpoint AJAX en el Backend: `update_pdf_progress`

Se implementó una nueva vista en `books/views.py` registrada bajo la URL `/books/<int:book_id>/update-pdf-progress/`:

```python
# books/views.py

@login_required
def update_pdf_progress(request, book_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    book = get_object_or_404(Book, pk=book_id, user=request.user)
    profile = request.user.profile

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST

        current_page = int(payload.get('current_page', 0))
        total_pages = int(payload.get('total_pages', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Datos de página inválidos'}, status=400)

    updated_fields = False

    # 1. Sincronización del total de páginas según el PDF real
    if total_pages > 0 and book.pages_total != total_pages:
        book.pages_total = total_pages
        updated_fields = True

    # 2. Sincronización del avance de páginas leídas
    last_pages_read = book.pages_read
    if current_page > 0:
        if current_page > book.pages_total:
            current_page = book.pages_total

        if current_page > last_pages_read:
            pages_diff = current_page - last_pages_read
            book.pages_read = current_page
            updated_fields = True

            # Si alcanzó la última página, marcar libro como completado
            if book.pages_read >= book.pages_total:
                book.date_completed = timezone.now().date()
            else:
                book.date_completed = None

            # Actualizar récord diario y acumulado mensual en Profile
            today = timezone.now().date()
            current_month = today.month

            if profile.date_most_pages_read == today:
                profile.most_pages_read += pages_diff
            else:
                if pages_diff > profile.most_pages_read:
                    profile.most_pages_read = pages_diff
                    profile.date_most_pages_read = today

            if profile.most_pages_read < 0:
                profile.most_pages_read = 0

            if profile.date_most_pages_read and profile.date_most_pages_read.month != current_month:
                profile.pages_this_month = 0
            profile.pages_this_month += pages_diff
            if profile.pages_this_month < 0:
                profile.pages_this_month = 0

            profile.save()

    if updated_fields:
        book.save()

    return JsonResponse({
        'status': 'ok',
        'pages_read': book.pages_read,
        'pages_total': book.pages_total,
        'progress': book.progress(),
        'date_completed': book.date_completed.strftime('%d/%m/%Y') if book.date_completed else None,
        'pages_for_day': book.pages_for_day(),
    })
```

---

## 5. Controles y Experiencia de Lectura para el Usuario

La cabecera del visor PDF incluye herramientas completas de lectura:

| Control | Acción | Atajo de Teclado |
|---|---|---|
| **◀ Anterior** | Retrocede una página en el PDF | `Flecha Izquierda` (◀) / `RePág` |
| **Siguiente ▶** | Avanza una página y guarda el progreso | `Flecha Derecha` (▶) / `AvPág` |
| **Página X de Y** | Permite teclear directamente el número de página al que se desea saltar | Tecla `Enter` tras teclear número |
| **Zoom (+ / −)** | Incrementa o reduce el tamaño de visualización en saltos de 15% | Botones de barra |
| **Ajustar** | Escala automáticamente el ancho del PDF al tamaño de la pantalla del usuario | Botón `Ajustar` |
| **Abrir original ↗** | Enlace directo para abrir o descargar el archivo PDF en una pestaña separada | Enlace en pie de tarjeta |

---

## 6. Actualización Reactiva en Tiempo Real en la Interfaz

Al avanzar una página en el visor, JavaScript envía una llamada asíncrona mediante `fetch()`. Al recibir la respuesta del servidor, la interfaz **se actualiza dinámicamente sin recargar la página**:

1. **Barra de Progreso:** La barra animada cambia su ancho porcentual en tiempo real (`progress-bar`).
2. **Contador de Páginas:** El texto `X de Y págs. (Z%)` se actualiza inmediatamente.
3. **Formulario de Edición:** Los inputs `id_pages_read` e `id_pages_total` reflejan la página actual.
4. **Tabla de Ritmo Diario:** Las filas de la tabla *"Días restantes / Páginas por día"* se recalculan y redibujan en vivo según las páginas que restan por leer.
5. **Badge de Confirmación:** Un badge verde flotante `✓ Progreso sincronizado (Pág. X)` aparece brevemente para confirmar al lector que su avance ha quedado respaldado en el servidor.
6. **Finalización Automática:** Al llegar a la última página, se despliega el badge `✅ Libro Completado (DD/Mes/AAAA)`.

---

## 7. Pruebas Automatizadas y Validación Empírica

Se ejecutó una prueba de integración completa simulando el ciclo de vida de lectura:

### Escenario de prueba ejecutado:
- **Libro inicial:** 100 páginas declaradas (provenientes de Google Books), `pages_read = 0`.
- **Evento 1 (Apertura del PDF de 25 páginas):**  
  El visor detecta `total_pages: 25` y abre en `current_page: 1`.  
  *Resultado:* `status: ok | pages_total: 25 | pages_read: 1 | progress: 4%`.
- **Evento 2 (Avance a la página 10):**  
  El usuario avanza a la página 10 del visor.  
  *Resultado:* `status: ok | pages_read: 10 | progress: 40%`.
- **Evento 3 (Lectura completa hasta la página 25):**  
  El usuario llega a la última página del documento.  
  *Resultado:* `status: ok | pages_read: 25 | progress: 100% | completed: True`.

```
Salida de consola del test:
Paso 1 (Ajuste de total a 25 págs): ok | pages_total: 25 | pages_read: 1 | progress: 4 %
Paso 2 (Avanza a pág 10): ok | pages_read: 10 | progress: 40 %
Paso 3 (Completa pág 25): ok | pages_read: 25 | progress: 100 % | completed: True
Libro eliminado limpiamente y comprobación exitosa.
```

---

## 8. Resumen de Archivos Modificados

| Archivo | Tipo de Modificación | Descripción del Cambio |
|---|---|---|
| [`BookTracker/urls.py`](BookTracker/urls.py) | Modificado | Registro de la ruta `/books/<int:book_id>/update-pdf-progress/`. |
| [`books/views.py`](books/views.py) | Modificado | Implementación de la vista controladora `update_pdf_progress`. |
| [`books/templates/book_detail.html`](books/templates/book_detail.html) | Reescrito | Reemplazo del `<iframe>` por el visor interactivo PDF.js, barra de progreso reactiva y script de sincronización. |
| [`BookTracker/settings.py`](BookTracker/settings.py) | Modificado | Ajuste de `ALLOWED_HOSTS = ['*']` para permitir peticiones AJAX y entornos de desarrollo/pruebas. |
| [`BUGFIX_REPORT5.md`](BUGFIX_REPORT5.md) | Creado | Este informe detallado de arquitectura, solución al conflicto de páginas y pruebas. |

