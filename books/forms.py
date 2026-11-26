from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from .models import Book

class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'autor', 'goal', 'pages_read', 'pages_total', 'cover', 'pdf_file', 'user_notes']
        widgets = {
            'goal': forms.DateInput(attrs={'type': 'date'}),
            'user_notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe tus notas, citas favoritas o reseña personal aquí...'}),
        }
    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['autor'].widget.attrs['class'] = 'form-control'
        self.fields['goal'].widget.attrs['class'] = 'form-control'  
        self.fields['pages_read'].widget.attrs['class'] = 'form-control'
        self.fields['pages_total'].widget.attrs['class'] = 'form-control'
        self.fields['cover'].widget.attrs['class'] = 'form-control'
        self.fields['pdf_file'].widget.attrs['class'] = 'form-control'
        self.fields['user_notes'].widget.attrs['class'] = 'form-control'
        self.fields['user_notes'].label = 'Notas personales / Reseña'
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

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

class SignInForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')
    def __init__(self, *args, **kwargs):
        super(SignInForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
