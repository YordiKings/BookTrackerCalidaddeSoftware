from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.utils import timezone
from django.http import JsonResponse
from .forms import BookForm
from .forms import SignUpForm
from .forms import SignInForm
from .models import Book, Profile
from datetime import datetime
import requests
from django.core.files.base import ContentFile
import json
import os
from django.conf import settings

# Create your views here.

def home(request):
    return render(request, 'home.html')

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

@login_required
def books(request):
    books = Book.objects.filter(user=request.user)
    return render(request, 'books.html', {'books': books})

@login_required
def dashboard(request):
    books_created = Book.objects.filter(user=request.user).order_by('-created')
    books_completed = Book.objects.filter(user=request.user, date_completed__isnull=False).order_by('-date_completed')
    profile = request.user.profile
    return render(request, 'dashboard.html', {'books_created': books_created, 'books_completed': books_completed, 'profile': profile})


def _fetch_google_books(query, max_results=5):
    """
    Busca libros en Google Books API (usando API key si está configurada).
    Si Google Books devuelve 429 (límite de cuota sin key) o no responde,
    realiza un fallback automático a Open Library API.
    """
    api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', '') or os.environ.get('GOOGLE_BOOKS_API_KEY', '')
    params = {'q': query, 'maxResults': max_results}
    if api_key:
        params['key'] = api_key

    # 1. Intentar con Google Books API
    try:
        gb_response = requests.get(
            'https://www.googleapis.com/books/v1/volumes',
            params=params,
            timeout=6
        )
        if gb_response.status_code == 200:
            data = gb_response.json()
            if 'items' in data and len(data['items']) > 0:
                results = []
                for item in data['items']:
                    vol = item.get('volumeInfo', {})
                    isbn = ''
                    for identifier in vol.get('industryIdentifiers', []):
                        if identifier.get('type') == 'ISBN_13':
                            isbn = identifier.get('identifier', '')
                            break
                        elif identifier.get('type') == 'ISBN_10':
                            isbn = identifier.get('identifier', '')

                    image_links = vol.get('imageLinks', {})
                    cover_url = (
                        image_links.get('thumbnail')
                        or image_links.get('smallThumbnail')
                        or ''
                    )
                    if cover_url:
                        cover_url = cover_url.replace('http:', 'https:')

                    categories = vol.get('categories', [])
                    results.append({
                        'source': 'Google Books',
                        'google_books_id': item.get('id', ''),
                        'title': vol.get('title', ''),
                        'authors': ', '.join(vol.get('authors', [])),
                        'description': vol.get('description', ''),
                        'page_count': vol.get('pageCount', 0),
                        'categories': ', '.join(categories) if categories else '',
                        'isbn': isbn,
                        'publisher': vol.get('publisher', ''),
                        'published_date': vol.get('publishedDate', ''),
                        'average_rating': vol.get('averageRating'),
                        'ratings_count': vol.get('ratingsCount'),
                        'preview_link': vol.get('previewLink', ''),
                        'cover_url': cover_url,
                    })
                if results:
                    return results
    except Exception:
        pass

    # 2. Fallback a Open Library API (abierta y sin cuotas restrictivas)
    try:
        ol_response = requests.get(
            'https://openlibrary.org/search.json',
            params={
                'q': query,
                'limit': max_results,
                'fields': 'key,title,author_name,number_of_pages_median,cover_i,isbn,publisher,first_publish_year,subject'
            },
            timeout=8
        )
        if ol_response.status_code == 200:
            docs = ol_response.json().get('docs', [])
            results = []
            for doc in docs:
                cover_id = doc.get('cover_i')
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ''
                authors = doc.get('author_name', [])
                publishers = doc.get('publisher', [])
                isbns = doc.get('isbn', [])
                subjects = doc.get('subject', [])

                first_year = doc.get('first_publish_year', '')
                desc = f"Publicación original: {first_year}." if first_year else ''
                if subjects:
                    desc += f" Temas: {', '.join(subjects[:4])}."

                results.append({
                    'source': 'Open Library',
                    'google_books_id': doc.get('key', '').replace('/works/', ''),
                    'title': doc.get('title', ''),
                    'authors': ', '.join(authors[:2]) if authors else 'Autor desconocido',
                    'description': desc,
                    'page_count': doc.get('number_of_pages_median', 0) or 0,
                    'categories': ', '.join(subjects[:2]) if subjects else '',
                    'isbn': isbns[0] if isbns else '',
                    'publisher': publishers[0] if publishers else '',
                    'published_date': str(first_year),
                    'average_rating': None,
                    'ratings_count': None,
                    'preview_link': f"https://openlibrary.org{doc.get('key', '')}" if doc.get('key') else '',
                    'cover_url': cover_url,
                })
            return results
    except Exception:
        pass

    return []


