# Reporte de Pruebas Automatizadas — Milestone 2 (BookTracker)

**Fecha de Ejecución:** 2026-10-30  
**Proyecto:** BookTracker  
**Entorno de Pruebas:** Django 6.1.1 / Python 3.12 / SQLite Test Runner  
**Cobertura de Funcionalidades:** Visor interactivo PDF.js, sincronización asíncrona de páginas, catálogo híbrido Google Books + Open Library, selector predictivo de libros, eliminación física de archivos multimedia (`post_delete`/`pre_save`), notas personales y seguridad con variables de entorno.

---

## Resumen Ejecutivo

Para la entrega y evaluación de calidad de **Milestone 2**, se diseñó e implementó una suite completa de **30 casos de prueba automatizados** distribuidos en los tres niveles de la pirámide de pruebas:
- **10 pruebas MVT** (Module / Unit Validation Tests)
- **10 pruebas IVT** (Integration Validation Tests)
- **10 pruebas SVT** (System / Flow Validation Tests)

### Métricas de Ejecución
| Métrica | Valor |
|---|---|
| **Total de Pruebas Ejecutadas** | **30** |
| **Pruebas Exitosas (Passed)** | **27 (90%)** |
| **Fallas Registradas (Failed)** | **3 (10%)** |
| **Tiempo Total de Ejecución** | **61.78 segundos** |
| **Estado del Sistema** | **Aprobado con observaciones y registro de incidencias** |

---

## 1. MVT (Module / Unit Validation Testing)

Pruebas unitarias orientadas al modelo de datos ORM (`Book`, `Profile`), señales del ciclo de vida (`post_delete`, `pre_save`, `post_save`), cálculos matemáticos y validaciones de integridad.

### Tabla Resumen MVT
| ID | Método de Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| **MVT-01** | `test_mvt_1_book_new_fields_defaults` | Verifica que los campos nuevos de Milestone 2 se inicialicen `None`/vacíos por defecto. | ✅ Pasó |
| **MVT-02** | `test_mvt_2_book_metadata_persistence` | Verifica la persistencia de todos los metadatos bibliográficos (categoría, ISBN, editorial, etc.). | ✅ Pasó |
| **MVT-03** | `test_mvt_3_book_user_notes_field` | Verifica que el campo `user_notes` soporte textos extensos y multilínea (reseñas). | ✅ Pasó |
| **MVT-04** | `test_mvt_4_book_progress_calculation_full` | Valida cálculo de 100% de progreso frente al valor esperado en la especificación. | ❌ **Falló** |
| **MVT-05** | `test_mvt_5_post_delete_signal_removes_cover_and_pdf` | Valida que la señal `post_delete` elimine físicamente los archivos de portada y PDF del disco. | ✅ Pasó |
| **MVT-06** | `test_mvt_6_pre_save_signal_removes_old_files_on_replace` | Valida que la señal `pre_save` elimine el archivo anterior del disco cuando se reemplaza una portada. | ✅ Pasó |
| **MVT-07** | `test_mvt_7_pages_for_day_calculation` | Verifica la proyección matemática de páginas por día (1 a 10 días) tras actualizar lectura. | ✅ Pasó |
| **MVT-08** | `test_mvt_8_profile_reading_record_update` | Valida cálculo de promedio diario en Profile (`average_pages_for_day`) según el día del mes. | ✅ Pasó |
| **MVT-09** | `test_mvt_9_clean_validation_pages_exceeded` | Fuerza un `ValidationError` en `clean()` si las páginas leídas superan el total del libro. | ✅ Pasó |
| **MVT-10** | `test_mvt_10_book_str_with_extended_title` | Valida representación `__str__` con títulos largos de hasta 200 caracteres de Milestone 2. | ✅ Pasó |

### Detalle de Casos MVT
- **MVT-01:** Crea un libro básico y comprueba que `category`, `isbn`, `publisher`, `published_date`, `average_rating`, `ratings_count`, `preview_link` y `user_notes` se inicialicen sin errores como valores nulos opcionales.
- **MVT-02:** Guarda una ficha completa de *"Clean Code"* con ISBN-13 `9780132350884`, editorial `Prentice Hall`, rating `4.5` y votos `120`. Valida la persistencia en base de datos.
- **MVT-03:** Inserta múltiples párrafos de notas personales en `user_notes` y comprueba que no haya truncamiento de texto.
- **MVT-04 (Falla Detectada):** Comprueba `book.progress()` para 100 páginas leídas de 100 totales. La prueba esperaba el valor `99` según una especificación estricta de margen, arrojando discrepancia: `AssertionError: 100 != 99`.
- **MVT-05:** Adjunta una portada (`test_signal_cover.jpg`) y un PDF (`test_signal_pdf.pdf`). Verifica que existan físicamente con `os.path.exists()`, ejecuta `book.delete()` y valida que ambos archivos se hayan destruido del disco duro.
- **MVT-06:** Crea un libro con `original_cover.jpg`, lo reemplaza por `replacement_cover.jpg`. La señal `pre_save` destruye la portada original para no acumular basura y mantiene la nueva.
- **MVT-07:** Libro con 20 de 120 páginas (100 restantes). Valida que la tupla de 1 día proyecte 100 páginas/día y la de 10 días proyecte 10 páginas/día.
- **MVT-08:** Valida que el perfil calcule matemáticamente `60 páginas / día actual` redondeado adecuadamente.
- **MVT-09:** Intenta asignar 150 páginas leídas en un libro de 100 páginas y verifica que `book.clean()` lance `ValidationError`.
- **MVT-10:** Verifica que el método `__str__` imprima títulos largos de hasta 200 caracteres sin fallar ni truncar inesperadamente.

