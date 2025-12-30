from django.contrib import admin
from django.utils.html import format_html
from .models import Prenda, Perfil, Transaccion, CentroAcopio

@admin.action(description="Validar Prenda y Premiar Puntualidad")
def validar_con_reputacion(modeladmin, request, queryset):
    hoy = timezone.now().date()
    for prenda in queryset.filter(validada=False):
        prenda.validada = True
        puntos_ganados = 10 # Base
        
        # BONO DE REPUTACIÓN: Si entrega a tiempo o antes
        if prenda.fecha_entrega and hoy <= prenda.fecha_entrega:
            puntos_ganados += 5
            messages.info(request, f"Bono de +5 pts otorgado a {prenda.donante.username} por puntualidad.")
        
        prenda.save()
        
        perfil = prenda.donante.perfil
        perfil.puntos += puntos_ganados
        perfil.save()
        
        # Logro automático de Confiabilidad
        if perfil.puntos >= 200: # Ejemplo: 200 puntos ganados honestamente
            logro, _ = Logro.objects.get_or_create(nombre="Donante Confiable", icono="bi-check-seal-fill", color="#0dcaf0")
            perfil.logros.add(logro)
            
@admin.action(description="Aprobar y Verificar Logros")
def aprobar_y_logros(modeladmin, request, queryset):
    for prenda in queryset.filter(validada=False):
        prenda.validada = True
        prenda.save()
        
        perfil = prenda.donante.perfil
        perfil.puntos += 10
        
        # LÓGICA DE LOGROS
        donaciones_count = Prenda.objects.filter(donante=prenda.donante, validada=True).count()
        
        # Logro: Primer Paso (1ra donación)
        if donaciones_count == 1:
            logro, _ = Logro.objects.get_or_create(nombre="Primer Paso", icono="bi-rocket-takeoff")
            perfil.logros.add(logro)
            
        # Logro: Donante Estrella (5 donaciones)
        if donaciones_count == 5:
            logro, _ = Logro.objects.get_or_create(nombre="Donante Estrella", icono="bi-star-fill", color="#FFD700")
            perfil.logros.add(logro)

        perfil.save()

@admin.action(description="Aprobar prendas seleccionadas y otorgar puntos")
def aprobar_prendas(modeladmin, request, queryset):
    for prenda in queryset.filter(validada=False):
        prenda.validada = True
        prenda.save()
        
        perfil = prenda.donante.perfil
        perfil.puntos += 10
        perfil.save()
        
        Transaccion.objects.create(
            usuario=prenda.donante,
            tipo='DONACION',
            puntos=10,
            detalle=f"Validación: {prenda.tipo} ({prenda.talla})"
        )

@admin.action(description="🛠️ Mantenimiento: Borrar registros de hace más de 1 año")
def limpieza_profunda(modeladmin, request, queryset):
    hace_un_ano = timezone.now() - timedelta(days=365)
    objetos_antiguos = queryset.filter(fecha_creacion__lt=hace_un_ano)
    
    contador = 0
    for obj in objetos_antiguos:
        # Borrar archivos físicos de las fotos para liberar espacio
        for foto in [obj.foto1, obj.foto2, obj.foto3]:
            if foto and os.path.isfile(foto.path):
                os.remove(foto.path)
        obj.delete()
        contador += 1
    
    modeladmin.message_user(request, f"Se han eliminado {contador} registros antiguos y sus archivos.")

class PrendaAdmin(admin.ModelAdmin):
    # Añadimos 'ver_foto' a la lista

# Añadimos 'fecha_entrega' a la vista principal
    list_display = ('ver_foto', 'tipo', 'centro', 'fecha_entrega', 'fecha_creacion', 'validada')
    list_filter = ('fecha_entrega', 'validada', 'centro')
    # Ordenar por fecha de entrega para ver lo que llega pronto
    ordering = ('fecha_entrega',)
    actions = [aprobar_prendas]
    actions = [aprobar_y_logros, limpieza_profunda] # Añadimos la nueva acción
    
    # Función para generar la miniatura
    def ver_foto(self, obj):
        if obj.foto1:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', obj.foto1.url)
        return "Sin foto"
    
    ver_foto.short_description = 'Imagen'

admin.site.register(Prenda, PrendaAdmin)
admin.site.register(CentroAcopio)
admin.site.register(Perfil)
admin.site.register(Transaccion)