from django import forms
from .models import Clase
from django.contrib.auth.models import User
from user.models import Users

class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ['nombre', 'descripcion', 'entrenador', 'fecha', 'hora', 'duracion_min', 'cupos', 'lugar']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'entrenador': forms.Select(attrs={'class': 'form-control'}),
            'duracion_min': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cupos': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'lugar': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            # CORRECCIÓN: Buscamos por el 'username' que es el texto único e idéntico en ambas tablas
            usernames_entrenadores = Users.objects.filter(role__nombre='Entrenador').values_list('username', flat=True)
            
            # Filtramos la tabla de Django usando esos usernames
            self.fields['entrenador'].queryset = User.objects.filter(username__in=usernames_entrenadores)
        except Exception:
            # Por si las moscas, si algo falla que muestre todos para no romper la pantalla
            self.fields['entrenador'].queryset = User.objects.all()