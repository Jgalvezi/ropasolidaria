from .models import CentroAcopio
from django.utils import timezone
from .models import Prenda

def global_context(request):
    return {
        'ultimos_centros_footer': CentroAcopio.objects.order_by('-id')[:3],
        'alertas_criticas': 0 # (tu lógica de alertas aquí)
    }
    
def user_stats(request):
    if request.user.is_authenticated:
        # Forzamos la carga del perfil para evitar errores de 'None'
        try:
            return {
                'puntos_usuario': request.user.perfil.puntos,
                'nivel_usuario': request.user.perfil.get_nivel()
            }
        except:
            return {'puntos_usuario': 0}
    return {}
    
def footer_data(request):
    # Obtenemos los últimos 3 centros agregados
    ultimos_centros = CentroAcopio.objects.order_by('-id')[:3]
    alertas_criticas = 0
    if request.user.is_authenticated and request.user.is_staff:
        hoy = timezone.now().date()
        # Contamos prendas no validadas cuya fecha de entrega ya pasó
        alertas_criticas = Prenda.objects.filter(
            validada=False, 
            fecha_entrega__lt=hoy
        ).count()

    return {
        'ultimos_centros_footer': Prenda.objects.order_by('-id')[:3], # ejemplo
        'alertas_criticas': alertas_criticas
    }

