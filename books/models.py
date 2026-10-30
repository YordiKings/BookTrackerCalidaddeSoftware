from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=200)
    autor = models.CharField(max_length=200)
    goal = models.DateField(null=True, blank=True)
    pages_read = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    pages_total = models.IntegerField(validators=[MinValueValidator(1)])
    created = models.DateField(auto_now_add=True)
    date_completed = models.DateField(null=True, blank=True, default=None)
    user =  models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Campos multimedia
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='pdfs/', null=True, blank=True)

    # Campos de Google Books API
    google_books_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    isbn = models.CharField(max_length=20, null=True, blank=True)
    publisher = models.CharField(max_length=200, null=True, blank=True)
    published_date = models.CharField(max_length=20, null=True, blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    ratings_count = models.IntegerField(null=True, blank=True)
    preview_link = models.URLField(max_length=500, null=True, blank=True)

    # Notas personales del usuario
    user_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title
    
    def progress(self):
        if self.pages_total == 0:
            return 0
        return round((self.pages_read / self.pages_total) * 100)
    
    def pages_for_day(self):
        if self.pages_total == 0:
            return 0
        tabla = []
        for dias in range(1, 11):
            paginas_por_dia = round((self.pages_total-self.pages_read) / dias)
            tabla.append((dias, paginas_por_dia))
        return tabla

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pages_read > self.pages_total:
            raise ValidationError("Las páginas leídas no pueden ser mayores que el total de páginas.")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_most_pages_read = models.DateField(null=True, blank=True)
    most_pages_read = models.PositiveIntegerField(default=0)
    pages_this_month = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def average_pages_for_day(self):
        if self.pages_this_month == 0:
            return 0
        dias = timezone.now().day
        paginas_por_dia = round(self.pages_this_month / dias)
        return paginas_por_dia

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

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

@receiver(pre_save, sender=Book)
def delete_old_files_on_update(sender, instance, **kwargs):
    """
    Si el usuario reemplaza una portada o un PDF por un archivo nuevo,
    elimina el archivo viejo del disco para evitar que se acumule basura.
    """
    if not instance.pk:
        return  # Libro nuevo, no hay archivo previo

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