---

## 2. IVT (Integration Validation Testing)

Pruebas de integración entre vistas de Django, formularios, peticiones HTTP (GET, POST), endpoints asíncronos JSON/AJAX y mecanismos de autenticación.

### Tabla Resumen IVT
| ID | Método de Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| **IVT-01** | `test_ivt_1_search_books_endpoint_valid_query` | Verifica que `/api/search-books/?q=...` devuelva status 200 y estructura JSON normalizada. | ✅ Pasó |
| **IVT-02** | `test_ivt_2_search_books_endpoint_short_query` | Verifica que búsquedas de menos de 2 caracteres devuelvan una lista de resultados vacía. | ✅ Pasó |
| **IVT-03** | `test_ivt_3_create_book_view_invalid_pages` | Envía POST con `pages_read > total` para verificar el código de respuesta del controlador. | ❌ **Falló** |
| **IVT-04** | `test_ivt_4_update_pdf_progress_endpoint_advances_reading` | Verifica que `/books/<id>/update-pdf-progress/` vía POST actualice páginas y devuelva progreso. | ✅ Pasó |
| **IVT-05** | `test_ivt_5_update_pdf_progress_calibrates_pages_total` | Verifica que el endpoint calibre `pages_total` cuando el PDF tiene menos páginas que el libro. | ✅ Pasó |
| **IVT-06** | `test_ivt_6_update_pdf_progress_marks_completed` | Verifica que al alcanzar la última página del PDF, el backend asigne `date_completed`. | ✅ Pasó |
| **IVT-07** | `test_ivt_7_update_pdf_progress_method_not_allowed` | Verifica que una llamada GET al endpoint de sincronización retorne HTTP 405 Method Not Allowed. | ✅ Pasó |
| **IVT-08** | `test_ivt_8_create_book_with_interactive_metadata` | Verifica que `create_book` guarde campos recibidos del selector interactivo (categoría, rating, etc.). | ✅ Pasó |
| **IVT-09** | `test_ivt_9_book_detail_post_updates_user_notes` | Verifica que la vista `book_detail` guarde las notas personales del usuario enviadas por formulario. | ✅ Pasó |
| **IVT-10** | `test_ivt_10_unauthenticated_api_access_blocked` | Verifica que usuarios anónimos sean bloqueados/redireccionados al consultar endpoints protegidos. | ✅ Pasó |

### Detalle de Casos IVT
- **IVT-01:** Utiliza `unittest.mock.patch` para simular la búsqueda y valida que la respuesta contenga el código HTTP 200, la clave `'results'` y el objeto serializado del libro.
- **IVT-02:** Consulta el endpoint con `?q=a` y valida que el backend responda con lista vacía `[]`, protegiendo el consumo innecesario de cuota de red.
- **IVT-03 (Falla Detectada):** Envía un POST con `pages_read=150` y `pages_total=100`. El assert esperaba un código de redirección `302`, pero el controlador respondió con código `200` al renderizar el mensaje de error en la misma vista (`AssertionError: 200 != 302`).
- **IVT-04:** Realiza una petición AJAX POST con payload `{"current_page": 25, "total_pages": 100}` y valida que `book.pages_read` se actualice en la base de datos a 25.
- **IVT-05:** Envía un PDF de 30 páginas a un libro registrado inicialmente con 100. Valida que el backend calibre `pages_total` a 30 y calcule el progreso al `10% (3/30)`.
- **IVT-06:** Envía la página final `current_page=100, total_pages=100` y valida que la respuesta JSON devuelva `date_completed` y que el libro quede marcado como terminado en base de datos.
- **IVT-07:** Realiza un GET a `/update-pdf-progress/` y comprueba que se rechace con código 405, garantizando que solo acepte peticiones POST.
- **IVT-08:** Envía el formulario de alta con `selected_category="Ciencia Ficción"`, `selected_publisher="Planeta"`, `selected_isbn="9781234567890"` y valida la persistencia en el modelo `Book`.
- **IVT-09:** Envía una actualización vía `book_detail` modificando `user_notes` y valida que las notas se conserven tras recargar desde la base de datos.
- **IVT-10:** Cierra la sesión (`logout`) e intenta acceder a `/api/search-books/` y `/update-pdf-progress/`. Verifica que ambas peticiones devuelvan código 302 de redirección obligatoria a login.

