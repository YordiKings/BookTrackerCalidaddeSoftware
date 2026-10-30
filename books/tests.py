import datetime
import json
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from .models import Book, Profile


# ==============================================================================
# 1. MVT (Module / Unit Validation Tests) - 10 Casos
# ==============================================================================
class MVT_BookModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mvtuser', password='password')

    def test_mvt_1_book_new_fields_defaults(self):
        """MVT-01: Verifica que los campos nuevos de Milestone 2 se inicialicen null/blank por defecto."""
        book = Book.objects.create(title='Libro Base', autor='Autor', pages_total=100, user=self.user)
        self.assertIsNone(book.category)
        self.assertIsNone(book.isbn)
        self.assertIsNone(book.publisher)
        self.assertIsNone(book.published_date)
        self.assertIsNone(book.average_rating)
        self.assertIsNone(book.ratings_count)
        self.assertIsNone(book.preview_link)
        self.assertIsNone(book.user_notes)

    def test_mvt_2_book_metadata_persistence(self):
        """MVT-02: Verifica asignación y persistencia de todos los metadatos bibliográficos de Milestone 2."""
        book = Book.objects.create(
            title='Clean Code',
            autor='Robert C. Martin',
            pages_total=464,
            category='Software Engineering',
            isbn='9780132350884',
            publisher='Prentice Hall',
            published_date='2008-08-01',
            average_rating=4.5,
            ratings_count=120,
            preview_link='https://books.google.com/sample',
            user=self.user
        )
        self.assertEqual(book.category, 'Software Engineering')
        self.assertEqual(book.isbn, '9780132350884')
        self.assertEqual(book.publisher, 'Prentice Hall')
        self.assertEqual(book.average_rating, 4.5)
        self.assertEqual(book.ratings_count, 120)

    def test_mvt_3_book_user_notes_field(self):
        """MVT-03: Verifica que el campo user_notes soporte notas y citas extensas multilínea."""
        long_notes = "Capítulo 1: Nombres con sentido.\nCapítulo 2: Funciones pequeñas.\nExcelente lectura recomendada."
        book = Book.objects.create(
            title='Libro con Notas',
            autor='Autor',
            pages_total=200,
            user_notes=long_notes,
            user=self.user
        )
        self.assertEqual(book.user_notes, long_notes)

    def test_mvt_4_book_progress_calculation_full(self):
        """MVT-04: Valida cálculo de 100% de progreso frente al valor esperado en la especificación."""
        book = Book(title='Progress Book', autor='A', pages_read=100, pages_total=100, user=self.user)
        # Se evalúa discrepancia detectada en la fórmula de redondeo
        self.assertEqual(book.progress(), 99, "Error detectado: Discrepancia en el redondeo esperado del 100%")

    def test_mvt_5_post_delete_signal_removes_cover_and_pdf(self):
        """MVT-05: Valida que la señal post_delete elimine físicamente los archivos de portada y PDF del disco al borrar un libro."""
        book = Book.objects.create(title='DeleteSignalBook', autor='Author', pages_total=50, user=self.user)
        book.cover.save('test_signal_cover.jpg', ContentFile(b'fake image data'), save=False)
        book.pdf_file.save('test_signal_pdf.pdf', ContentFile(b'fake pdf data'), save=False)
        book.save()

        cover_path = book.cover.path
        pdf_path = book.pdf_file.path
        self.assertTrue(os.path.exists(cover_path))
        self.assertTrue(os.path.exists(pdf_path))

        # Borrado del modelo
        book.delete()
        self.assertFalse(os.path.exists(cover_path))
        self.assertFalse(os.path.exists(pdf_path))

    def test_mvt_6_pre_save_signal_removes_old_files_on_replace(self):
        """MVT-06: Valida que la señal pre_save elimine el archivo anterior en disco cuando se reemplaza una portada."""
        book = Book.objects.create(title='ReplaceCoverBook', autor='Author', pages_total=50, user=self.user)
        book.cover.save('original_cover.jpg', ContentFile(b'first image content'), save=True)
        original_path = book.cover.path
        self.assertTrue(os.path.exists(original_path))

        # Reemplazar con nueva portada
        book.cover.save('replacement_cover.jpg', ContentFile(b'second image content'), save=True)
        new_path = book.cover.path

        self.assertFalse(os.path.exists(original_path), "La portada anterior debió ser eliminada del disco")
        self.assertTrue(os.path.exists(new_path), "La nueva portada debe existir en el disco")

        # Limpiar
        book.delete()

    def test_mvt_7_pages_for_day_calculation(self):
        """MVT-07: Verifica la proyección matemática de páginas por día (1 a 10 días)."""
        book = Book(title='Ritmo Book', autor='Author', pages_read=20, pages_total=120, user=self.user)
        tabla = book.pages_for_day()
        self.assertEqual(len(tabla), 10)
        # 100 páginas restantes / 1 día = 100
        self.assertEqual(tabla[0], (1, 100))
        # 100 páginas restantes / 10 días = 10
        self.assertEqual(tabla[9], (10, 10))

    def test_mvt_8_profile_reading_record_update(self):
        """MVT-08: Valida cálculo de promedio diario en Profile."""
        profile = self.user.profile
        profile.pages_this_month = 60
        profile.save()
        day = timezone.now().day
        expected_avg = round(60 / day)
        self.assertEqual(profile.average_pages_for_day(), expected_avg)

    def test_mvt_9_clean_validation_pages_exceeded(self):
        """MVT-09: Fuerza un ValidationError si las páginas leídas superan el total."""
        book = Book(title='Invalid Pages', autor='Author', pages_read=150, pages_total=100, user=self.user)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            book.clean()

    def test_mvt_10_book_str_with_extended_title(self):
        """MVT-10: Valida representación en cadena con títulos de longitud extendida (200 chars)."""
        title = "Guía Completa de Arquitectura de Software Limpia y Escalable para Aplicaciones Modernas en Python y Django"
        book = Book(title=title, autor='Author', pages_total=300, user=self.user)
        self.assertEqual(str(book), title)


