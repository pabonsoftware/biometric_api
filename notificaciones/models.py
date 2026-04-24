from django.db import models

class Notificacion(models.Model):

    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )

    mensaje = models.CharField(max_length=255)

    leido = models.BooleanField(default=False)

    tipo = models.CharField(max_length=50,blank=True)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.correo} - {self.mensaje[:20]}"