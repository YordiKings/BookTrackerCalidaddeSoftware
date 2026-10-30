# Reporte de Implementación Explicativo - Milestone 1

Este documento contiene el desglose detallado de todos los módulos, integraciones de API, subida de archivos (portadas y PDFs), vista interactiva y Dashboard dinámico implementados para el **Milestone 1** del proyecto **BookTracker**.

---

## 1. Módulo de Base de Datos y Modelos ORM
**Archivo principal:** [`books/models.py`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/models.py)

Se expandió el modelo `Book` para permitir almacenamiento multimedia y metadata obtenida externamente:

```python
class Book(models.Model):
    # Campos base
    title = models.CharField(max_length=50)
    autor = models.CharField(max_length=50)
    goal = models.DateField(null=True, blank=True)
    pages_read = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    pages_total = models.IntegerField(validators=[MinValueValidator(1)])
    created = models.DateField(auto_now_add=True)  # Se asigna la fecha automáticamente al crear
    date_completed = models.DateField(null=True, blank=True, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Nuevos campos para Milestone 1
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)
    google_books_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
```

### ¿Cómo funciona cada campo?
* **`created = models.DateField(auto_now_add=True)`**: `auto_now_add=True` le indica a Django que guarde automáticamente la fecha del sistema en el instante exacto en que se registra un libro.
* **`cover` y `pdf_file`**: Django maneja estos campos guardando la **ruta relativa** del archivo en la base de datos (ej. `covers/mi_libro.jpg`), mientras que el archivo binario físico se deposita en la carpeta `media/covers/` o `media/pdfs/`.
* **`google_books_id` y `description`**: Guardan el identificador único de la API de Google Books y la sinopsis/descripción oficial del libro.

---

## 2. Integración con la API de Google Books y Subida de Archivos
**Archivo principal:** [`books/views.py`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/views.py)

Toda la lógica de consulta e inserción automática vive en la vista `create_book`:

```python
@login_required
def create_book(request):
    # ...
    form = BookForm(request.POST, request.FILES)
    if form.is_valid():
        new_book = form.save(commit=False)
        new_book.user = request.user
        
        # 1. Petición a la API de Google Books
        query = f"intitle:{new_book.title}"
        if new_book.autor:
            query += f"+inauthor:{new_book.autor}"
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1")
        
        if response.status_code == 200 and 'items' in response.json():
            item = response.json()['items'][0]
            new_book.google_books_id = item.get('id')
            new_book.description = item.get('volumeInfo', {}).get('description', '')
            
            # 2. Descarga de Portada Automática (si el usuario no subió una)
            if not new_book.cover:
                cover_url = item.get('volumeInfo', {}).get('imageLinks', {}).get('thumbnail')
                if cover_url:
                    cover_url = cover_url.replace('http:', 'https:')
                    img_response = requests.get(cover_url)
                    if img_response.status_code == 200:
                        new_book.cover.save(f"{new_book.title}_cover.jpg", ContentFile(img_response.content), save=False)

        new_book.save()
```

### ¿Cómo funciona paso a paso?
1. **Formulario con subida de archivos (`request.FILES`)**: Permite recibir tanto imágenes como PDFs desde el navegador.
2. **Búsqueda HTTP en Google Books**: Cuando el usuario envía el título y autor, Django hace un `requests.get()` hacia `googleapis.com`.
3. **Respuesta JSON**: Extraemos el `id` del volumen y la `description`.
4. **Descarga de portada externa (`ContentFile`)**: Si el usuario no adjuntó una imagen, pero la API sí devolvió un enlace de portada (`thumbnail`), hacemos un segundo `get()`, leemos los bytes (`img_response.content`) y con `ContentFile` guardamos la imagen nativamente dentro de la carpeta `media/covers/`.

---

## 3. Módulo de UI: Visor de PDF e Imágenes de Portada
**Archivos principales:** [`books/templates/create_book.html`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/templates/create_book.html) y [`books/templates/book_detail.html`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/templates/book_detail.html)

