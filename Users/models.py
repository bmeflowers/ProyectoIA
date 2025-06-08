from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_completo = models.CharField(max_length=150)
    edad = models.PositiveIntegerField()
    biografia = models.TextField(blank=True)
    foto = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    ocupacion = models.CharField(max_length=100, blank=True)
    genero = models.CharField(max_length=20, choices=[
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro'),
    ])

    def __str__(self):
        return f'Perfil de {self.user.username}'