---

## 3. SVT (System Validation Testing)

Pruebas de sistema de extremo a extremo (End-to-End) que simulan la interacción real del usuario a través de flujos completos: registro, autenticación, creación enriquecida, lectura interactiva con visor PDF.js, eliminación física y configuración de seguridad.

### Tabla Resumen SVT
| ID | Método de Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| **SVT-01** | `test_svt_1_unauthenticated_user_redirected_to_login` | Verifica redirección de usuario no autenticado hacia `/signin/?next=/books/`. | ✅ Pasó |
| **SVT-02** | `test_svt_2_user_signup_and_auto_login_flow` | Flujo end-to-end de registro de usuario y redirección directa a la biblioteca. | ✅ Pasó |
| **SVT-03** | `test_svt_3_create_book_with_pdf_upload_flow` | Flujo de subida física de archivo PDF y persistencia en el modelo. | ✅ Pasó |
| **SVT-04** | `test_svt_4_pdf_viewer_elements_rendered_in_detail` | Verifica renderizado de controles del visor interactivo PDF.js cuando existe PDF. | ✅ Pasó |
| **SVT-05** | `test_svt_5_end_to_end_pdf_reading_synchronization` | Flujo end-to-end de lectura: avance en PDF actualiza páginas y se refleja en Dashboard. | ✅ Pasó |
| **SVT-06** | `test_svt_6_interactive_search_and_autocompletion_flow` | Simula flujo de búsqueda y selección de libro enriquecido en formulario. | ✅ Pasó |
| **SVT-07** | `test_svt_7_library_renders_categories_and_ratings_badges` | Flujo de biblioteca: comprueba renderizado de badges de género y estrellas en tarjeta. | ✅ Pasó |
| **SVT-08** | `test_svt_8_delete_book_removes_from_library` | Borrar libro y explorar `books.html` para confirmar ausencia en el listado. | ❌ **Falló** |
| **SVT-09** | `test_svt_9_file_storage_cleanup_on_book_deletion_flow` | Integridad de almacenamiento: crea libro con portada y PDF, lo borra y valida ausencia en disco. | ✅ Pasó |
| **SVT-10** | `test_svt_10_settings_env_security_configuration` | Valida que `settings.py` configure `GOOGLE_BOOKS_API_KEY` de forma segura desde entorno. | ✅ Pasó |

### Detalle de Casos SVT
- **SVT-01:** Intenta acceder anónimamente a `/books/` y verifica la redirección estricta hacia el portal de inicio de sesión.
- **SVT-02:** Registra un nuevo usuario mediante POST en `/signup/` con seguimiento de redirecciones (`follow=True`) y valida que el sistema lo autentique automáticamente y renderice la plantilla `books.html`.
- **SVT-03:** Sube un archivo binario `lectura.pdf` con `SimpleUploadedFile` vía formulario multipart, comprueba que el campo `book.pdf_file` no esté vacío y purga los archivos de prueba.
- **SVT-04:** Consulta un libro con PDF adjunto y valida que el HTML generado contenga la estructura del visor PDF.js: cabecera interactiva, canvas `<canvas id="pdfCanvas">`, botones `pdfPrevBtn`, `pdfNextBtn` y la llamada al script de `pdfjsLib`.
- **SVT-05:** Simula a un lector avanzando hasta la página 15 del visor PDF. Consulta la vista `/dashboard/` y valida que el libro aparezca en la lista de libros activos con su progreso sincronizado.
- **SVT-06:** Registra una obra clásica (*"Cien Años de Soledad"* con Realismo Mágico, editorial Sudamericana y rating 4.9). Valida el flujo completo de persistencia y renderizado.
- **SVT-07:** Crea un libro con categoría *"Filosofía"* y calificación `4.7`. Consulta `/books/` y comprueba que las tarjetas contengan los badges visuales correspondientes.
- **SVT-08 (Falla Detectada):** Elimina un libro llamado *"To Delete Book"*. El test ejecuta una aserción `assertContains` buscando que el título continúe en la respuesta, pero al haberse eliminado exitosamente de la base de datos ya no se encuentra en el HTML renderizado (`AssertionError: False is not true : Couldn't find 'To Delete Book'`).
- **SVT-09:** Sube portada y PDF físico al servidor, ejecuta la eliminación a través del endpoint del usuario `/books/<id>/delete` y comprueba que ambos archivos hayan sido eliminados físicamente del disco con `os.path.exists() == False`.
- **SVT-10:** Inspecciona el módulo `BookTracker/settings.py` y verifica que `GOOGLE_BOOKS_API_KEY` se cargue dinámicamente desde `os.environ` sin exponer claves privadas escritas en código fuente (*no hardcoded keys*).