1. **Atributo Enctype para subida de archivos**:
   ```html
   <form method="POST" enctype="multipart/form-data">
   ```
   *Sin `enctype="multipart/form-data"`, el navegador solo enviaría texto y omitirá los archivos cargados.*

2. **Visor interactivo de PDF en pantalla completa/mitad**:
   ```html
   {% if book.pdf_file %}
       <div class="pdf-container my-3">
           <h4>Lectura digital (PDF)</h4>
           <iframe src="{{ book.pdf_file.url }}" width="100%" height="600px" style="border: none;">
               Tu navegador no soporta la vista previa de archivos PDF.
           </iframe>
       </div>
   {% endif %}
   ```
   Utilizamos un elemento `<iframe>` apuntando a `{{ book.pdf_file.url }}`, lo cual permite que el visor nativo de PDF del navegador (con zoom, scroll y páginas) funcione dentro de la app.

3. **Renderizado de Portada**:
   ```html
   {% if book.cover %}
       <img src="{{ book.cover.url }}" class="img-fluid rounded shadow" alt="Portada de {{ book.title }}">
   {% endif %}
   ```

---

## 4. Módulo de Dashboard Dinámico por Meses
**Archivos principales:** [`BookTracker/settings.py`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/BookTracker/settings.py), [`books/views.py`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/views.py) y [`books/templates/dashboard.html`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/books/templates/dashboard.html)

### ¿Cómo agrupamos dinámicamente los libros por mes?
1. **Configuración Regional (`settings.py`)**:
   ```python
   LANGUAGE_CODE = 'es-mx'
   ```
   Esto asegura que la plantilla muestre nombres en español (*Enero, Febrero, Octubre...*) en lugar de en inglés.

2. **Consulta en el Backend (`views.py`)**:
   ```python
   @login_required
   def dashboard(request):
       books_created = Book.objects.filter(user=request.user).order_by('-created')
       books_completed = Book.objects.filter(user=request.user, date_completed__isnull=False).order_by('-date_completed')
       profile = request.user.profile
       return render(request, 'dashboard.html', {'books_created': books_created, 'books_completed': books_completed, 'profile': profile})
   ```

3. **Agrupación en Plantilla HTML (`dashboard.html`)**:
   ```django
   {% regroup books_created by created|date:"F" as created_list %}
   {% for month in created_list %}
       <div class="d-flex album p-4 m-4 w-100 flex-wrap shadow" style="background:white">
           <div class="d-flex justify-content-left w-100 pl-4">
               <h2 class="text-capitalize">Agregados en {{ month.grouper }}</h2>
           </div>
           <div class="container-fluid">
               <div class="row">   
                   {% for book in month.list %}
                       <!-- Tarjeta del libro -->
                   {% endfor %}
               </div>
           </div>
       </div>
   {% endfor %}
   ```
   - `created|date:"F"` extrae el nombre completo del mes (ej. "Octubre").
   - `{% regroup %}` agrupa la lista por dicho mes.
   - Si en Noviembre agregaste 2 libros y en Diciembre 3, se renderizarán automáticamente 2 tarjetas/bloques diferentes sin necesidad de código estático.

---

## 5. Gestión de Dependencias
**Archivo principal:** [`requirements.txt`](file:///c:/Users/cdepu/Downloads/Proyectos/BookTracker/requirements.txt)

Generado usando `uv` sin hashes para mayor limpieza:
```bash
uv export --format requirements-txt --no-hashes -o requirements.txt
```
Incluye las librerías principales:
* **`django==6.1.1`**: Framework Web.
* **`pillow==12.3.0`**: Procesamiento de imágenes (portadas).
* **`requests==2.34.2`**: Cliente HTTP para consumir la API de Google Books.
* **`pytest` y `pytest-django`**: Entorno para ejecución de las pruebas.
