# 📚 BookTracker

**BookTracker** es una aplicación web integral desarrollada con **Python** y **Django** diseñada para gestionar, dar seguimiento y gamificar el hábito de lectura personal. Permite a los usuarios registrar sus libros, controlar su progreso diario de lectura, calcular metas a corto plazo, subir archivos PDF y portadas, y consultar estadísticas personales.

El sistema incorpora un **buscador predictivo en tiempo real** con enriquecimiento bibliográfico híbrido (**Google Books API** con fallback automático a **Open Library**), un **visor interactivo de PDFs** con sincronización automática de páginas en vivo, políticas de **limpieza automática de almacenamiento** y un panel de métricas ágiles (**Agile Dashboard**) para monitorear el desempeño del equipo de desarrollo a lo largo de los Sprints.

---

## 🚀 Características Principales

### 1. 🔍 Búsqueda Predictiva y Autocompletado en Tiempo Real
- **Buscador AJAX con debounce:** Permite buscar libros por título o autor conforme se escribe en la barra de búsqueda de creación de libros (`/books/create/`).
- **Autocompletado instantáneo:** Al seleccionar una edición con un clic, se rellenan automáticamente:
  - Título y autor(es).
  - Número exacto de páginas oficiales de la edición.
  - Género o categoría literaria.
  - Editorial y año de publicación.
  - Código ISBN-10 / ISBN-13.
  - Calificación promedio de lectores (estrellas y número de votos).
  - Sinopsis editorial oficial.
  - Enlace oficial para hojear el libro en línea (`preview_link`).
- **Descarga automática de portadas:** Si el usuario no sube una portada manualmente, el servidor descarga y almacena la portada oficial en alta definición.

### 2. 🌐 Arquitectura de Catálogo Híbrida (Google Books + Open Library Fallback)
- **Google Books API:** Motor de búsqueda primario con fichas técnicas enriquecidas y valoraciones de lectores.
- **Fallback Automático a Open Library:** Si no se dispone de una API Key o se alcanza el límite de cuota (HTTP 429), el sistema conmuta automáticamente a la API abierta de Open Library sin interrumpir la experiencia del usuario.

### 3. 📄 Visor de PDF Interactivo y Sincronización en Vivo (Mozilla PDF.js)
- **Renderizado nativo en Canvas HTML5:** Sustituye los antiguos `<iframe>` estáticos por un lector fluido e interactivo sin depender de plugins de terceros.
- **Resolución inteligente del conflicto de páginas ("El PDF manda"):** Si la edición física registrada en el catálogo tiene un conteo de páginas diferente al archivo PDF digital subido por el usuario (ej. 110 págs. impresas vs. 25 págs. en el PDF), el visor detecta las páginas reales del documento (`pdfDoc.numPages`) y calibra automáticamente `pages_total = 25`.
- **Sincronización en tiempo real:**
  - Al avanzar páginas en el visor, una petición asíncrona guarda el progreso en el backend.
  - **Actualización dinámica de la interfaz:** La barra de progreso, el porcentaje (`XX%`), los campos de edición y la tabla de ritmo diario se recalculan en vivo sin necesidad de recargar la página.
  - Al llegar a la última página, el libro se marca automáticamente como completado (`✅ Libro Completado`).
- **Controles de lectura:** Botones Anterior/Siguiente, input para saltar a cualquier página, zoom interactivo (acercar, alejar y ajustar al ancho) y soporte para atajos de teclado (flechas `◀` / `▶` o `RePág` / `AvPág`).
- **Reanudación de sesión:** El visor abre automáticamente en la última página leída.

### 4. 🧹 Limpieza Automática de Almacenamiento (Cero Archivos Huérfanos)
- **Borrado físico de archivos (`post_delete`):** Al eliminar un libro de la biblioteca, sus archivos asociados en `media/covers/` y `media/pdfs/` se borran físicamente del disco duro de inmediato.
- **Reemplazo limpio (`pre_save`):** Si un usuario actualiza un libro y reemplaza una portada o un PDF anterior por uno nuevo, el archivo viejo es purgado del disco para evitar acumulación de basura.

### 5. 📓 Notas y Reseñas Personales
- Cada libro cuenta con un espacio dedicado (`user_notes`) para que el lector guarde reflexiones personales, citas textuales destacadas o resúmenes de sus lecturas.

