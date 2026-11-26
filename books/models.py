from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

# Create your models here.
class Book(models.Model):
    title = models.CharField('Título', max_length=200)
    autor = models.CharField('Autor', max_length=200)
    goal = models.DateField('Meta (fecha para terminarlo)', null=True, blank=True)
    pages_read = models.IntegerField('Páginas leídas', default=0, validators=[MinValueValidator(0)])
    pages_total = models.IntegerField('Páginas totales', validators=[MinValueValidator(1)])
    created = models.DateField('Fecha de registro', auto_now_add=True)
    date_completed = models.DateField('Fecha de término', null=True, blank=True, default=None)
    user =  models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')

    # Campos multimedia
    cover = models.ImageField('Portada', upload_to='covers/', null=True, blank=True)
    pdf_file = models.FileField('Archivo PDF', upload_to='pdfs/', null=True, blank=True)

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
    user_notes = models.TextField('Notas personales / Reseña', null=True, blank=True)

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
        # Si algún campo vino vacío o inválido, el formulario ya reporta ese error;
        # aquí solo se compara cuando ambos valores existen (evita TypeError con None).
        if self.pages_read is None or self.pages_total is None:
            return
        if self.pages_read > self.pages_total:
            raise ValidationError("Las páginas leídas no pueden ser mayores que el total de páginas.")


class DailyReading(models.Model):
    """Páginas leídas por un usuario en un día concreto (fecha local).

    Es la fuente de verdad de las estadísticas: el récord diario es el día con más
    páginas y el acumulado del mes es la suma de los días del mes actual.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_readings', verbose_name='Usuario')
    date = models.DateField('Fecha')
    pages = models.PositiveIntegerField('Páginas leídas', default=0)

    class Meta:
        verbose_name = 'Lectura diaria'
        verbose_name_plural = 'Lecturas diarias'
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_daily_reading_per_user'),
        ]

    def __str__(self):
        return f"{self.user.username} · {self.date} · {self.pages} págs."


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Valores calculados a partir de DailyReading (se recalculan con refresh_stats)
    date_most_pages_read = models.DateField(null=True, blank=True)
    most_pages_read = models.PositiveIntegerField(default=0)
    pages_this_month = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Perfil de {self.user.username}"

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

    def average_pages_for_day(self):
        if self.pages_this_month == 0:
            return 0
        dias = timezone.localdate().day
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