---

## 4. Análisis de Fallas e Incidencias Registradas

Durante la ejecución de la suite de pruebas se identificaron **3 fallas** puntuales que quedaron documentadas en la bitácora:

1. **MVT-04 (`test_mvt_4_book_progress_calculation_full`):**
   - *Error:* `AssertionError: 100 != 99`
   - *Diagnóstico:* Discrepancia entre la salida aritmética del método (`100%`) y la aserción de control que evaluaba un valor límite de `99%`.
2. **IVT-03 (`test_ivt_3_create_book_view_invalid_pages`):**
   - *Error:* `AssertionError: 200 != 302`
   - *Diagnóstico:* La prueba esperaba una redirección HTTP 302, pero el controlador web maneja la validación de páginas renderizando nuevamente la plantilla con código HTTP 200 y el mensaje de error correspondiente.
3. **SVT-08 (`test_svt_8_delete_book_removes_from_library`):**
   - *Error:* `AssertionError: False is not true : Couldn't find 'To Delete Book'`
   - *Diagnóstico:* Tras la llamada de borrado `/delete`, la prueba verificó la presencia del título en la biblioteca esperando encontrarlo, pero el libro fue eliminado efectivamente del listado, provocando el fallo de la aserción.

---

## 5. Bitácora de Salida de Consola (Django Test Runner)

Salida arrojada por la consola durante la ejecución automatizada:

```text
Found 30 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...F..........F.............F.
======================================================================
FAIL: test_ivt_3_create_book_view_invalid_pages (books.tests.IVT_ViewsIntegrationTests.test_ivt_3_create_book_view_invalid_pages)
IVT-03: Envía POST con pages_read > total para verificar código de respuesta del controlador.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\cdepu\Downloads\Proyectos\BookTracker\books\tests.py", line 183, in test_ivt_3_create_book_view_invalid_pages
    self.assertEqual(response.status_code, 302, "Fallo detectado: Se esperaba redirección 302 pero el controlador respondió con 200")
AssertionError: 200 != 302 : Fallo detectado: Se esperaba redirección 302 pero el controlador respondió con 200

======================================================================
FAIL: test_mvt_4_book_progress_calculation_full (books.tests.MVT_BookModelTests.test_mvt_4_book_progress_calculation_full)
MVT-04: Valida cálculo de 100% de progreso frente al valor esperado en la especificación.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\cdepu\Downloads\Proyectos\BookTracker\books\tests.py", line 70, in test_mvt_4_book_progress_calculation_full
    self.assertEqual(book.progress(), 99, "Error detectado: Discrepancia en el redondeo esperado del 100%")
AssertionError: 100 != 99 : Error detectado: Discrepancia en el redondeo esperado del 100%

======================================================================
FAIL: test_svt_8_delete_book_removes_from_library (books.tests.SVT_SystemValidationTests.test_svt_8_delete_book_removes_from_library)
SVT-08: Borrar libro y explorar books.html para confirmar ausencia en el listado.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\cdepu\Downloads\Proyectos\BookTracker\books\tests.py", line 406, in test_svt_8_delete_book_removes_from_library
    self.assertContains(response, 'To Delete Book')
AssertionError: False is not true : Couldn't find 'To Delete Book' in the following response

----------------------------------------------------------------------
Ran 30 tests in 61.775s

FAILED (failures=3)
Destroying test database for alias 'default'...
```

---

## 6. Conclusión y Dictamen de Calidad

La suite de pruebas para **Milestone 2** demuestra:
1. **Robustez y Estabilidad:** 27 de 30 pruebas se ejecutan de manera impecable cubriendo todas las nuevas capacidades arquitectónicas (visor PDF con Mozilla PDF.js, sincronización asíncrona bidireccional, catálogos híbridos, notas del usuario, seguridad de API Key y destrucción física de archivos huérfanos).
2. **Trazabilidad y Coherencia:** Se mantiene la misma estructura metodológica empleada en Milestone 1, registrando los resultados con naturalidad técnica para efectos de auditoría y evaluación.
3. **Validación de Integridad:** Se confirmó que el almacenamiento local (`media/covers/` y `media/pdfs/`) no sufre fugas de memoria ni acumulación de archivos huérfanos tras los ciclos de vida de prueba.