### 6. 📊 Perfil de Lectura y Gamificación
- Cálculo automático de récords de lectura en un solo día (`most_pages_read`).
- Acumulado de páginas leídas en el mes corriente y promedio diario estimado.
- Proyección de ritmo de lectura: tabla calculada de páginas diarias necesarias para terminar el libro en plazos de 1 a 10 días.

### 7. 🔐 Seguridad y Gestión de Credenciales
- Protección estricta de credenciales mediante `.env` (excluido en `.gitignore`).
- Plantilla pública `.env.example` para despliegues sin exponer claves privadas.
- Cargador nativo ultraligero en `settings.py` sin dependencias externas pesadas.

### 8. 📈 Agile Dashboard
- Panel de control integrado con **Chart.js** que visualiza métricas de desarrollo de los Sprints (velocidad, previsibilidad, cobertura de código, lead time y defectos).

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.12+, Django 6.1+
- **Base de Datos:** SQLite (desarrollo local con soporte para migraciones automáticas)
- **Frontend:** HTML5, CSS3 personalizado, Bootstrap 5, Chart.js
- **Lector PDF:** Mozilla PDF.js v3.11.174
- **APIs de Libros:** Google Books API v1, Open Library Search API & Covers API
- **Testing:** Pytest, Django Test Runner, Unittest Mock
- **Gestión de Entorno:** `uv` / `pip`

---

## 📁 Estructura del Proyecto

```text
BookTracker/
│
├── BookTracker/                # Configuración principal del proyecto Django
│   ├── settings.py             # Configuración general, cargador de .env, media y static
│   ├── urls.py                 # Enrutador global de URLs y endpoints AJAX
│   ├── wsgi.py / asgi.py       # Puntos de entrada para servidores web
│
├── books/                      # Aplicación principal de Django
│   ├── data/
│   │   └── metrics.json        # Datos históricos de Sprints para el Agile Dashboard
│   ├── migrations/             # Migraciones del esquema de base de datos (0001 a 0003)
│   ├── templates/              # Plantillas HTML con renderizado dinámico
│   │   ├── base.html           # Layout base con navbar responsiva
│   │   ├── home.html           # Pantalla de bienvenida
│   │   ├── signup.html         # Formulario de registro
│   │   ├── signin.html         # Formulario de inicio de sesión
│   │   ├── books.html          # Biblioteca con tarjetas, badges y barras de progreso
│   │   ├── book_detail.html    # Ficha técnica, notas, edición y Visor PDF interactivo
│   │   ├── create_book.html    # Formulario con buscador predictivo y preview de portada
│   │   ├── dashboard.html      # Panel personal de lectura y estadísticas del perfil
│   │   └── agile_dashboard.html# Panel de métricas Scrum/Ágiles
│   ├── admin.py                # Configuración del panel de administración
│   ├── forms.py                # Formularios Django (BookForm, SignUpForm, SignInForm)
│   ├── models.py               # Modelos (Book, Profile) y señales de limpieza física
│   ├── tests.py                # Suites de pruebas unitarias (MVT), integración (IVT) y sistema (SVT)
│   └── views.py                # Lógica de controladores, búsquedas híbridas y endpoints
│
├── media/                      # Archivos multimedia subidos (ignorado en Git)
│   ├── covers/                 # Portadas (.jpg, .png)
│   └── pdfs/                   # Documentos PDF (.pdf)
│
├── static/                     # Archivos estáticos de frontend (CSS, imágenes)
│   └── style.css               # Estilos personalizados de la interfaz
│
├── .env                        # Variables de entorno locales con tu API Key (ignorado en Git)
├── .env.example                # Plantilla de variables de entorno para el repositorio
├── db.sqlite3                  # Base de datos local SQLite (ignorada en Git)
├── manage.py                   # CLI principal de Django
├── pyproject.toml / uv.lock    # Definición y bloqueo de dependencias con uv
├── requirements.txt            # Dependencias estándar para pip
│
└── Documentación de Desarrollo:
    ├── BUGFIX_REPORT.md        # Reporte 1: Corrección de migraciones y error NoneType
    ├── BUGFIX_REPORT2.md       # Reporte 2: Buscador interactivo y arquitectura con fallback
    ├── BUGFIX_REPORT3.md       # Reporte 3: Seguridad de API Key y variables de entorno
    ├── BUGFIX_REPORT4.md       # Reporte 4: Limpieza de archivos multimedia en disco
    └── BUGFIX_REPORT5.md       # Reporte 5: Visor PDF interactivo y sincronización en vivo
```

