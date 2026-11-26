# Reporte final de correcciones (Parte 1) — BookTracker

**Fecha:** 2026-11-26  
**Proyecto:** BookTracker (Django 6.1.1 / Python 3.12 / Bootstrap 4.3.1)  
**Rama:** `feat-borrar_metricas`  
**Alcance:** Corrección de los 18 hallazgos de la lista de errores: H01 a H17 y un error nuevo detectado fuera del Excel (rutas `/complete` y `/delete` abiertas por GET). Todos se confirmaron en el código antes de corregirlos, y cada corrección se verificó después con pruebas automáticas. En H16, el aviso de guardado quedó corregido y el tiempo de espera se redujo, pero no se eliminó del todo (ver detalle).

---

## Índice

1. [Resumen de correcciones](#1-resumen-de-correcciones)
2. [Prioridad alta](#2-prioridad-alta)
   - [H04 · Error 500 con campo vacío](#h04--error-500-con-campo-vacío)
   - [H07 · No funciona bien en celular](#h07--no-funciona-bien-en-celular)
3. [Prioridad media](#3-prioridad-media)
   - [H01 · Textos en inglés](#h01--textos-en-inglés)
   - [H02 · Mensaje de login contradictorio y errores sin estilo](#h02--mensaje-de-login-contradictorio-y-errores-sin-estilo)
   - [H03 · Contraseñas débiles aceptadas](#h03--contraseñas-débiles-aceptadas)
   - [H09 · El progreso del PDF solo sube](#h09--el-progreso-del-pdf-solo-sube)
   - [H10 · Estadísticas del mes y del récord mal calculadas](#h10--estadísticas-del-mes-y-del-récord-mal-calculadas)
   - [H12 · Contraste insuficiente](#h12--contraste-insuficiente)
   - [H16 · Guardar un libro puede tardar ~22 s sin avisar](#h16--guardar-un-libro-puede-tardar-22-s-sin-avisar)
   - [H05 · Dashboard confuso](#h05--dashboard-confuso)
   - [H06 · El inicio promete funciones que no existen](#h06--el-inicio-promete-funciones-que-no-existen)
4. [Prioridad baja](#4-prioridad-baja)
   - [H08 · El dashboard agrupa por mes sin año](#h08--el-dashboard-agrupa-por-mes-sin-año)
   - [H11 · Zona horaria UTC](#h11--zona-horaria-utc)
   - [H13 · Biblioteca vacía sin mensaje](#h13--biblioteca-vacía-sin-mensaje)
   - [H14 · Libros sin portada y tarjetas desiguales](#h14--libros-sin-portada-y-tarjetas-desiguales)
   - [H15 · Botones del inicio sin sesión y clase de Bootstrap 5](#h15--botones-del-inicio-sin-sesión-y-clase-de-bootstrap-5)
   - [H17 · HTML mal cerrado](#h17--html-mal-cerrado)
5. [Error nuevo: `/complete` y `/delete` por GET dan error 500](#5-error-nuevo-complete-y-delete-por-get-dan-error-500)
6. [Cambios en la base de datos (migración 0004)](#6-cambios-en-la-base-de-datos-migración-0004)
7. [Pruebas y verificación](#7-pruebas-y-verificación)
8. [Archivos modificados](#8-archivos-modificados)
9. [Notas y decisiones de diseño](#9-notas-y-decisiones-de-diseño)

---

## 1. Resumen de correcciones

| ID | Prioridad | Problema | Estado | Archivos principales |
|---|---|---|---|---|
| H04 | Alta | Error 500 si "páginas leídas" va vacío | ✅ Corregido | `views.py`, `forms.py`, `models.py` |
| H07 | Alta | Biblioteca y dashboard aplastados en celular | ✅ Corregido | `books.html`, `dashboard.html` |
| H01 | Media | Textos, menú y etiquetas en inglés | ✅ Corregido | `base.html`, plantillas, `models.py` + migración |
| H02 | Media | Mensaje "no son incorrectos" y errores sin estilo | ✅ Corregido | `views.py`, `signin.html`, `signup.html`, `style.css` |
| H03 | Media | Registro acepta contraseñas como "123" | ✅ Corregido | `views.py` |
| H09 | Media | El progreso del PDF solo sube e infla estadísticas | ✅ Corregido | `book_detail.html`, `views.py` |
| H10 | Media | Reinicio mensual y récord diario mal calculados | ✅ Corregido | `models.py` (nuevo `DailyReading`), `views.py` + migración |
| H12 | Media | Contraste de botones por debajo de WCAG AA | ✅ Corregido | `style.css` |
| H16 | Media | Guardar puede tardar ~22 s sin aviso | ✅ Corregido (indicador) / mitigado (tiempo) | `create_book.html`, `views.py` |
| H05 | Media | Récord sin etiqueta y vacío sin datos | ✅ Corregido | `dashboard.html` |
| H06 | Media | Inicio promete géneros, autores y "Reading Wrapped" | ✅ Corregido (texto ajustado) | `home.html` |
| H08 | Baja | Agrupación por mes sin año | ✅ Corregido | `dashboard.html` |
| H11 | Baja | `TIME_ZONE = 'UTC'` | ✅ Corregido | `settings.py`, `views.py`, `models.py` |
| H13 | Baja | Biblioteca vacía sin mensaje | ✅ Corregido | `books.html` |
| H14 | Baja | Sin imagen para libros sin portada; alturas distintas | ✅ Corregido | `books.html`, `style.css` |
| H15 | Baja | Botones visibles sin sesión; `ms-2` de Bootstrap 5 | ✅ Corregido | `home.html` |
| H17 | Baja | `<div>` sin cerrar y `<a>` cerrado con `</h1>` | ✅ Corregido | `base.html`, `signin.html`, `signup.html` |
| Nuevo | — | GET a `/complete` y `/delete` da error 500 | ✅ Corregido | `views.py` |

> ⚠️ **Acción requerida tras actualizar el código:** ejecutar `python manage.py migrate` (ver [sección 6](#6-cambios-en-la-base-de-datos-migración-0004)).

---

## 2. Prioridad alta

### H04 · Error 500 con campo vacío

**Error:** al crear o editar un libro dejando vacío el campo "Páginas leídas", la aplicación mostraba una página de error 500 con traza técnica.

**Qué pasaba:** las vistas convertían el valor con `int()` directamente desde `request.POST` **antes** de validar el formulario. `int('')` lanza `ValueError` y, como estaba fuera de cualquier `try`, Django respondía con error 500. Además, `Book.clean()` comparaba `pages_read > pages_total` sin comprobar si alguno era `None`, lo que podía provocar un `TypeError` cuando "Páginas totales" venía vacío.

**Reproducción (antes):**
```
POST /books/create/   pages_read=""  pages_total="100"  ->  500
POST /books/<id>/     pages_read=""  pages_total="100"  ->  500
```

**Dónde:** `books/views.py` (funciones `create_book` y `book_detail`), `books/forms.py` (`BookForm`), `books/models.py` (`Book.clean`).

**Código anterior** (`views.py`, igual en `create_book` y `book_detail`):
```python
form = BookForm(request.POST, request.FILES)
pages_read = int(request.POST.get('pages_read', 0))
pages_total = int(request.POST.get('pages_total', 0))
if pages_read > pages_total:
    return render(request, 'create_book.html', {'form': form, 'error': 'No puedes leer más páginas de las que tiene el libro'})
if form.is_valid():
    ...
```

**Código corregido** (`views.py`):
```python
form = BookForm(request.POST, request.FILES)
# La validación (campos vacíos, números inválidos, leídas > totales) la hace el formulario
if form.is_valid():
    pages_read = form.cleaned_data['pages_read']
    pages_total = form.cleaned_data['pages_total']
    ...
else:
    return render(request, 'create_book.html', {'form': form, 'error': 'Revisa los campos marcados en el formulario.'})
```

**Código corregido** (`forms.py`, nuevo en `BookForm`):
```python
        # "Páginas leídas" vacío se interpreta como 0 en lugar de provocar un error
        self.fields['pages_read'].required = False

    def clean_pages_read(self):
        pages_read = self.cleaned_data.get('pages_read')
        return 0 if pages_read is None else pages_read

    def clean(self):
        cleaned_data = super().clean()
        pages_read = cleaned_data.get('pages_read')
        pages_total = cleaned_data.get('pages_total')
        if pages_read is not None and pages_total is not None and pages_read > pages_total:
            self.add_error('pages_read', 'No puedes leer más páginas de las que tiene el libro.')
        return cleaned_data
```

**Código anterior / corregido** (`models.py`, `Book.clean`):
```python
# Antes
def clean(self):
    from django.core.exceptions import ValidationError
    if self.pages_read > self.pages_total:
        raise ValidationError("Las páginas leídas no pueden ser mayores que el total de páginas.")

# Después
def clean(self):
    from django.core.exceptions import ValidationError
    # Si algún campo vino vacío o inválido, el formulario ya reporta ese error;
    # aquí solo se compara cuando ambos valores existen (evita TypeError con None).
    if self.pages_read is None or self.pages_total is None:
        return
    if self.pages_read > self.pages_total:
        raise ValidationError("Las páginas leídas no pueden ser mayores que el total de páginas.")
```

**Resultado (después):**
```
POST /books/create/   pages_read=""   pages_total="100"  ->  302 (libro creado con 0 páginas leídas)
POST /books/<id>/     pages_read=""   pages_total="300"  ->  302
POST /books/<id>/     pages_read="5"  pages_total=""     ->  200 con el error marcado en el campo
POST /books/create/   pages_read="150" pages_total="100" ->  200 con "No puedes leer más páginas..."
```

---

### H07 · No funciona bien en celular

**Error:** en pantallas pequeñas las tarjetas de libros quedaban aplastadas.

**Qué pasaba:** la biblioteca usaba la clase `col` sin puntos de quiebre: Bootstrap reparte el ancho en partes iguales entre **todas** las tarjetas de la fila, sin importar el tamaño de pantalla (con 8 libros, cada tarjeta medía 1/8 del ancho del celular). El dashboard usaba `col-4` fija, es decir, 3 tarjetas por fila incluso en un celular de 360 px. El bloque de estadísticas también usaba `col-8` / `col` fijos y un atributo inválido `style="width=60%"`.

**Dónde:** `books/templates/books.html`, `books/templates/dashboard.html`.

**Código anterior** (`books.html`):
```html
{% for book in books %}
<div class="col">
    <div class="card mb-4 box-shadow shadow" style="width: 100%">
```

**Código corregido** (`books.html`):
```html
{% for book in books %}
<!-- 1 columna en celular, 2 en tablet, 3 en laptop y 4 en pantallas grandes -->
<div class="col-12 col-sm-6 col-md-4 col-xl-3 mb-4">
    <div class="card box-shadow shadow h-100">
```

**Código anterior** (`dashboard.html`):
```html
<div class= "col-4">
    <div class="card my-2" style="width: 100%">
...
<div class=" container-fluid mx-2 mb-5 row w-100 ">
    <div class= "col-8 mr-4 bg-light shadow" style="width=60%">
```

**Código corregido** (`dashboard.html`):
```html
<div class="col-12 col-sm-6 col-lg-4 my-2">
    <div class="card h-100" style="width: 100%">
...
<div class="row w-100 mx-0 mb-2">
    <div class="col-12 col-md-4 mb-3"> ... </div>   <!-- récord -->
    <div class="col-12 col-md-4 mb-3"> ... </div>   <!-- páginas del mes -->
    <div class="col-12 col-md-4 mb-3"> ... </div>   <!-- promedio diario -->
</div>
```

**Resultado:** en celular cada tarjeta ocupa el ancho completo (1 por fila), en tablet 2, en laptop 3, y en pantallas grandes 4 (biblioteca) o 3 (dashboard).

---

## 3. Prioridad media

### H01 · Textos en inglés

**Error:** parte de la interfaz estaba en inglés: el menú, títulos y botones, los enlaces de registro e inicio de sesión, el idioma del documento (`<html lang="en">`), el título de la pestaña y las etiquetas de los campos del formulario.

**Qué pasaba:** las plantillas tenían textos fijos en inglés y los campos del modelo `Book` no tenían `verbose_name`, así que Django generaba etiquetas a partir del nombre técnico del campo (`pages_read` → "Pages read", `pdf_file` → "Pdf file").

**Dónde:** `base.html`, `books.html`, `create_book.html`, `signin.html`, `signup.html`, `dashboard.html`, `books/models.py`.

**Código anterior** (`base.html`):
```html
<html lang="en">
...
<title>BookTracker Application</title>
...
<a class="nav-link" href="{% url 'home' %}">Home<span class="sr-only">(current)</span></a>
<a class="nav-link" href="/books">Books</a>
<a class="nav-link" href="/books/create">Create Book</a>
<a class="nav-link" href="/dashboard">Dashboard</a>
<a class="nav-link" href="/logout">Log out</a>
<a class="nav-link" href="/signup">Sign up</a>
<a class="nav-link" href="/signin">Sign in</a>
```

**Código corregido** (`base.html`):
```html
<html lang="es">
...
<title>BookTracker · Seguimiento de lectura</title>
...
<a class="nav-link" href="{% url 'home' %}">Inicio{% if url_name == 'home' %}<span class="sr-only">(actual)</span>{% endif %}</a>
<a class="nav-link" href="/books">Biblioteca</a>
<a class="nav-link" href="/books/create">Agregar libro</a>
<a class="nav-link" href="/dashboard">Estadísticas</a>
<a class="nav-link" href="/logout">Cerrar sesión</a>
<a class="nav-link" href="/signup">Registrarse</a>
<a class="nav-link" href="/signin">Iniciar sesión</a>
```
También se tradujo el `aria-label="Toggle navigation"` del botón del menú móvil a `"Mostrar u ocultar menú"`.

**Textos de plantillas:**

| Plantilla | Antes | Después |
|---|---|---|
| `books.html` | `Library` | `Mi biblioteca` |
| `books.html` | `Goal: …` | `Meta: …` |
| `create_book.html` | `Create Book` (título) | `Agregar libro` |
| `dashboard.html` | `Dashboard` (título) | `Estadísticas de lectura` |
| `signin.html` | `Sign in` / `Submit` | `Iniciar sesión` / `Entrar` |
| `signin.html` | `Not registered? Sign Up` | `¿No tienes cuenta? Regístrate` |
| `signup.html` | `Sign Up` / `Submit` | `Crear cuenta` / `Registrarme` |
| `signup.html` | `Already have an account? Sign In` | `¿Ya tienes cuenta? Inicia sesión` |

**Código anterior** (`models.py`):
```python
title = models.CharField(max_length=200)
autor = models.CharField(max_length=200)
goal = models.DateField(null=True, blank=True)
pages_read = models.IntegerField(default=0, validators=[MinValueValidator(0)])
pages_total = models.IntegerField(validators=[MinValueValidator(1)])
...
cover = models.ImageField(upload_to='covers/', null=True, blank=True)
pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)
...
user_notes = models.TextField(null=True, blank=True)
```

**Código corregido** (`models.py`):
```python
title = models.CharField('Título', max_length=200)
autor = models.CharField('Autor', max_length=200)
goal = models.DateField('Meta (fecha para terminarlo)', null=True, blank=True)
pages_read = models.IntegerField('Páginas leídas', default=0, validators=[MinValueValidator(0)])
pages_total = models.IntegerField('Páginas totales', validators=[MinValueValidator(1)])
created = models.DateField('Fecha de registro', auto_now_add=True)
date_completed = models.DateField('Fecha de término', null=True, blank=True, default=None)
user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
cover = models.ImageField('Portada', upload_to='covers/', null=True, blank=True)
pdf_file = models.FileField('Archivo PDF', upload_to='pdfs/', null=True, blank=True)
...
user_notes = models.TextField('Notas personales / Reseña', null=True, blank=True)
```

**Nota:** agregar `verbose_name` genera una migración (incluida en `0004`, ver [sección 6](#6-cambios-en-la-base-de-datos-migración-0004)). Solo cambia metadatos y no altera las tablas ni los datos. Los formularios de autenticación de Django ya salen en español porque `LANGUAGE_CODE = 'es-mx'`.

---

### H02 · Mensaje de login contradictorio y errores sin estilo

**Error:** al fallar el inicio de sesión aparecía *"El usuario o la contraseña **no son incorrectos**"*, que dice lo contrario de lo que pasó. Además, los errores de login y registro se imprimían como texto plano encima del formulario, fuera de cualquier caja o estilo.

**Qué pasaba:** el mensaje tenía una doble negación. Las plantillas mostraban `{{error}}` suelto, sin contenedor. También, `request.POST['username']` lanzaba `KeyError` (error 500) si la petición llegaba sin ese campo.

**Dónde:** `books/views.py` (`signin`), `signin.html`, `signup.html`, `static/style.css`.

**Código anterior** (`views.py`):
```python
user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
if user is None:
    return render(request, 'signin.html', {'form': SignInForm(), 'error': 'El usuario o la contraseña no son incorrectos'})
```

**Código corregido** (`views.py`):
```python
username = request.POST.get('username', '')
user = authenticate(request, username=username, password=request.POST.get('password', ''))
if user is None:
    return render(request, 'signin.html', {
        'form': SignInForm(initial={'username': username}),
        'error': 'El usuario o la contraseña son incorrectos.',
    })
```
Además, el usuario escrito se conserva en el formulario para no tener que teclearlo de nuevo.

**Código anterior** (`signin.html` y `signup.html`):
```html
{% block content %}
{{error}}
<div class = "d-flex flex-column ...">
```

**Código corregido:**
```html
<div class="p-3 rounded formOutline" style="background-color:#FFFFFF">
    {% if error %}
        <div class="alert alert-danger" role="alert">{{ error }}</div>
    {% endif %}
    <form ...>
```

**Código nuevo** (`style.css`), para los errores por campo que Django genera como `<ul class="errorlist">`:
```css
ul.errorlist{
    list-style: none;
    padding: 0.4rem 0.75rem;
    margin: 0 0 0.5rem 0;
    color: #721c24;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    font-size: 0.875rem;
}
```

---

### H03 · Contraseñas débiles aceptadas

**Error:** el registro aceptaba contraseñas como `123`.

**Qué pasaba:** la vista `signup` creaba el usuario con `User.objects.create_user(...)` directamente. Ese método **no ejecuta** los validadores de `AUTH_PASSWORD_VALIDATORS` (longitud mínima, contraseñas comunes, solo números y parecido al usuario), aunque estaban configurados en `settings.py`. El formulario `SignUpForm` (basado en `UserCreationForm`) se mostraba, pero nunca se usaba para validar.

**Reproducción (antes):** `POST /signup/ password1="123" password2="123"` → `302` y usuario creado.

**Dónde:** `books/views.py` (`signup`).

**Código anterior:**
```python
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': SignUpForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            # Registrar el usuario
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('books')
            except IntegrityError:
                return render(request, 'signup.html', {'form': SignUpForm(), 'error': 'El usuario ya existe'})
        return render(request, 'signup.html', {'form': SignUpForm(), 'error': 'Las contraseñas no coinciden'})
```

**Código corregido:**
```python
def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': SignUpForm()})
    else:
        # UserCreationForm valida: usuario duplicado, contraseñas que no coinciden
        # y los AUTH_PASSWORD_VALIDATORS de settings.py (longitud, comunes, numéricas...)
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('books')
        return render(request, 'signup.html', {'form': form, 'error': 'No se pudo crear la cuenta. Revisa los campos marcados.'})
```

**Resultado (después):** `password="123"` → `200`, el usuario **no** se crea y se muestran los motivos en español:
- *"Su contraseña es muy corta. Debe contener al menos 8 caracteres."*
- *"Su contraseña no puede ser una contraseña de uso común."*
- *"Su contraseña no puede ser muy similar a su otra información personal."*

Una contraseña robusta (`Lectura-2026!x`) se acepta con `302`. Los casos de usuario duplicado y contraseñas distintas siguen cubiertos, ahora por el propio formulario, que además conserva lo escrito. Se eliminó el `import IntegrityError`, que ya no se usa.

---

### H09 · El progreso del PDF solo sube

**Error:** si el usuario saltaba a la página 250 del PDF para consultar algo, la app la marcaba como leída. Al regresar a la página donde iba, el progreso no bajaba. Además, esas 250 páginas se sumaban a las estadísticas (récord diario y páginas del mes).

**Qué pasaba:** el visor (`book_detail.html`) enviaba al servidor **cualquier** página mayor a la última guardada, sin distinguir entre leer y consultar: botón «Siguiente», flecha y salto con el campo "Pág." se trataban igual. A su vez, el endpoint `update_pdf_progress` solo aceptaba aumentos (`if current_page > last_pages_read`), así que no había forma de corregir el progreso hacia atrás.

**Reproducción (antes):** saltar a la página 250 y volver a la 10 → `pages_read = 250`.

**Dónde:** `books/templates/book_detail.html` (JavaScript del visor) y `books/views.py` (`update_pdf_progress`).

**Solución aplicada: lectura vs. consulta.**
- **Lectura:** avanzar con «Siguiente» o ▶ **desde una página ya leída o desde la siguiente por leer** sí guarda el progreso.
- **Consulta:** saltar con el campo "Pág.", avanzar desde una página a la que se saltó o retroceder **no** modifica el progreso. Se muestra una barra amarilla de *"🔎 Modo consulta: esta página no cuenta como leída. Tu progreso sigue en la pág. N."*
- **Guardado explícito:** la barra incluye el botón *"📌 Guardar esta página como mi progreso"*, que fija el avance en la página visible, hacia adelante o hacia atrás. Sirve si el usuario leyó en otro lado o quiere corregir.
- **Servidor:** el endpoint acepta ahora correcciones hacia atrás. Las estadísticas se ajustan con la diferencia, que puede ser negativa (ver H10).

**Código anterior** (`book_detail.html`):
```javascript
let lastSavedPage = {{ book.pages_read }};
...
function onPrevPage() {
    if (pageNum <= 1) return;
    pageNum--;
    queueRenderPage(pageNum);
    // Si avanzamos más allá de lo registrado, sincronizamos
    if (pageNum > lastSavedPage) {
        syncProgress(pageNum, totalPdfPages);
    }
}

function onNextPage() {
    if (pageNum >= totalPdfPages) return;
    pageNum++;
    queueRenderPage(pageNum);
    if (pageNum > lastSavedPage) {
        syncProgress(pageNum, totalPdfPages);
    }
}

// Salto directo a página
pageNumInput.addEventListener('change', function() {
    ...
    pageNum = val;
    queueRenderPage(pageNum);
    if (pageNum > lastSavedPage) {
        syncProgress(pageNum, totalPdfPages);
    }
});
```

**Código corregido** (`book_detail.html`):
```javascript
// Última página contada como leída (el "progreso"). Solo avanza leyendo en orden
// desde aquí, o con el botón "Guardar esta página como mi progreso" (H09).
let readingFrontier = {{ book.pages_read }};
...
function onPrevPage() {
    if (pageNum <= 1) return;
    pageNum--;
    // Retroceder nunca modifica el progreso (es relectura o consulta)
    queueRenderPage(pageNum);
}

function onNextPage() {
    if (pageNum >= totalPdfPages) return;
    const fromPage = pageNum;
    pageNum++;
    queueRenderPage(pageNum);
    // Solo cuenta como LECTURA si se avanza desde una página ya leída o desde la
    // siguiente por leer. Si se avanza desde una página saltada (consulta), no cuenta.
    if (fromPage <= readingFrontier + 1 && pageNum > readingFrontier) {
        readingFrontier = pageNum;
        syncProgress(pageNum, totalPdfPages);
    }
    updateConsultBar();
}

// Salto directo a página: es una CONSULTA, no marca páginas como leídas
pageNumInput.addEventListener('change', function() {
    ...
    pageNum = val;
    queueRenderPage(pageNum);
});

// Guardado explícito: el usuario decide que la página visible es su progreso
saveHereBtn.addEventListener('click', function() {
    readingFrontier = pageNum;
    syncProgress(pageNum, totalPdfPages);
    updateConsultBar();
});

function updateConsultBar() {
    const consulting = pageNum > readingFrontier + 1 || pageNum < readingFrontier;
    frontierNumSpan.textContent = readingFrontier;
    consultBar.classList.toggle('d-none', !consulting);
    consultBar.classList.toggle('d-flex', consulting);
}
```

Otros ajustes en el visor:
- El frente de lectura se actualiza **en el momento** y no al recibir la respuesta del servidor, para que varios «Siguiente» rápidos (con el debounce de 300 ms) se cuenten bien.
- Al calibrar el total con el PDF se envía el progreso real (`readingFrontier`) en lugar de la página visible. Antes, un libro con 0 páginas leídas quedaba marcado con la página 1.
- La insignia "✅ Libro Completado" se oculta si el progreso baja del total.

**Código anterior** (`views.py`, `update_pdf_progress`):
```python
last_pages_read = book.pages_read
if current_page > 0:
    if current_page > book.pages_total:
        current_page = book.pages_total

    # Solo incrementamos si avanzó más allá de lo leído previamente
    if current_page > last_pages_read:
        pages_diff = current_page - last_pages_read
        book.pages_read = current_page
        updated_fields = True
        if book.pages_read >= book.pages_total:
            book.date_completed = timezone.now().date()
        else:
            book.date_completed = None
        # ... ~20 líneas de cálculo manual de récord y mes (ver H10) ...
        profile.save()
```

**Código corregido** (`views.py`, `update_pdf_progress`):
```python
last_pages_read = book.pages_read
if current_page > book.pages_total:
    current_page = book.pages_total
if current_page > 0 and current_page != last_pages_read:
    pages_diff = current_page - last_pages_read
    book.pages_read = current_page
    updated_fields = True

    # Si alcanzó el final del PDF, marcar como completado (conservando la fecha original)
    if book.pages_read >= book.pages_total:
        if not book.date_completed:
            book.date_completed = timezone.localdate()
    else:
        book.date_completed = None

    # Actualizar estadísticas (récord diario y mes actual) en el perfil del lector
    profile.register_pages(pages_diff)
elif last_pages_read > book.pages_total:
    # El PDF tiene menos páginas que lo registrado: recortar el avance al nuevo total
    book.pages_read = book.pages_total
    if not book.date_completed:
        book.date_completed = timezone.localdate()
    updated_fields = True
```

**Resultado (después):**
- **Navegador:** saltar a la página 250 ya no se guarda y aparece la barra de "Modo consulta".
- **Servidor:** si se guarda la 250 y luego la 10 de forma explícita, `pages_read = 10` y las estadísticas se corrigen.

---

### H10 · Estadísticas del mes y del récord mal calculadas

**Error:**
1. **Mes:** el contador "Páginas leídas este mes" se reiniciaba según el mes de la **fecha del récord**, no según el mes actual. Si el récord era de un mes anterior, **cada** lectura nueva ponía el contador en 0 antes de sumar, así que nunca acumulaba. Si no se leía nada en el mes nuevo, seguía mostrando las páginas del mes pasado.
2. **Récord diario:** se mezclaba la suma del día con el máximo histórico. Cada lectura suelta se comparaba contra el récord y la suma del día no se guardaba en ninguna parte. Leer 30 + 30 páginas en un día con un récord previo de 50 dejaba el récord en 50, aunque ese día se leyeron 60.

**Reproducción (antes):**
```
Récord del mes pasado, hoy se leen 5 + 5 páginas      -> pages_this_month = 5   (esperado 10)
Récord previo 50 (ayer), hoy se leen 30 + 30 páginas   -> récord = 50            (esperado 60, hoy)
```

**Dónde:** `books/models.py` (`Profile`) y la lógica duplicada en tres vistas de `books/views.py` (`create_book`, `book_detail` y `update_pdf_progress`).

**Código anterior** (repetido con pequeñas variaciones en las 3 vistas):
```python
today = timezone.now().date()
current_month = today.month
# Actualizar récord diario/máximo
if profile.date_most_pages_read == today:
    profile.most_pages_read += pages
else:
    if pages > profile.most_pages_read:
        profile.most_pages_read = pages
        profile.date_most_pages_read = today
if profile.most_pages_read < 0:
    profile.most_pages_read = 0
# Reiniciar contador mensual si cambió el mes
if profile.date_most_pages_read and profile.date_most_pages_read.month != current_month:
    profile.pages_this_month = 0
profile.pages_this_month += pages
if profile.pages_this_month < 0:
    profile.pages_this_month = 0
profile.save()
```

**Solución:** se agregó un registro diario de lectura, el nuevo modelo `DailyReading` con una fila por usuario y día. Las estadísticas **se calculan** a partir de él en un solo lugar:
- **Récord:** el día con más páginas.
- **Mes:** la suma de los días del mes actual.

Los campos de `Profile` se conservan como valores calculados, así que las plantillas y los tests siguen funcionando.

**Código nuevo** (`models.py`):
```python
class DailyReading(models.Model):
    """Páginas leídas por un usuario en un día concreto (fecha local)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_readings', verbose_name='Usuario')
    date = models.DateField('Fecha')
    pages = models.PositiveIntegerField('Páginas leídas', default=0)

    class Meta:
        verbose_name = 'Lectura diaria'
        verbose_name_plural = 'Lecturas diarias'
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_daily_reading_per_user'),
        ]


class Profile(models.Model):
    ...
    def register_pages(self, pages):
        """Suma (o resta, si es negativo) páginas a la lectura de HOY y recalcula estadísticas."""
        if pages:
            today = timezone.localdate()
            log, _ = DailyReading.objects.get_or_create(user=self.user, date=today)
            log.pages = max(0, log.pages + pages)
            log.save()
        self.refresh_stats()

    def refresh_stats(self):
        """Recalcula récord diario y acumulado del mes actual desde DailyReading."""
        today = timezone.localdate()
        logs = DailyReading.objects.filter(user=self.user)

        best = logs.filter(pages__gt=0).order_by('-pages', '-date').first()
        if best:
            self.most_pages_read = best.pages
            self.date_most_pages_read = best.date
        else:
            self.most_pages_read = 0
            self.date_most_pages_read = None

        month_total = logs.filter(
            date__gte=today.replace(day=1), date__lte=today
        ).aggregate(total=models.Sum('pages'))['total']
        self.pages_this_month = month_total or 0
        self.save()
```

**Código corregido** en las vistas (las ~20 líneas repetidas se reemplazan por una sola llamada):
```python
# create_book
profile.register_pages(pages_read)

# book_detail (diferencia respecto al valor anterior; puede ser negativa si el usuario corrige)
profile.register_pages(pages_read - last_pages_read)

# update_pdf_progress
profile.register_pages(pages_diff)

# dashboard: recalcular antes de mostrar, para que el mes se reinicie aunque no se haya leído nada
profile.refresh_stats()
```

**Resultado (después):**
```
Récord del mes pasado, hoy se leen 5 + 5               -> pages_this_month = 10       ✅
Récord previo 50 (ayer), hoy se leen 30 + 30           -> récord = 60 (hoy)           ✅
Corrección hacia atrás de 60 a 1 página hoy            -> el récord vuelve a 50 (ayer) ✅
Mes nuevo sin lecturas (con 999 guardado del anterior)  -> pages_this_month = 0         ✅
```

También se registró `DailyReading` en el panel de administración (`admin.py`) para poder revisar las lecturas por día.

---

### H12 · Contraste insuficiente

**Error:** varios botones no cumplían el contraste mínimo WCAG AA, de 4.5:1 para texto normal.

**Qué pasaba:** el botón principal (`formButtonColor`) tenía texto blanco sobre beige y el botón de eliminar tenía texto negro sobre rojo. Además, los enlaces del menú usaban el gris semitransparente de Bootstrap (`rgba(0,0,0,.5)`) sobre el beige de la barra.

**Dónde:** `static/style.css`.

**Contrastes medidos** (fórmula de luminancia relativa WCAG 2.x):

| Elemento | Antes | Contraste | Después | Contraste |
|---|---|---|---|---|
| Botón principal (`formButtonColor`) | `#FFFFFF` sobre `#DCBD9E` | **1.78:1** ❌ | `#1A202C` sobre `#DCBD9E` | **9.18:1** ✅ |
| Botón principal (hover) | gris Bootstrap | 6.21:1 | `#1A202C` sobre `#C9A27C` | **6.95:1** ✅ |
| Botón eliminar (`deleteButtonColor`) | `#000000` sobre `#E02626` | **4.47:1** ❌ | `#FFFFFF` sobre `#B91C1C` | **6.47:1** ✅ |
| Enlaces del menú (adicional) | `rgba(0,0,0,.5)` sobre `#DCBD9E` | **3.50:1** ❌ | `rgba(0,0,0,.8)` sobre `#DCBD9E` | **8.41:1** ✅ |

**Código anterior:**
```css
.formButtonColor{
    background-color: #DCBD9E;
    color: #FFFFFF;
}
.deleteButtonColor{
    background-color: #e02626;
    color: black;
}
```

**Código corregido:**
```css
/* Contraste (H12): antes texto blanco sobre beige = 1.78:1. Texto oscuro sobre beige = 9.18:1 */
.formButtonColor{
    background-color: #DCBD9E;
    color: #1A202C;
    border-color: #C9A27C;
}
.formButtonColor:hover,
.formButtonColor:focus{
    background-color: #C9A27C;
    color: #1A202C;
}
/* Contraste (H12): antes texto negro sobre #e02626 = 4.47:1. Texto blanco sobre #B91C1C = 6.47:1 */
.deleteButtonColor{
    background-color: #B91C1C;
    border-color: #B91C1C;
    color: #FFFFFF;
}
/* Contraste (H12): enlaces del menú de 3.5:1 a 8.41:1 */
.navbar-light.navcolor .navbar-nav .nav-link{
    color: rgba(0, 0, 0, 0.8);
}
.navbar-light.navcolor .navbar-nav .nav-link:hover,
.navbar-light.navcolor .navbar-nav .active > .nav-link{
    color: #000000;
}
```
Los botones "Completar" (verde, 13.0:1) y "Actualizar" (amarillo, 15.5:1) ya cumplían y no se modificaron.

---

### H16 · Guardar un libro puede tardar ~22 s sin avisar

**Error:** al crear un libro sin portada, el servidor consulta Google Books, luego Open Library como respaldo y después descarga la portada. Con timeouts de 6, 8 y 8 segundos, si los servicios no respondían el guardado podía tardar unos 22 s. Mientras tanto la pantalla no mostraba nada, y el usuario podía pensar que se colgó y volver a pulsar el botón, lo que creaba el libro duplicado.

**Dónde:** `books/views.py` (`_fetch_google_books`, `_download_and_save_cover`) y `books/templates/create_book.html`.

**Código anterior** (`views.py`):
```python
gb_response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params, timeout=6)
...
ol_response = requests.get('https://openlibrary.org/search.json', params={...}, timeout=8)
...
img_response = requests.get(cover_url, headers=headers, timeout=8)
```

**Código corregido** (`views.py`):
```python
# Timeout (conexión, lectura) en segundos para las APIs externas de libros y portadas.
# Antes eran 6 s, 8 s y 8 s (hasta ~22 s acumulados al guardar un libro sin portada).
API_TIMEOUT = (3, 4)
...
gb_response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params, timeout=API_TIMEOUT)
ol_response = requests.get('https://openlibrary.org/search.json', params={...}, timeout=API_TIMEOUT)
img_response = requests.get(cover_url, headers=headers, timeout=API_TIMEOUT)
```

**Código anterior** (`create_book.html`):
```html
<button type="submit" class="formButtonColor btn btn-secondary btn-block">Crear Libro</button>
```

**Código corregido** (`create_book.html`):
```html
<button type="submit" id="createBookSubmit" class="formButtonColor btn btn-secondary btn-block">Crear Libro</button>
<!-- Indicador de guardado (H16): guardar puede tardar si se consultan portadas/datos en línea -->
<div id="createBookSaving" class="alert alert-info text-center mt-2 mb-0 d-none" role="status" aria-live="polite">
    <span class="spinner-border spinner-border-sm mr-2" aria-hidden="true"></span>
    Guardando libro… si no tiene portada se buscan sus datos en línea, esto puede tardar unos segundos.
</div>
```
```javascript
// Indicador de "guardando" y bloqueo del botón para evitar envíos dobles (H16)
formEl.addEventListener('submit', function() {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Guardando…';
    savingBox.classList.remove('d-none');
});
// Si el usuario vuelve con el botón "Atrás", restaurar el botón
window.addEventListener('pageshow', function() {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Crear Libro';
    savingBox.classList.add('d-none');
});
```

**Resultado:**
- **Aviso:** al pulsar «Crear Libro» aparece de inmediato el indicador "Guardando…" y el botón se bloquea, así que ya no hay envíos dobles.
- **Tiempo de espera:** si los servicios externos no responden, cada intento de conexión se corta a los 3 s. El caso de "servicio caído" baja de unos 22 s a unos 9 s.

**Límite:** el timeout de `requests` es por fase (conexión y lectura), no un total. Un servidor que responde muy lento pero sin cortarse todavía puede alargar la espera. Por eso la corrección principal es el aviso visible.

---

### H05 · Dashboard confuso

**Error:** el récord se mostraba como una fecha grande (`<h1>`) sin ninguna etiqueta que dijera qué era. Si no había récord, el `<h1>` quedaba vacío y debajo solo aparecía "0 páginas".

**Dónde:** `books/templates/dashboard.html`.

**Código anterior:**
```html
<div class= "col-8 mr-4 bg-light shadow" style="width=60%">
    <h1 class="mb-2">{{ profile.date_most_pages_read|date:'j M'  }}</h1>
    <h2 class="ml-4">{{ profile.most_pages_read }} páginas</h2>

    <h1 class="mb-2">Páginas leídas este mes:</h1>
    <h2 class="ml-4">{{profile.pages_this_month }}</h2>
 </div>
<div class= " col ml-4 bg-light shadow">
    <h1 class= "mb-2">Promedio de páginas por día </h1>
    <h2 class= "mb-2 ml-4">{{ profile.average_pages_for_day }} / Día</h2>
</div>
```

**Código corregido:** tres tarjetas con etiqueta propia, colocadas arriba del dashboard, y un mensaje cuando no hay datos.
```html
<div class="col-12 col-md-4 mb-3">
    <div class="bg-white shadow-sm rounded p-3 h-100">
        <h2 class="h6 text-uppercase text-muted mb-2">Récord de páginas en un día</h2>
        {% if profile.most_pages_read and profile.date_most_pages_read %}
            <p class="h3 mb-1">{{ profile.most_pages_read }} páginas</p>
            <p class="text-muted mb-0">el {{ profile.date_most_pages_read|date:'j \d\e F \d\e Y' }}</p>
        {% else %}
            <p class="text-muted mb-0">Aún no hay registros. Tu récord aparecerá cuando registres páginas leídas.</p>
        {% endif %}
    </div>
</div>
<!-- + tarjetas "Páginas leídas este mes" y "Promedio de páginas por día" -->
```
Además, si el usuario no tiene libros, el dashboard muestra *"Todavía no tienes libros registrados"* con un botón para agregar el primero.

---

### H06 · El inicio promete funciones que no existen

**Error:** la página de inicio prometía un *"Reading Wrapped"*, *"géneros favoritos"* y *"autores más leídos"*. Ninguna de esas estadísticas existe en el dashboard.

**Dónde:** `books/templates/home.html`.

**Decisión:** la lista de errores daba dos opciones, implementar esas funciones o ajustar el texto. Se **ajustó el texto** para describir solo lo que la app realmente hace. Implementar las estadísticas sería una funcionalidad nueva, que puede hacerse después aprovechando el nuevo registro `DailyReading` y los campos `category` y `autor`.

**Texto anterior:**
```html
<p class="mt-4">
    Inspirada en la idea de un <strong>"Reading Wrapped"</strong>, BookTracker transforma la experiencia lectora
    en algo más dinámico y significativo. Los usuarios pueden consultar datos como sus géneros favoritos, autores
    más leídos, número de libros por mes y más, todo dentro de una interfaz clara, moderna y pensada para brindar
    una experiencia agradable.
</p>
```

**Texto corregido:**
```html
<p class="mt-4">
    Busca tus libros en línea para completar automáticamente portada, páginas, género y sinopsis;
    adjunta el PDF para leerlo dentro de la app con tu avance sincronizado, y escribe notas o reseñas
    de cada lectura.
</p>

<p class="mt-4">
    En tus estadísticas verás tu récord de páginas leídas en un día, las páginas leídas en el mes,
    tu promedio diario y los libros que agregaste y terminaste cada mes. Además, cada libro te muestra
    cuántas páginas al día necesitas para terminarlo a tiempo.
</p>
```

---

## 4. Prioridad baja

### H08 · El dashboard agrupa por mes sin año

**Error:** las secciones "Agregados en…" y "Terminados en…" agrupaban solo por el nombre del mes. Los libros de enero de 2026 y enero de 2027 aparecían juntos bajo "Enero".

**Dónde:** `books/templates/dashboard.html`.

**Código anterior:**
```django
{% regroup books_created by created|date:"F" as created_list %}
...
{% regroup books_completed by date_completed|date:"F" as completed_list %}
```

**Código corregido:**
```django
<!-- Se agrupa por mes Y año para no mezclar, p. ej., enero 2026 con enero 2027 -->
{% regroup books_created by created|date:"F Y" as created_list %}
...
{% regroup books_completed by date_completed|date:"F Y" as completed_list %}
```

**Resultado:** con un libro de enero de 2026 y otro de enero de 2027 se generan dos grupos, `['Enero 2027', 'Enero 2026']`.

---

### H11 · Zona horaria UTC

**Error:** con `TIME_ZONE = 'UTC'`, para un usuario en México el "día" cambiaba a las 18:00 hora local (UTC−6). Lo leído en la noche se contaba para el día siguiente, lo que afectaba el récord diario, el mes y las fechas de término.

**Qué pasaba además:** aunque se cambiara `TIME_ZONE`, el código usaba `timezone.now().date()`. Con `USE_TZ = True`, `timezone.now()` devuelve la hora en **UTC**, así que `.date()` seguía dando la fecha UTC. Había que usar `timezone.localdate()`.

**Dónde:** `BookTracker/settings.py`, `books/views.py` y `books/models.py`.

**Código anterior:**
```python
# settings.py
TIME_ZONE = 'UTC'

# views.py (varios lugares)
today = timezone.now().date()
book.date_completed = timezone.now()

# models.py (Profile.average_pages_for_day)
dias = timezone.now().day
```

**Código corregido:**
```python
# settings.py
TIME_ZONE = 'America/Mexico_City'

# views.py / models.py
book.date_completed = timezone.localdate()
today = timezone.localdate()      # dentro de Profile.register_pages / refresh_stats
dias = timezone.localdate().day   # Profile.average_pages_for_day
```
El paquete `tzdata`, necesario en Windows, ya estaba en las dependencias.

---

### H13 · Biblioteca vacía sin mensaje

**Error:** un usuario sin libros veía la página "Library" en blanco, sin ninguna indicación de qué hacer.

**Dónde:** `books/templates/books.html`.

**Código anterior:**
```django
{% for book in books %}
    ...tarjeta...
{% endfor %}
```

**Código corregido:**
```django
{% for book in books %}
    ...tarjeta...
{% empty %}
<div class="col-12">
    <div class="text-center bg-white rounded shadow-sm p-5 mx-auto" style="max-width: 560px;">
        <div style="font-size: 3rem;" aria-hidden="true">📚</div>
        <h2 class="h4 mt-2">Tu biblioteca está vacía</h2>
        <p class="text-muted">Agrega tu primer libro para empezar a registrar tu progreso de lectura.</p>
        <a href="{% url 'create_book' %}" class="formButtonColor btn px-4">Agregar mi primer libro</a>
    </div>
</div>
{% endfor %}
```

---

### H14 · Libros sin portada y tarjetas desiguales

**Error:** los libros sin portada no mostraban ninguna imagen. Como cada tarjeta tenía una altura distinta (con o sin portada, con o sin meta), la cuadrícula quedaba desalineada.

**Dónde:** `books/templates/books.html` y `static/style.css`.

**Código anterior:**
```html
<div class="card mb-4 box-shadow shadow" style="width: 100%">
    <div class="card-body shadow">
        <a class="card-text" href="{% url 'book_detail' book.id %}" style="text-decoration: none;">
            {% if book.cover %}
                <img src="{{ book.cover.url }}" alt="{{ book.title }}" class="img-fluid rounded mb-2" style="max-height: 200px; object-fit: cover; width: 100%;">
            {% endif %}
```

**Código corregido:**
```html
<div class="card box-shadow shadow h-100">
    <a href="{% url 'book_detail' book.id %}" class="text-decoration-none">
        {% if book.cover %}
            <img src="{{ book.cover.url }}" alt="Portada de {{ book.title }}" class="card-img-top book-cover">
        {% else %}
            <div class="card-img-top book-cover book-cover-placeholder" role="img" aria-label="Libro sin portada">
                <span aria-hidden="true">📖</span>
                <small>Sin portada</small>
            </div>
        {% endif %}
    </a>
    <div class="card-body d-flex flex-column">
        ...
        <!-- mt-auto empuja el progreso al fondo para alinear todas las tarjetas -->
        <div class="mt-auto"> ...páginas y barra de progreso... </div>
    </div>
</div>
```
```css
/* Portadas de la biblioteca (H14): misma altura para todas las tarjetas */
.book-cover{
    height: 220px;
    width: 100%;
    object-fit: cover;
}
.book-cover-placeholder{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #F2E9DC, #DCBD9E);
    color: #4A3B2C;   /* contraste 6.05:1 sobre el tono más oscuro del degradado */
    font-size: 3rem;
}
```
**Resultado:**
- **Portada:** todas las tarjetas tienen un área de 220 px, con la imagen o con la portada de reemplazo "📖 Sin portada".
- **Altura:** `h-100` iguala la altura de las tarjetas de cada fila.
- **Progreso:** `mt-auto` alinea las barras de progreso en la parte inferior.

---

### H15 · Botones del inicio sin sesión y clase de Bootstrap 5

**Error:**
- **Botones sin sesión:** la página de inicio mostraba "Ver mi Biblioteca" y "Agregar Libro" a visitantes sin sesión, que al pulsarlos eran enviados al login.
- **Clase de Bootstrap 5:** el segundo botón usaba `ms-2`, que es de Bootstrap 5. La app carga Bootstrap 4.3.1, así que la clase no hacía nada y los botones quedaban pegados.

**Dónde:** `books/templates/home.html`.

**Código anterior:**
```html
<div class="text-center mt-4">
    <a href="{% url 'books' %}" class="btn btn-primary px-4 py-2">Ver mi Biblioteca</a>
    <a href="{% url 'create_book' %}" class="btn btn-outline-primary px-4 py-2 ms-2">Agregar Libro</a>
</div>
```

**Código corregido:**
```html
<!-- Botones: dependen de si hay sesión iniciada -->
<div class="text-center mt-4">
    {% if user.is_authenticated %}
        <a href="{% url 'books' %}" class="formButtonColor btn px-4 py-2 mb-2">Ver mi biblioteca</a>
        <a href="{% url 'create_book' %}" class="btn btn-outline-dark px-4 py-2 ml-2 mb-2">Agregar libro</a>
    {% else %}
        <a href="{% url 'signup' %}" class="formButtonColor btn px-4 py-2 mb-2">Crear cuenta</a>
        <a href="{% url 'signin' %}" class="btn btn-outline-dark px-4 py-2 ml-2 mb-2">Iniciar sesión</a>
    {% endif %}
</div>
```
También se cambió `btn-primary` (blanco sobre `#007BFF`, **3.98:1**, no cumple AA) por los colores del proyecto, que sí cumplen.

---

### H17 · HTML mal cerrado

**Error:**
1. `base.html` tenía un `<div>` donde debía ir `</div>`. El contenedor principal nunca se cerraba y además se abría uno nuevo vacío.
2. En `signin.html` y `signup.html`, el enlace `<a>` se cerraba con `</h1>`.
3. En ambas plantillas, el `<div>` exterior del formulario tampoco se cerraba.

Los navegadores "adivinan" cómo reparar este HTML. El resultado puede variar entre navegadores y romper el diseño.

**Dónde:** `books/templates/base.html`, `signin.html`, `signup.html`.

**Código anterior** (`base.html`):
```html
<div class="d-flex justify-content-center pagebg">
    {% block content %}
    {% endblock %}
<div>
```

**Código corregido** (`base.html`):
```html
<div class="d-flex justify-content-center pagebg">
    {% block content %}
    {% endblock %}
</div>
```

**Código anterior** (`signin.html`; `signup.html` igual con "Already have an account? Sign In"):
```html
<div class="d-flex p-2 justify-content-center">
            <a href="/signup">Not registered? Sign Up</h1>
</div>
</div>
{% endblock %}
```

**Código corregido** (`signin.html`):
```html
        <div class="d-flex p-2 justify-content-center">
            <a href="/signup">¿No tienes cuenta? Regístrate</a>
        </div>
    </div>
</div>
{% endblock %}
```

**Verificación:** se analizó el HTML renderizado de las 7 páginas principales (inicio, iniciar sesión, registro, biblioteca, estadísticas, agregar libro y detalle) con un parser que comprueba que cada etiqueta abierta se cierre en orden. Todas quedaron balanceadas.

---

## 5. Error nuevo: `/complete` y `/delete` por GET dan error 500

**Error:** si alguien abría por GET las rutas `/books/<id>/complete` o `/books/<id>/delete` (escribiéndolas en la barra, desde un enlace o al recargar), la app respondía con **error 500**.

**Qué pasaba:** las vistas solo tenían código dentro de `if request.method == 'POST':`. En cualquier otro caso la función terminaba sin devolver nada (`None`), y Django lanza `ValueError: The view ... didn't return an HttpResponse object`.

**Reproducción (antes):** `GET /books/1/complete` → `500`. `GET /books/1/delete` → `500`.

**Dónde:** `books/views.py` (`complete_book`, `delete_book`).

**Código anterior:**
```python
@login_required
def complete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method == 'POST':
        book.pages_read = book.pages_total
        book.date_completed = timezone.now()
        book.save()
        return redirect('books')

@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method == 'POST':
        book.delete()
        return redirect('books')
```

**Código corregido:**
```python
@login_required
def complete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method != 'POST':
        # Abrir la URL por GET (enlace, recarga, escribirla a mano) ya no da error 500
        return redirect('book_detail', book_id=book.id)
    book.pages_read = book.pages_total
    if not book.date_completed:
        book.date_completed = timezone.localdate()
    book.save()
    return redirect('books')

@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method != 'POST':
        # Abrir la URL por GET ya no da error 500; nunca se borra nada por GET
        return redirect('book_detail', book_id=book.id)
    book.delete()
    return redirect('books')
```

**Decisión:** se eligió **redirigir** a la ficha del libro en vez de devolver 405, porque estas rutas las abre una persona en el navegador y una página 405 en blanco no le ayuda. Por seguridad, la acción solo se ejecuta por POST, con el token CSRF. Un libro ajeno sigue devolviendo 404.

**Cambio relacionado:** antes, `book_detail` llamaba a la **vista** `complete_book(request, book_id)` como si fuera una función auxiliar e ignoraba su respuesta. Ahora `book_detail` marca el libro como completado directamente. Tanto `book_detail` como `complete_book` **conservan la fecha de término original** si el libro ya estaba terminado. Antes, editar las notas de un libro terminado le cambiaba la fecha de término a hoy y lo movía de mes en el dashboard (H08).

**Resultado (después):**
```
GET  /books/1/complete  ->  302 a /books/1/  (sin cambios en el libro)
GET  /books/1/delete    ->  302 a /books/1/  (el libro sigue existiendo)
POST /books/1/complete  ->  302 a /books/    (funciona igual que antes)
POST /books/2/delete    ->  302 a /books/    (libro borrado)
```

---

## 6. Cambios en la base de datos (migración 0004)

Se creó `books/migrations/0004_traducciones_y_lectura_diaria.py`, que incluye:
1. **`AlterField`** en los campos de `Book`: solo agrega los `verbose_name` en español (H01). No cambia columnas ni datos.
2. **`CreateModel DailyReading`**: crea la tabla del registro diario de lectura (H10), con la restricción de una fila por usuario y día.
3. **`RunPython seed_daily_readings_from_profiles`**: conserva el récord existente. Por cada perfil con récord crea una lectura diaria con esas páginas en esa fecha, para que no se pierda al pasar al nuevo cálculo.

```python
def seed_daily_readings_from_profiles(apps, schema_editor):
    Profile = apps.get_model('books', 'Profile')
    DailyReading = apps.get_model('books', 'DailyReading')
    for profile in Profile.objects.exclude(date_most_pages_read__isnull=True).filter(most_pages_read__gt=0):
        DailyReading.objects.get_or_create(
            user_id=profile.user_id,
            date=profile.date_most_pages_read,
            defaults={'pages': profile.most_pages_read},
        )
```

**Para aplicarla:**
```bash
python manage.py migrate
```

**Verificación con datos reales:** la migración se probó sobre una **copia** de la base de datos local, sin tocar la original. Se aplicó sin errores y los 4 perfiles con récord lo conservaron con el mismo número de páginas y la misma fecha, por ejemplo 559 páginas el 09/11/2025.

**Limitación:** el contador "páginas de este mes" anterior no se puede repartir por días porque no se sabe en qué fecha se leyó cada página. Además, por el error H10, ese valor no era confiable. A partir de la migración el contador del mes se calcula solo con las lecturas registradas, y el récord histórico sí se conserva.

---

## 7. Pruebas y verificación

### Suite automatizada (`python manage.py test books`)

```
Ran 30 tests
FAILED (failures=3)
```

- **27 de 30 pasan**, las mismas que pasaban antes de los cambios.
- **Las 3 que fallan ya fallaban antes** y no tienen relación con estas correcciones. Están escritas para documentar "fallas detectadas" del reporte de pruebas del Milestone:
  - `test_ivt_3`: espera un 302 al enviar más páginas leídas que totales, cuando lo correcto es mostrar el error (200).
  - `test_mvt_4`: espera 99 % para un libro de 100/100 páginas.
  - `test_svt_8`: espera que un libro borrado siga apareciendo en la biblioteca.

  Se verificó en la rama sin cambios que fallan exactamente igual.

**Test ajustado:** `test_mvt_8_profile_reading_record_update` calculaba el día esperado con `timezone.now().day`, que es el día en UTC. Se cambió a `timezone.localdate().day`, porque ahora el promedio usa el día local (H11). Sin el ajuste, el test fallaría todos los días entre las 18:00 y las 24:00 hora de México.

```python
# Antes
day = timezone.now().day
# Después
day = timezone.localdate().day  # día local (TIME_ZONE), no el día en UTC
```

### Verificación específica de cada corrección

Se escribió un script de reproducción que usa una base de datos de prueba en memoria y simula las APIs externas. Resultado:

```
H04 crear pages_read vacio -> 302 | creado con 0: True
H04 editar pages_read vacio -> 302
H04 editar pages_total vacio -> 200 | muestra error de campo: True
H04 leidas > totales -> 200 | True
NUEVO GET complete -> 302 /books/1/
NUEVO GET delete -> 302 /books/1/ | libro sigue: True
NUEVO POST delete sigue funcionando -> 302 | borrado: True
H02 mensaje corregido: True | alerta con estilo: True
H02 signin POST sin campos -> 200
H03 "123" -> 200 | creado: False
H03 contraseña fuerte -> 302 | creado: True
H09 servidor acepta correccion hacia atras -> pages_read = 10
H10a 5+5 este mes con record del mes pasado -> pages_this_month = 10
H10b 30+30 hoy vs record 50 -> record = 60 | fecha hoy: True
H10c correccion hacia atras (60->1) -> record vuelve a 50
H10d mes nuevo sin lecturas -> mes = 0 | record conservado = 40
H11 TIME_ZONE = America/Mexico_City
H08 grupos: ['Enero 2027', 'Enero 2026']
H05 dashboard sin datos muestra mensaje: True | etiqueta record: True
H07 dashboard sin col-4 fija: True
H13 biblioteca vacia: True | boton: True
H14 placeholder sin portada: True | H07 columnas: True
H15 inicio sin sesion: oculta biblioteca: True | muestra crear cuenta: True | ms-2: False
H15 inicio con sesion muestra biblioteca: True
H06 texto sin promesas inexistentes: True
H01 lang/titulo/etiquetas: True True True
H01 menu sin ingles: True
H16 indicador guardando: True | API_TIMEOUT = (3, 4)
H17 HTML balanceado: home, signin, signup, books, dashboard, create, detail -> True
JS detail / create: sintaxis OK (node --check sobre el HTML renderizado)
```

Además:
- **Django:** `python manage.py check` no reporta problemas y `makemigrations --check` no detecta cambios pendientes.

**Pendiente de prueba manual en navegador:**
- El "modo consulta" del visor PDF (H09).
- El diseño en celular (H07).
- El indicador "Guardando…" (H16).

La lógica y la sintaxis se verificaron, pero no se ejecutaron en un navegador real.

---

## 8. Archivos modificados

| Archivo | Hallazgos |
|---|---|
| `BookTracker/settings.py` | H11 |
| `books/models.py` | H01, H04, H10, H11 |
| `books/forms.py` | H04 |
| `books/views.py` | H02, H03, H04, H09, H10, H11, H16, nuevo |
| `books/admin.py` | H10 (registro de `DailyReading`) |
| `books/migrations/0004_traducciones_y_lectura_diaria.py` | H01, H10 (**nuevo**) |
| `books/templates/base.html` | H01, H17 |
| `books/templates/books.html` | H01, H07, H13, H14 |
| `books/templates/dashboard.html` | H01, H05, H07, H08 |
| `books/templates/home.html` | H06, H15 |
| `books/templates/signin.html` | H01, H02, H17 |
| `books/templates/signup.html` | H01, H02, H17 |
| `books/templates/create_book.html` | H01, H16 |
| `books/templates/book_detail.html` | H09 |
| `static/style.css` | H02, H12, H14 |
| `books/tests.py` | Ajuste de `test_mvt_8` por H11 |
| `README.md` | Documentación del modo consulta, `DailyReading` y migración 0004 |

---

## 9. Notas y decisiones de diseño

- **H09, cambio de comportamiento:** saltar a una página ya no la marca como leída. El progreso solo avanza leyendo en orden con «Siguiente» desde donde se va, o con el botón «📌 Guardar esta página como mi progreso». Retroceder nunca baja el progreso automáticamente. Para corregirlo hacia atrás se usa el mismo botón o el formulario de edición.
- **H10, fuente única de verdad:** las estadísticas se calculan desde `DailyReading` en `Profile.register_pages()` y `Profile.refresh_stats()`, en lugar de tres copias de la misma lógica en tres vistas. Este registro diario también sirve de base para futuras estadísticas, como un "Reading Wrapped" real (ver H06).
- **H10, correcciones negativas:** si el usuario corrige páginas hacia atrás, se restan **del día de hoy** (mínimo 0). No se modifican días anteriores, porque no se sabe qué día se leyeron las páginas corregidas.
- **Marcar como completado:** igual que antes, «Marcar como Completado» no suma páginas a las estadísticas, porque el usuario pudo haber leído el libro fuera de la app. Solo se cambió que ahora conserva la fecha de término original.
- **H06:** se optó por ajustar el texto. Si se desea implementar "géneros favoritos" y "autores más leídos", los datos ya existen (`Book.category`, `Book.autor`).
