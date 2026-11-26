from django.contrib import admin
from .models import Book, DailyReading

class BookAdmin(admin.ModelAdmin):
    readonly_fields = ("created", )

class DailyReadingAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "pages")
    list_filter = ("user",)

# Register your models here.
admin.site.register(Book, BookAdmin)
admin.site.register(DailyReading, DailyReadingAdmin)