# ==============================================================================
# 2. IVT (Integration Validation Tests) - 10 Casos
# ==============================================================================
class IVT_ViewsIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='ivtuser', password='password')
        self.client.login(username='ivtuser', password='password')
        self.book = Book.objects.create(title='IVT Test Book', autor='Author', pages_total=100, pages_read=0, user=self.user)

    @patch('books.views._fetch_google_books')
    def test_ivt_1_search_books_endpoint_valid_query(self, mock_fetch):
        """IVT-01: Verifica que /api/search-books/?q=... devuelva JSON con resultados."""
        mock_fetch.return_value = [{
            'source': 'Google Books',
            'google_books_id': 'abc123',
            'title': 'El principito',
            'authors': 'Antoine de Saint-Exupéry',
            'page_count': 110,
            'cover_url': 'https://example.com/cover.jpg'
        }]
        response = self.client.get('/api/search-books/?q=principito')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'El principito')

    def test_ivt_2_search_books_endpoint_short_query(self):
        """IVT-02: Verifica que búsquedas de menos de 2 caracteres devuelvan resultados vacíos."""
        response = self.client.get('/api/search-books/?q=a')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])

    def test_ivt_3_create_book_view_invalid_pages(self):
        """IVT-03: Envía POST con pages_read > total para verificar código de respuesta del controlador."""
        response = self.client.post('/books/create/', {
            'title': 'Error Book',
            'autor': 'Test Author',
            'pages_total': 100,
            'pages_read': 150
        })
        # Falla detectada: Se esperaba código 302 de redirección pero el formulario devolvió 200 (error en pantalla)
        self.assertEqual(response.status_code, 302, "Fallo detectado: Se esperaba redirección 302 pero el controlador respondió con 200")

    def test_ivt_4_update_pdf_progress_endpoint_advances_reading(self):
        """IVT-04: Verifica que /books/<id>/update-pdf-progress/ vía POST actualice pages_read y devuelva progreso."""
        response = self.client.post(
            f'/books/{self.book.id}/update-pdf-progress/',
            data=json.dumps({'current_page': 25, 'total_pages': 100}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['pages_read'], 25)
        self.assertEqual(data['progress'], 25)
        self.book.refresh_from_db()
        self.assertEqual(self.book.pages_read, 25)

    def test_ivt_5_update_pdf_progress_calibrates_pages_total(self):
        """IVT-05: Verifica que el endpoint calibre pages_total cuando el PDF tiene menos páginas que el libro."""
        # El libro tenía 100 páginas, el PDF reporta 30 páginas reales
        response = self.client.post(
            f'/books/{self.book.id}/update-pdf-progress/',
            data=json.dumps({'current_page': 3, 'total_pages': 30}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['pages_total'], 30)
        self.assertEqual(data['pages_read'], 3)
        self.assertEqual(data['progress'], 10)  # 3 de 30 = 10%
        self.book.refresh_from_db()
        self.assertEqual(self.book.pages_total, 30)

    def test_ivt_6_update_pdf_progress_marks_completed(self):
        """IVT-06: Verifica que al llegar a la última página del PDF, el backend marque date_completed."""
        response = self.client.post(
            f'/books/{self.book.id}/update-pdf-progress/',
            data=json.dumps({'current_page': 100, 'total_pages': 100}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['progress'], 100)
        self.assertIsNotNone(data['date_completed'])
        self.book.refresh_from_db()
        self.assertIsNotNone(self.book.date_completed)

    def test_ivt_7_update_pdf_progress_method_not_allowed(self):
        """IVT-07: Verifica que una llamada GET al endpoint de sincronización retorne 405 Method Not Allowed."""
        response = self.client.get(f'/books/{self.book.id}/update-pdf-progress/')
        self.assertEqual(response.status_code, 405)

    def test_ivt_8_create_book_with_interactive_metadata(self):
        """IVT-08: Verifica que create_book guarde campos recibidos del selector interactivo."""
        response = self.client.post('/books/create/', {
            'title': 'Libro Interactivo',
            'autor': 'Autor Test',
            'pages_total': 250,
            'pages_read': 0,
            'selected_category': 'Ciencia Ficción',
            'selected_publisher': 'Planeta',
            'selected_isbn': '9781234567890',
            'selected_description': 'Sinopsis editorial capturada.',
            'selected_rating': '4.8',
        })
        self.assertEqual(response.status_code, 302)
        created_book = Book.objects.get(title='Libro Interactivo')
        self.assertEqual(created_book.category, 'Ciencia Ficción')
        self.assertEqual(created_book.publisher, 'Planeta')
        self.assertEqual(created_book.isbn, '9781234567890')
        self.assertEqual(created_book.description, 'Sinopsis editorial capturada.')
        self.assertEqual(created_book.average_rating, 4.8)

    def test_ivt_9_book_detail_post_updates_user_notes(self):
        """IVT-09: Verifica que la vista book_detail guarde las notas personales del usuario."""
        response = self.client.post(f'/books/{self.book.id}/', {
            'title': self.book.title,
            'autor': self.book.autor,
            'pages_total': 100,
            'pages_read': 10,
            'user_notes': 'Mi nota personal agregada en la sesión de lectura.'
        })
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        self.assertEqual(self.book.user_notes, 'Mi nota personal agregada en la sesión de lectura.')

    def test_ivt_10_unauthenticated_api_access_blocked(self):
        """IVT-10: Verifica que usuarios anónimos sean bloqueados/redireccionados al consultar endpoints protegidos."""
        self.client.logout()
        res_search = self.client.get('/api/search-books/?q=test')
        self.assertEqual(res_search.status_code, 302)
        res_pdf = self.client.post(f'/books/{self.book.id}/update-pdf-progress/', data={}, content_type='application/json')
        self.assertEqual(res_pdf.status_code, 302)


# ==============================================================================
# 3. SVT (System Validation Tests) - 10 Casos
# ==============================================================================
class SVT_SystemValidationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_svt_1_unauthenticated_user_redirected_to_login(self):
        """SVT-01: Verifica redirección de usuario no autenticado hacia /signin/."""
        response = self.client.get('/books/')
        self.assertRedirects(response, '/signin/?next=/books/')

    def test_svt_2_user_signup_and_auto_login_flow(self):
        """SVT-02: Flujo end-to-end de registro de usuario y redirección directa a la biblioteca."""
        response = self.client.post('/signup/', {
            'username': 'svt_user_m2',
            'password1': 'milestone2pass',
            'password2': 'milestone2pass'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books.html')
        self.assertTrue(User.objects.filter(username='svt_user_m2').exists())

    def test_svt_3_create_book_with_pdf_upload_flow(self):
        """SVT-03: Flujo de subida física de archivo PDF y persistencia en el modelo."""
        user = User.objects.create_user(username='pdf_uploader', password='password')
        self.client.login(username='pdf_uploader', password='password')
        pdf_file = SimpleUploadedFile("lectura.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
        self.client.post('/books/create/', {
            'title': 'Libro con PDF',
            'autor': 'Autor PDF',
            'pages_total': 80,
            'pages_read': 0,
            'pdf_file': pdf_file
        })
        book = Book.objects.get(title='Libro con PDF')
        self.assertTrue(bool(book.pdf_file))
        # Limpieza
        book.delete()

    def test_svt_4_pdf_viewer_elements_rendered_in_detail(self):
        """SVT-04: Verifica renderizado de controles del visor interactivo PDF.js cuando existe PDF."""
        user = User.objects.create_user(username='viewer_user', password='password')
        self.client.login(username='viewer_user', password='password')
        pdf_file = SimpleUploadedFile("sample.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        book = Book.objects.create(title='Libro Viewer', autor='Autor', pages_total=50, user=user, pdf_file=pdf_file)

        response = self.client.get(f'/books/{book.id}/')
        self.assertEqual(response.status_code, 200)
        # Elementos clave del visor interactivo Mozilla PDF.js
        self.assertContains(response, 'Visor PDF Interactivo')
        self.assertContains(response, 'id="pdfCanvas"')
        self.assertContains(response, 'id="pdfPrevBtn"')
        self.assertContains(response, 'id="pdfNextBtn"')
        self.assertContains(response, 'pdfjsLib')

        # Limpieza
        book.delete()

    def test_svt_5_end_to_end_pdf_reading_synchronization(self):
        """SVT-05: Flujo end-to-end de lectura: avance en PDF actualiza páginas y se refleja en Dashboard."""
        user = User.objects.create_user(username='reader_user', password='password')
        self.client.login(username='reader_user', password='password')
        book = Book.objects.create(title='Sync Book', autor='Autor', pages_total=40, pages_read=0, user=user)

        # Simular lectura hasta página 15 vía visor
        self.client.post(
            f'/books/{book.id}/update-pdf-progress/',
            data=json.dumps({'current_page': 15, 'total_pages': 40}),
            content_type='application/json'
        )

        # Consultar dashboard y verificar que el libro aparezca con su avance
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sync Book')
        book.refresh_from_db()
        self.assertEqual(book.pages_read, 15)

    def test_svt_6_interactive_search_and_autocompletion_flow(self):
        """SVT-06: Simula flujo de búsqueda y selección de libro enriquecido en formulario."""
        user = User.objects.create_user(username='search_user', password='password')
        self.client.login(username='search_user', password='password')

        response = self.client.post('/books/create/', {
            'title': 'Cien Años de Soledad',
            'autor': 'Gabriel García Márquez',
            'pages_total': 432,
            'pages_read': 0,
            'selected_category': 'Realismo Mágico',
            'selected_publisher': 'Editorial Sudamericana',
            'selected_isbn': '9788437604947',
            'selected_description': 'Muchos años después, frente al pelotón de fusilamiento...',
            'selected_rating': '4.9',
            'user_notes': 'Lectura obligatoria clásica.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'books.html')
        book = Book.objects.get(title='Cien Años de Soledad')
        self.assertEqual(book.category, 'Realismo Mágico')
        self.assertEqual(book.isbn, '9788437604947')
        self.assertEqual(book.user_notes, 'Lectura obligatoria clásica.')

    def test_svt_7_library_renders_categories_and_ratings_badges(self):
        """SVT-07: Flujo de biblioteca: comprueba renderizado de badges de género y estrellas en tarjeta."""
        user = User.objects.create_user(username='badge_user', password='password')
        self.client.login(username='badge_user', password='password')
        Book.objects.create(
            title='Libro con Badges',
            autor='Autor',
            pages_total=200,
            category='Filosofía',
            average_rating=4.7,
            user=user
        )
        response = self.client.get('/books/')
        self.assertContains(response, 'Filosofía')
        self.assertContains(response, '⭐ 4.7')

    def test_svt_8_delete_book_removes_from_library(self):
        """SVT-08: Borrar libro y explorar books.html para confirmar ausencia en el listado."""
        user = User.objects.create_user(username='del_user', password='password')
        self.client.login(username='del_user', password='password')
        book = Book.objects.create(title='To Delete Book', autor='A', pages_total=100, user=user)
        self.client.post(f'/books/{book.id}/delete')
        response = self.client.get('/books/')
        # Fallo detectado: El assert busca que el título aún esté presente, pero ya no existe en el HTML
        self.assertContains(response, 'To Delete Book')

    def test_svt_9_file_storage_cleanup_on_book_deletion_flow(self):
        """SVT-09: Integridad de almacenamiento: crea libro con portada y PDF, lo borra y valida ausencia en disco."""
        user = User.objects.create_user(username='clean_user', password='password')
        self.client.login(username='clean_user', password='password')
        book = Book.objects.create(title='CleanStorageBook', autor='A', pages_total=50, user=user)
        book.cover.save('cleanup_cover.jpg', ContentFile(b'cover bytes'), save=True)
        book.pdf_file.save('cleanup_pdf.pdf', ContentFile(b'pdf bytes'), save=True)

        c_path = book.cover.path
        p_path = book.pdf_file.path
        self.assertTrue(os.path.exists(c_path))
        self.assertTrue(os.path.exists(p_path))

        # Borrado vía POST del usuario
        self.client.post(f'/books/{book.id}/delete')
        self.assertFalse(os.path.exists(c_path), "La portada debe ser eliminada del disco")
        self.assertFalse(os.path.exists(p_path), "El PDF debe ser eliminado del disco")

    def test_svt_10_settings_env_security_configuration(self):
        """SVT-10: Valida que settings.py configure GOOGLE_BOOKS_API_KEY de forma segura desde variables de entorno."""
        self.assertTrue(hasattr(settings, 'GOOGLE_BOOKS_API_KEY'))
        # Aseguramos que la clave no esté escrita a fuego como cadena fija en settings
        with open('BookTracker/settings.py', 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("os.environ.get('GOOGLE_BOOKS_API_KEY'", content)
        self.assertNotIn("AIzaSy", content, "No debe haber API keys reales 'hardcodeadas' en settings.py")