@login_required
def search_google_books(request):
    """Endpoint AJAX que busca libros y devuelve JSON."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    results = _fetch_google_books(query, max_results=5)
    return JsonResponse({'results': results})


def _download_and_save_cover(book, cover_url):
    """Descarga una imagen de portada desde una URL y la asigna al modelo Book."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) BookTracker/1.0'}
        img_response = requests.get(cover_url, headers=headers, timeout=8)
        if img_response.status_code == 200 and len(img_response.content) > 200:
            ext = 'jpg'
            content_type = img_response.headers.get('Content-Type', '')
            if 'png' in content_type:
                ext = 'png'
            book.cover.save(
                f"{book.title}_cover.{ext}",
                ContentFile(img_response.content),
                save=False
            )
            return True
    except Exception:
        pass
    return False


@login_required
def create_book(request):
    profile = request.user.profile
    if request.method == 'GET':
        return render(request, 'create_book.html', {'form': BookForm()})
    else:
        form = BookForm(request.POST, request.FILES)
        pages_read = int(request.POST.get('pages_read', 0))
        pages_total = int(request.POST.get('pages_total', 0))
        if pages_read > pages_total:
            return render(request, 'create_book.html', {'form': form, 'error': 'No puedes leer más páginas de las que tiene el libro'})
        if form.is_valid():
            try:
                new_book = form.save(commit=False)
                new_book.user = request.user

                # 1. Obtener metadatos enviados desde el selector interactivo
                gb_id = request.POST.get('google_books_id', '').strip()
                selected_cover_url = request.POST.get('selected_cover_url', '').strip()
                selected_desc = request.POST.get('selected_description', '').strip()
                selected_cat = request.POST.get('selected_category', '').strip()
                selected_pub = request.POST.get('selected_publisher', '').strip()
                selected_date = request.POST.get('selected_published_date', '').strip()
                selected_isbn = request.POST.get('selected_isbn', '').strip()
                selected_rating = request.POST.get('selected_rating', '').strip()
                selected_preview = request.POST.get('selected_preview_link', '').strip()

                if gb_id or selected_desc or selected_cover_url:
                    new_book.google_books_id = gb_id
                    if selected_desc:
                        new_book.description = selected_desc
                    if selected_cat:
                        new_book.category = selected_cat
                    if selected_pub:
                        new_book.publisher = selected_pub
                    if selected_date:
                        new_book.published_date = selected_date
                    if selected_isbn:
                        new_book.isbn = selected_isbn
                    if selected_preview:
                        new_book.preview_link = selected_preview
                    if selected_rating:
                        try:
                            new_book.average_rating = float(selected_rating)
                        except (ValueError, TypeError):
                            pass

                    # Si no subió portada manual, descargar la portada seleccionada
                    if not new_book.cover and selected_cover_url:
                        _download_and_save_cover(new_book, selected_cover_url)

                # 2. Si el usuario no usó el buscador (creación manual sin portada), intentar enriquecer
                elif not new_book.cover:
                    auto_results = _fetch_google_books(f"{new_book.title} {new_book.autor}".strip(), max_results=1)
                    if auto_results:
                        first = auto_results[0]
                        new_book.google_books_id = first.get('google_books_id', '')
                        new_book.description = first.get('description', '')
                        new_book.category = first.get('categories', '')
                        new_book.publisher = first.get('publisher', '')
                        new_book.published_date = first.get('published_date', '')
                        new_book.isbn = first.get('isbn', '')
                        new_book.preview_link = first.get('preview_link', '')
                        new_book.average_rating = first.get('average_rating')
                        new_book.ratings_count = first.get('ratings_count')
                        if first.get('cover_url'):
                            _download_and_save_cover(new_book, first['cover_url'])

                new_book.save()

                if pages_read == pages_total and pages_total > 0:
                    book_obj = Book.objects.get(pk=new_book.id)
                    book_obj.pages_read = book_obj.pages_total
                    book_obj.date_completed = timezone.now()
                    book_obj.save()

                today = timezone.now().date()
                # Actualizar récord diario/máximo
                if profile.date_most_pages_read == today:
                    profile.most_pages_read += pages_read
                else:
                    if pages_read > profile.most_pages_read:
                        profile.most_pages_read = pages_read
                        profile.date_most_pages_read = today
                if profile.most_pages_read < 0:
                    profile.most_pages_read = 0
                profile.pages_this_month += pages_read
                if profile.pages_this_month < 0:
                    profile.pages_this_month = 0
                profile.save()
                return redirect('books')
            except (ValueError, Exception) as e:
                return render(request, 'create_book.html', {'form': form, 'error': f'Error al guardar: {str(e)}'})
        else:
            return render(request, 'create_book.html', {'form': form, 'error': 'Formulario inválido'})

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    profile = request.user.profile
    last_pages_read = book.pages_read
    if request.method == 'GET':
        form = BookForm(instance=book)
        return render(request, 'book_detail.html', {'book': book, 'form': form})
    else:
        form = BookForm(request.POST, request.FILES, instance=book)
        pages_read = int(request.POST.get('pages_read', 0))
        pages_total = int(request.POST.get('pages_total', 0))
        if pages_read > pages_total:
            return render(request, 'book_detail.html', {'book': book, 'form': form, 'error': 'No puedes leer más páginas de las que tiene el libro'})
        if form.is_valid():
            try:
                form.save()
                if pages_read == pages_total:
                    complete_book(request, book_id)
                elif pages_read < pages_total:
                    book.date_completed = None
                    book.save()
                # Calcular cuántas páginas nuevas se leyeron
                pages = pages_read - last_pages_read
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
                return redirect('books')
            except ValueError:
                return render(request, 'book_detail.html', {'book': book, 'form': form, 'error': 'Error actualizando libro'})
        else:
            return render(request, 'book_detail.html', {'book': book, 'form': form, 'error': 'Formulario inválido'})

