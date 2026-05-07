from django.db import models
from django.contrib.auth.models import User

class Sala(models.Model):
    nombre = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"{self.sala} - {self.usuario.username} ({self.fecha} {self.hora_inicio})"
