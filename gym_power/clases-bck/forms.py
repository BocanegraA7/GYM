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
        # Obtener IDs de usuarios con rol Entrenador
        entrenadores_ids = Users.objects.filter(role__nombre='Entrenador').values_list('id', flat=True)
        self.fields['entrenador'].queryset = User.objects.filter(id__in=entrenadores_ids)