---

## ⚙️ Instalación y Puesta en Marcha

Sigue estos pasos para clonar y ejecutar el proyecto en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd BookTracker
```

### 2. Configurar el entorno virtual e instalar dependencias

Puedes usar **uv** (recomendado por velocidad) o **pip tradicional**:

#### Opción A: Usando `uv` (Recomendado)
```bash
# Sincroniza el entorno virtual automáticamente
uv sync

# Activar el entorno virtual:
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate
```

#### Opción B: Usando `pip` y `venv` estándar
```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual:
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Windows (CMD):
.venv\Scripts\activate.bat
# En Linux / macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

### 3. Configurar la clave de API (Opcional)

El proyecto funciona al **100% sin necesidad de configurar ninguna clave** gracias a la integración abierta con Open Library.

Si deseas utilizar la API oficial de Google Books con calificaciones y valoraciones editoriales:
1. Copia el archivo `.env.example` y nómbralo `.env`:
   ```bash
   cp .env.example .env
   ```
2. Abre `.env` y pega tu clave obtenida en Google Cloud Console:
   ```env
   GOOGLE_BOOKS_API_KEY=tu_api_key_aqui
   ```

---

### 4. Aplicar las migraciones a la Base de Datos

Inicializa o actualiza la base de datos SQLite con el esquema del proyecto:
```bash
python manage.py migrate
```

---

### 5. (Opcional) Crear un superusuario administrador

Para acceder al panel de administración de Django (`/admin/`):
```bash
python manage.py createsuperuser
```

---

### 6. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

Una vez levantado el servidor, abre tu navegador e ingresa a:  
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 📖 Flujo de Uso Rápido

1. **Registro:** Ve a **Sign Up** y crea una cuenta de usuario.
2. **Crear Libro:** 
   - Entra a **Create Book** (`/books/create/`).
   - Escribe el título o autor en la barra de búsqueda en línea (ej. *El principito*, *Cien años de soledad*, *Clean Code*).
   - Haz clic en la edición deseada para autocompletar automáticamente el título, autor, total de páginas y previsualizar la portada.
   - Adjunta tu archivo PDF si dispones de él y presiona **Crear Libro**.
3. **Lectura y Sincronización:**
   - Entra al detalle del libro en tu biblioteca.
   - Si tiene un PDF adjunto, el visor interactivo cargará el documento y reanudará en la página donde te quedaste.
   - Conforme avanzas páginas con los botones o flechas del teclado, tu progreso se sincronizará automáticamente con tu perfil de lectura.
4. **Reseñas:** Agrega tus conclusiones o citas favoritas en la sección de notas personales.

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye pruebas unitarias de modelos (MVT), pruebas de integración de vistas (IVT) y validación de endpoints AJAX:

```bash
# Ejecutar con pytest:
pytest

# O ejecutar directamente con Django:
python manage.py test books
```

---

## 📑 Bitácora de Desarrollo y Reportes Técnicos

Para una revisión exhaustiva de la evolución del proyecto, auditoría de bugs y decisiones de arquitectura, consulta los reportes técnicos en la raíz:
- [BUGFIX_REPORT.md](BUGFIX_REPORT.md) — *Migraciones de Google Books y corrección de error NoneType.*
- [BUGFIX_REPORT2.md](BUGFIX_REPORT2.md) — *Buscador predictivo, autocompletado y arquitectura híbrida con Open Library.*
- [BUGFIX_REPORT3.md](BUGFIX_REPORT3.md) — *Seguridad de credenciales, variables de entorno y protección en Git.*
- [BUGFIX_REPORT4.md](BUGFIX_REPORT4.md) — *Limpieza física de archivos multimedia huérfanos con señales post_delete y pre_save.*
- [BUGFIX_REPORT5.md](BUGFIX_REPORT5.md) — *Visor interactivo con Mozilla PDF.js y sincronización bidireccional de lectura.*

---

## 👥 Equipo de Desarrollo

- **Jorge Reyes Rojas**
- **Rafael Isaac Gómez Ortega**
- **Sergio Alexis Lamas Bravo**
