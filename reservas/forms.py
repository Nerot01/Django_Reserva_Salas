from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Reserva, Sala
from datetime import datetime, date

BLOQUES_HORARIOS = [
    ("08:10-08:50", "08:10 - 08:50"),
    ("08:50-09:30", "08:50 - 09:30"),
    ("09:40-10:20", "09:40 - 10:20"),
    ("10:20-11:00", "10:20 - 11:00"),
    ("11:10-11:50", "11:10 - 11:50"),
    ("11:50-12:30", "11:50 - 12:30"),
    ("13:00-13:40", "13:00 - 13:40"),
    ("13:40-14:20", "13:40 - 14:20"),
    ("14:30-15:10", "14:30 - 15:10"),
    ("15:10-15:50", "15:10 - 15:50"),
    ("16:00-16:40", "16:00 - 16:40"),
    ("16:40-17:20", "16:40 - 17:20"),
    ("17:30-18:10", "17:30 - 18:10"),
    ("18:10-18:50", "18:10 - 18:50"),
    ("19:00-19:35", "19:00 - 19:35"),
    ("19:35-20:10", "19:35 - 20:10"),
    ("20:15-20:50", "20:15 - 20:50"),
    ("20:50-21:25", "20:50 - 21:25"),
    ("21:30-22:05", "21:30 - 22:05"),
    ("22:05-22:40", "22:05 - 22:40"),
]

class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = ['nombre', 'capacidad', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la sala'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacidad de personas', 'min': 1}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción de la sala (opcional)'}),
        }
        labels = {
            'nombre': 'Nombre de la Sala',
            'capacidad': 'Capacidad (personas)',
            'descripcion': 'Descripción',
        }

class ReservaForm(forms.ModelForm):
    bloque = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'id_bloque'}),
        required=True,
        error_messages={'required': 'Por favor selecciona un bloque horario.'}
    )

    class Meta:
        model = Reserva
        fields = ['fecha']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_fecha'}),
        }
        labels = {
            'fecha': 'Fecha de la Reserva',
        }

    def __init__(self, *args, **kwargs):
        self.sala = kwargs.pop('sala', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        bloque = cleaned_data.get('bloque')

        if fecha and fecha < date.today():
            self.add_error('fecha', "No se pueden realizar reservas para fechas pasadas.")
            return cleaned_data

        if fecha and bloque and self.sala:
            try:
                inicio_str, fin_str = bloque.split('-')
                hora_inicio = datetime.strptime(inicio_str.strip(), '%H:%M').time()
                hora_fin = datetime.strptime(fin_str.strip(), '%H:%M').time()
                cleaned_data['hora_inicio'] = hora_inicio
                cleaned_data['hora_fin'] = hora_fin
            except ValueError:
                self.add_error('bloque', "Bloque horario no válido.")
                return cleaned_data

            # Validar traslapes de reserva
            overlap = Reserva.objects.filter(
                sala=self.sala,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio
            )
            if self.instance and self.instance.pk:
                overlap = overlap.exclude(pk=self.instance.pk)

            if overlap.exists():
                self.add_error('bloque', "La sala ya se encuentra reservada para este bloque horario y fecha.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.hora_inicio = self.cleaned_data['hora_inicio']
        instance.hora_fin = self.cleaned_data['hora_fin']
        if commit:
            instance.save()
        return instance

class RegistroForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Requerido. Letras, dígitos y @/./+/-/_ únicamente."

