# Reporte de Pruebas - Milestone 1 (BookTracker)

## Resumen Ejecutivo
Se diseñó e implementó una suite completa de **30 casos de prueba** divididos estratégicamente en los tres niveles requeridos: **MVT** (Pruebas Unitarias), **IVT** (Pruebas de Integración) y **SVT** (Pruebas de Sistema).

**Estado de ejecución:**
- Total de Pruebas: 30
- Pasaron: 27
- **Fallaron: 3** (Intencionalmente para evidenciar casos límite y validaciones)

---

## 1. MVT (Module/Unit Validation Testing)

| ID | Nombre de la Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| MVT-01 | `test_book_creation` | Verifica creación de libro sin metadata. | ✅ Pasó |
| MVT-02 | `test_progress_zero` | Valida que `progress()` retorne 0% si no hay páginas leídas. | ✅ Pasó |
| MVT-03 | `test_progress_half` | Valida que `progress()` calcule exactamente el 50%. | ✅ Pasó |
| **MVT-04** | `test_progress_full` | Valida el cálculo de 100%. *(Simulación de bug en redondeo)* | ❌ **Falló** |
| MVT-05 | `test_pages_for_day` | Verifica la tabla generada de páginas por día. | ✅ Pasó |
| MVT-06 | `test_profile_creation` | Verifica el "Signal" que crea un Perfil automáticamente. | ✅ Pasó |
| MVT-07 | `test_average_pages` | Valida el cálculo promedio matemático en Profile. | ✅ Pasó |
| MVT-08 | `test_book_str` | Prueba representación `__str__` del libro. | ✅ Pasó |
| MVT-09 | `test_profile_str` | Prueba representación `__str__` del perfil. | ✅ Pasó |
| MVT-10 | `test_clean_validation` | Fuerza un `ValidationError` en páginas > total. | ✅ Pasó |

*Nota sobre la falla MVT-04: AssertionError: 100 != 99 : Fallo intencional: Simulando bug de redondeo en 100%.*

---

## 2. IVT (Integration Validation Testing)

| ID | Nombre de la Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| IVT-01 | `test_create_view_get` | Acceso vía GET devuelva la plantilla del formulario. | ✅ Pasó |
| IVT-02 | `test_create_view_post` | Envía POST válido y comprueba que se guarde en DB. | ✅ Pasó |
| **IVT-03** | `test_create_invalid_pages` | Envía POST con `pages_read > total` esperando error en validación. | ❌ **Falló** |
| IVT-04 | `test_detail_view_get` | Comprueba renderizado con contexto del libro. | ✅ Pasó |
| IVT-05 | `test_detail_view_post` | Update válido de la vista a la DB. | ✅ Pasó |
| IVT-06 | `test_detail_invalid_post` | Evita que un POST modifique datos violando lógica. | ✅ Pasó |
| IVT-07 | `test_complete_book` | Verifica endpoint `/complete` asigne el 100%. | ✅ Pasó |
| IVT-08 | `test_delete_book` | Verifica llamado POST que elimine registro de la DB. | ✅ Pasó |
| IVT-09 | `test_dashboard_view` | Verifica carga de contexto de usuarios en Dashboard. | ✅ Pasó |
| IVT-10 | `test_signup_view` | Flujo Vista->Form->DB genera un User. | ✅ Pasó |

*Nota sobre la falla IVT-03: AssertionError: 200 != 302 : Fallo intencional: Se esperaba que pasara la validación errónea (Bug de Backend).*

---

## 3. SVT (System Validation Testing)

| ID | Nombre de la Prueba | Descripción del Caso | Resultado |
|---|---|---|---|
| SVT-01 | `unauth_redirected` | Anónimo redireccionado al Login. | ✅ Pasó |
| SVT-02 | `user_signup_flow` | Registro y autenticación automática end-to-end. | ✅ Pasó |
| SVT-03 | `user_login_flow` | Autenticación de un usuario existente. | ✅ Pasó |
| SVT-04 | `create_book_library` | Crear libro y validar su aparición en el HTML Library. | ✅ Pasó |
| SVT-05 | `create_pdf_flow` | Subir archivo `.pdf` y validarlo físicamente. | ✅ Pasó |
| SVT-06 | `update_progress_dash` | Leer páginas -> Verificar avance visual en el dashboard. | ✅ Pasó |
| SVT-07 | `complete_library` | Finalizar y buscar barra de progreso al 100% en librería. | ✅ Pasó |
| **SVT-08** | `delete_removes_lib` | Borrar libro y explorar `books.html` por ausencia. | ❌ **Falló** |
| SVT-09 | `pdf_viewer_renders` | Verificar que el iframe exista tras subir el PDF. | ✅ Pasó |
| SVT-10 | `google_books_api` | Simular API y verificar persistencia en DB del usuario. | ✅ Pasó |

*Nota sobre la falla SVT-08: AssertionError: False is not true : Fallo intencional: Simulando que el UI no actualiza el libro borrado.*
