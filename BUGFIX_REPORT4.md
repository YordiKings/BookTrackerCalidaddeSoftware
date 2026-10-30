# Reporte de Optimización y Limpieza de Almacenamiento (Parte 4) — BookTracker

**Fecha:** 2026-10-29  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12)  
**Alcance:** Eliminación automática de archivos multimedia en disco (`media/covers/` y `media/pdfs/`) al borrar o actualizar libros mediante señales del ORM de Django (`post_delete` y `pre_save`).

---

## Índice

1. [Diagnóstico del problema: Archivos huérfanos en disco](#1-diagnóstico-del-problema-archivos-huérfanos-en-disco)
2. [Solución arquitectónica: Señales del ciclo de vida en Django](#2-solución-arquitectónica-señales-del-ciclo-de-vida-en-django)
3. [Código implementado en `books/models.py`](#3-código-implementado-en-booksmodelspy)
4. [Mecanismos implementados: Borrado y Reemplazo de archivos](#4-mecanismos-implementados-borrado-y-reemplazo-de-archivos)
5. [Pruebas empíricas y validación](#5-pruebas-empíricas-y-validación)
6. [Resumen de Archivos Afectados](#6-resumen-de-archivos-afectados)
7. [Beneficios para el proyecto](#7-beneficios-para-el-proyecto)

---

## 1. Diagnóstico del problema: Archivos huérfanos en disco

### Comportamiento por defecto en Django
Por diseño interno y por motivos de seguridad heredados, Django **no elimina los archivos físicos del disco duro** cuando se ejecuta `model.delete()`. 

Cuando un usuario hacía clic en **Delete Book** (`/books/<id>/delete`):
1. La fila en la base de datos SQLite (`books_book`) se eliminaba correctamente.
2. Sin embargo, la imagen en `media/covers/` y el archivo en `media/pdfs/` permanecían intactos en el almacenamiento del servidor.

### Impacto negativo:
- **Acumulación de archivos huérfanos:** Con el paso del tiempo, el servidor acumula gigabytes de PDFs e imágenes que ya no pertenecen a ningún libro existente ni pueden ser consultados por nadie.
- **Vulnerabilidad de privacidad:** Si un usuario elimina un PDF personal, espera que sea destruido en el servidor.
- **Consumo innecesario de almacenamiento:** En despliegues en la nube (AWS S3, Render, Railway, VPS), almacenar archivos sin dueño incrementa los costos operativos.

---

## 2. Solución arquitectónica: Señales del ciclo de vida en Django

Para solucionar esto de raíz sin alterar las vistas ni los controladores existentes, se implementó el patrón de **Señales de Django (`django.db.models.signals`)**:

1. **`post_delete`:** Escucha el momento exacto en que una instancia de `Book` es eliminada de la base de datos y procede a borrar sus archivos asociados de portada y PDF mediante el sistema de almacenamiento oficial (`instance.cover.storage.delete()`).
2. **`pre_save`:** Escucha cuando un libro existente va a ser actualizado. Si el usuario sube una nueva portada o un nuevo PDF que reemplaza al anterior, detecta el cambio y elimina el archivo anterior del disco, evitando duplicados.

---

## 3. Código implementado en `books/models.py`

Se importaron `post_delete` y `pre_save`, y se agregaron los siguientes dos receptores decorados con `@receiver`:

```python
# books/models.py

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

# 1. Limpieza al eliminar el libro
@receiver(post_delete, sender=Book)
def delete_book_files_on_delete(sender, instance, **kwargs):
    """
    Elimina físicamente los archivos de portada y PDF del almacenamiento
    cuando el libro es eliminado por el usuario.
    """
    if instance.cover:
        try:
            if instance.cover.storage.exists(instance.cover.name):
                instance.cover.storage.delete(instance.cover.name)
        except Exception:
            pass

    if instance.pdf_file:
        try:
            if instance.pdf_file.storage.exists(instance.pdf_file.name):
                instance.pdf_file.storage.delete(instance.pdf_file.name)
        except Exception:
            pass

# 2. Limpieza al actualizar archivos de un libro existente
@receiver(pre_save, sender=Book)
def delete_old_files_on_update(sender, instance, **kwargs):
    """
    Si el usuario reemplaza una portada o un PDF por un archivo nuevo,
    elimina el archivo viejo del disco para evitar que se acumule basura.
    """
    if not instance.pk:
        return  # Libro nuevo, no hay archivo previo que limpiar

    try:
        old_book = Book.objects.get(pk=instance.pk)
    except Book.DoesNotExist:
        return

    # Si se reemplazó la portada anterior por otra nueva
    if old_book.cover and old_book.cover != instance.cover:
        try:
            if old_book.cover.storage.exists(old_book.cover.name):
                old_book.cover.storage.delete(old_book.cover.name)
        except Exception:
            pass

    # Si se reemplazó el archivo PDF anterior por otro nuevo
    if old_book.pdf_file and old_book.pdf_file != instance.pdf_file:
        try:
            if old_book.pdf_file.storage.exists(old_book.pdf_file.name):
                old_book.pdf_file.storage.delete(old_book.pdf_file.name)
        except Exception:
            pass
```

---

## 4. Mecanismos implementados: Borrado y Reemplazo de archivos

### A. Escenario 1: Borrado total del libro
```
[ Usuario pulsa "Delete Book" ]
               │
               ▼
   book.delete() en Django ORM
               │
               ├─────────────────────────┐
               ▼                         ▼
   Elimina fila en SQLite    Dispara señal post_delete
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
               ¿Existe cover en disco?        ¿Existe pdf_file en disco?
                         │                               │
                      Sí: BORRAR                      Sí: BORRAR
```

### B. Escenario 2: Reemplazo de archivo en edición
Si un usuario edita un libro y cambia la portada `portada_v1.jpg` por `portada_v2.png`:
1. La señal `pre_save` consulta el estado anterior del libro en la base de datos.
2. Compara `old_book.cover` con `instance.cover`.
3. Al detectar que cambiaron, elimina `portada_v1.jpg` de `media/covers/` y permite que se guarde `portada_v2.png`.

---

## 5. Pruebas empíricas y validación

Se ejecutó un script de verificación automatizada en Python para validar ambos casos:

### Prueba A: Eliminación de libro con portada y PDF
1. Se creó un libro temporal con portada (`signal_test_cover.jpg`) y archivo PDF (`signal_test_pdf.pdf`).
2. Se verificó que ambos archivos existieran físicamente en el disco duro.
3. Se llamó al método `b.delete()`.
4. Se inspeccionó el disco con `os.path.exists()`.
   - **Resultado:**
     ```
     Created files exist: True True
     Files exist after book.delete(): False False
     ```
   - **Conclusión:** Ambos archivos fueron purgados del disco inmediatamente al eliminar el libro.

### Prueba B: Reemplazo de portada en libro existente
1. Se creó un libro con una portada inicial `old_cover.jpg`.
2. Se reemplazó por `new_cover.jpg` y se guardó el cambio.
3. Se verificó si la portada vieja continuaba en el disco.
   - **Resultado:**
     ```
     Old cover exists: True
     Old cover deleted on update: True
     New cover exists on update: True
     New cover deleted on delete: True
     ```
   - **Conclusión:** La portada vieja fue eliminada al guardar la nueva, y la nueva fue eliminada al borrar finalmente el libro.

---

## 6. Resumen de Archivos Afectados

| Archivo | Modificación |
|---|---|
| [`books/models.py`](books/models.py) | Se añadieron las señales `delete_book_files_on_delete` (`post_delete`) y `delete_old_files_on_update` (`pre_save`). |
| [`BUGFIX_REPORT4.md`](BUGFIX_REPORT4.md) | Creación de este reporte formal. |

---

## 7. Beneficios para el proyecto

- **Mantenimiento Cero:** La carpeta `media/` se autolimpia automáticamente sin necesidad de scripts manuales de mantenimiento.
- **Protección de Almacenamiento:** No habrá consumo residual ni acumulación de basura en disco.
- **Transparencia Total:** Funciona de forma transparente tanto si el libro se borra desde la interfaz web, desde el panel de administración (`/admin/`), o desde el código Python/Django shell.

