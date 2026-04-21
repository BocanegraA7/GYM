from django.db import models
from django.contrib.auth.models import User


class Clase(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    entrenador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clases_creadas')
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_min = models.PositiveIntegerField(default=60)
    cupos = models.PositiveIntegerField(default=10)
    lugar = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} - {self.fecha} {self.hora.strftime('%H:%M')}"


class Inscripcion(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clases_inscritas')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'clase')

    def __str__(self):
        return f"{self.cliente.username} inscrito en {self.clase.nombre}"