@login_required
def complete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method == 'POST':
        book.pages_read = book.pages_total
        book.date_completed = timezone.now()
        book.save()
        return redirect('books')

@login_required
def update_pdf_progress(request, book_id):
    """
    Endpoint AJAX para sincronizar en tiempo real el progreso de lectura
    del visor de PDF con el modelo Book y el Profile del usuario.
    """
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

    # 1. Sincronización del total de páginas si el PDF tiene un conteo diferente
    if total_pages > 0 and book.pages_total != total_pages:
        book.pages_total = total_pages
        updated_fields = True

    # 2. Sincronización del avance de páginas leídas
    last_pages_read = book.pages_read
    if current_page > 0:
        if current_page > book.pages_total:
            current_page = book.pages_total

        # Solo incrementamos si avanzó más allá de lo leído previamente
        if current_page > last_pages_read:
            pages_diff = current_page - last_pages_read
            book.pages_read = current_page
            updated_fields = True

            # Si alcanzó el final del PDF, marcar como completado
            if book.pages_read >= book.pages_total:
                book.date_completed = timezone.now().date()
            else:
                book.date_completed = None

            # Actualizar estadísticas en el perfil del lector
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

@login_required    
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    if request.method == 'POST':
        book.delete()
        return redirect('books')

@login_required    
def signout(request):
    logout(request)
    return redirect('home')

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': SignInForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html', {'form': SignInForm(), 'error': 'El usuario o la contraseña no son incorrectos'})
        else:
            login(request, user)
            return redirect('books')


@login_required
def agile_dashboard(request):
    # Ruta hacia el archivo JSON de métricas
    json_path = os.path.join(settings.BASE_DIR, "books", "data", "metrics.json")

    # Carga de datos dinámicos
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
    else:
        # Fallback en caso de no encontrar el archivo
        metrics_data = {"sprints": [], "kpis_summary": {}}

    context = {
        "metrics": metrics_data,
        "metrics_json": json.dumps(metrics_data),
    }
    return render(request, "agile_dashboard.html", context)
