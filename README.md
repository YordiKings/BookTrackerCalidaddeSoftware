# 📚 BookTracker

**BookTracker** es una aplicación web integral desarrollada con **Python** y **Django** diseñada para gestionar, dar seguimiento y gamificar el hábito de lectura personal. Permite a los usuarios registrar sus libros, controlar su progreso diario de lectura, calcular metas a corto plazo, subir archivos PDF y portadas, y consultar estadísticas personales.

Adicionalmente, el proyecto incluye un panel de métricas ágiles (**Agile Dashboard**) para monitorear el desempeño del equipo de desarrollo a lo largo de los Sprints (velocidad, previsibilidad, cobertura de código y defectos).

---

## 🚀 Características Principales

- **Gestión de Libros (CRUD):** Registro de libros con título, autor, meta de finalización, páginas totales y leídas.
- **Enriquecimiento Automático vía Google Books API:** Al dar de alta un libro, el sistema busca automáticamente la sinopsis oficial y descarga la imagen de portada si no se proporciona una manualmente.
- **Soporte Multimedia:** Posibilidad de subir portadas personalizadas y documentos PDF de lectura.
- **Cálculo de Ritmo de Lectura:** Generación de tablas estimadas de páginas diarias necesarias para terminar el libro en plazos de 1 a 10 días.
- **Perfil y Gamificación:** Registro automático de récord de más páginas leídas en un solo día, acumulado de páginas leídas en el mes y cálculo de promedio diario.
- **Autenticación Segura:** Sistema de registro (`Sign Up`), inicio de sesión (`Sign In`) y cierre de sesión (`Sign Out`) por usuario.
- **Agile Dashboard:** Visualización gráfica con Chart.js de métricas de Sprints del proyecto (Story Points planeados vs. completados, Lead Time, Cobertura de código y CSAT).

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3.12+, Django 5.x
- **Base de Datos:** SQLite (desarrollo local)
- **Frontend:** HTML5, CSS3 personalizado, Bootstrap 5, Chart.js
- **APIs Externas:** Google Books API v1
- **Testing:** Pytest, Django Test Runner, Unittest Mock
- **Gestor de Paquetes:** `uv` / `pip`

---

## 📁 Estructura del Proyecto

```text
BookTracker/
│
├── BookTracker/                # Configuración principal del proyecto Django
│   ├── settings.py             # Configuración general (apps, BD, media, static)
│   ├── urls.py                 # Enrutador global de URLs
│   ├── wsgi.py / asgi.py       # Puntos de entrada para despliegue
│
├── books/                      # Aplicación principal de Django
│   ├── data/
│   │   └── metrics.json        # Datos históricos de Sprints para el Agile Dashboard
│   ├── migrations/             # Migraciones del esquema de base de datos
│   ├── templates/              # Plantillas HTML (vistas del usuario y dashboards)
│   ├── admin.py                # Configuración del panel de administración
│   ├── forms.py                # Formularios Django (libros y autenticación)
│   ├── models.py               # Modelos ORM (Book, Profile) y señales
│   ├── tests.py                # Suites de pruebas unitarias e integración
│   └── views.py                # Lógica de controladores y endpoints
│
├── media/                      # Archivos multimedia subidos por usuarios (ignorado en Git)
│   ├── covers/                 # Portadas (.jpg, .png)
│   └── pdfs/                   # Documentos (.pdf)
│
├── static/                     # Archivos estáticos de frontend (CSS, imágenes)
│   └── style.css
│
├── db.sqlite3                  # Base de datos local (ignorada en Git)
├── manage.py                   # CLI principal de Django
├── pyproject.toml / uv.lock    # Definición de dependencias con uv
└── requirements.txt            # Dependencias estándar de pip
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

Puedes usar **uv** (recomendado) o **pip tradicional**:

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

# Instalar requerimientos
pip install -r requirements.txt
```

---

### 3. Aplicar las migraciones a la Base de Datos

Inicializa la base de datos SQLite con el esquema del proyecto:
```bash
python manage.py migrate
```

---

### 4. (Opcional) Crear un superusuario administrador

Para acceder al panel de administración de Django (`/admin/`):
```bash
python manage.py createsuperuser
```

---

### 5. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

Una vez levantado el servidor, abre tu navegador e ingresa a:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🧪 Ejecución de Pruebas

El proyecto cuenta con pruebas unitarias de modelos (MVT) y pruebas de integración de vistas (IVT):

```bash
# Ejecutar con pytest:
pytest

# O ejecutar directamente con Django:
python manage.py test books
```

---

## 👥 Equipo de Desarrollo

- **Jorge Reyes Rojas**
- **Rafael Isaac Gómez Ortega**
- **Sergio Alexis Lamas Bravo**
