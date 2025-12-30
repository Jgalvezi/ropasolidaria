from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Perfil
from django.core.mail import send_mail
from .models import Prenda
from django.contrib import messages

# Al otorgar un logro en el admin (ver paso anterior), agregamos:
# messages.success(request, f"¡Felicidades! Has desbloqueado el logro: {logro.nombre}", extra_tags='success')

@receiver(post_save, sender=Prenda)
def verificar_capacidad_critica(sender, instance, **kwargs):
    if instance.validada:
        centro = instance.centro
        if centro.porcentaje_ocupacion() >= 90:
            send_mail(
                '⚠️ ALERTA: Centro de Acopio casi lleno',
                f'El centro {centro.nombre} ha alcanzado el {centro.porcentaje_ocupacion()}% de su capacidad.',
                'sistema@ropasolidaria.com',
                ['admin@ropasolidaria.com'], # Correo del administrador
                fail_silently=True,
            )
            
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # CORRECCIÓN: Solo intenta guardar si el objeto 'perfil' ya existe
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
    else:
        # Por si acaso el usuario existía de antes, lo creamos aquí
        Perfil.objects.create(user=instance)