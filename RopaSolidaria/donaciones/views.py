from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Sum
from .models import Prenda, Perfil, CentroAcopio, Transaccion
from .forms import PrendaForm
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


# @login_required
# def admin_dashboard(request):
    # if not request.user.is_staff:
        # return redirect('home')

    # hoy = timezone.now().date()
    # prendas_hoy = Prenda.objects.filter(fecha_entrega=hoy, validada=False)
    
    # # Capacidad por centro (ejemplo: conteo de prendas actuales)
    # capacidad = CentroAcopio.objects.annotate(total_prendas=Count('prenda'))
    
    # return render(request, 'admin/dashboard_logistico.html', {
        # 'prendas_hoy': prendas_hoy,
        # 'capacidad': capacidad,
        # 'hoy': hoy
    # })
    
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    hoy = timezone.now().date()
    prendas_hoy = Prenda.objects.filter(fecha_entrega=hoy, validada=False)
    
    # Calculamos el promedio de calificación por centro
    stats_centros = CentroAcopio.objects.annotate(
        promedio_rating=Avg('resenas__calificacion')
    ).order_by('-promedio_rating')

    # Prendas atrasadas para la alerta roja
    prendas_atrasadas = Prenda.objects.filter(validada=False, fecha_entrega__lt=hoy)

    return render(request, 'admin/dashboard_logistico.html', {
        'prendas_hoy': prendas_hoy,
        'stats_centros': stats_centros,
        'prendas_atrasadas': prendas_atrasadas,
        'hoy': hoy,
    })

@login_required
def dejar_resena(request, centro_id):
    if request.method == 'POST':
        centro = get_object_or_404(CentroAcopio, id=centro_id)
        calificacion = request.POST.get('calificacion')
        comentario = request.POST.get('comentario')
        
        ResenaCentro.objects.create(
            centro=centro,
            usuario=request.user,
            calificacion=calificacion,
            comentario=comentario
        )
        messages.success(request, "¡Gracias por calificar el centro!")
    return redirect('centros')

@login_required
def cancelar_entrega(request, prenda_id):
    prenda = get_object_or_404(Prenda, id=prenda_id, donante=request.user, validada=False)
    prenda.delete()
    messages.warning(request, "La entrega ha sido cancelada correctamente.")
    return redirect('historial')
    
def misiones_semanales(request):
    misiones = [
        {'titulo': 'Donante Veloz', 'desc': 'Entrega una prenda antes de tu fecha límite.', 'recompensa': '+5 pts', 'progreso': 0},
        {'titulo': 'Ropero Solidario', 'desc': 'Dona 3 prendas de invierno (Abrigo/Poleron).', 'recompensa': '+20 pts', 'progreso': 60},
        {'titulo': 'Pionero', 'desc': 'Sé el primero en donar en un centro nuevo.', 'recompensa': 'Badge Especial', 'progreso': 10},
    ]
    return render(request, 'donaciones/misiones.html', {'misiones': misiones})

def leaderboard(request):
    # Obtenemos el top 10 de usuarios con más puntos, prefiriendo los que tienen perfil
    top_usuarios = Perfil.objects.select_related('user').order_by('-puntos')[:10]
    
    return render(request, 'donaciones/leaderboard.html', {
        'top_usuarios': top_usuarios
    })
    
@login_required
def perfil_usuario_admin(request, user_id):
    if not request.user.is_staff:
        return redirect('home')
    
    # Obtenemos el usuario que queremos inspeccionar
    usuario_inspeccionado = get_object_or_404(User, id=user_id)
    # Sus prendas
    prendas = Prenda.objects.filter(donante=usuario_inspeccionado).order_by('-fecha_creacion')
    
    return render(request, 'admin/perfil_usuario_detalle.html', {
        'usuario_target': usuario_inspeccionado,
        'prendas': prendas
    })

@login_required
def donar_prenda(request):
    # Verificar baneo antes de permitir donar
    if request.user.perfil.tiene_bloqueo_por_mora():
        messages.error(request, "⚠️ Tu cuenta está temporalmente bloqueada para nuevas donaciones debido a 3 o más entregas pendientes vencidas. Por favor, regulariza tu situación en el centro de acopio.")
        return redirect('historial')

@login_required
def buscar_usuarios_admin(request):
    if not request.user.is_staff:
        return redirect('home')

    query = request.GET.get('q', '')
    filtro_mora = request.GET.get('mora', False)
    hoy = timezone.now().date()

    # Buscador por nombre de usuario o email
    usuarios = User.objects.all()
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )

    # Lógica de filtro para usuarios con entregas vencidas
    if filtro_mora:
        # Obtenemos usuarios que tienen al menos una prenda pendiente con fecha anterior a hoy
        usuarios = usuarios.filter(
            prenda__validada=False,
            prenda__fecha_entrega__lt=hoy
        ).distinct()

    # Obtener prendas vencidas para cada usuario (para el botón de notificar)
    for u in usuarios:
        u.prendas_vencidas = u.prenda_set.filter(validada=False, fecha_entrega__lt=hoy).order_by('fecha_entrega')

    return render(request, 'admin/buscar_usuarios.html', {
        'usuarios': usuarios,
        'query': query,
        'filtro_mora': filtro_mora,
        'hoy': hoy
    })

  
@login_required
def calendario_entregas(request):
    # Solo el personal del staff puede ver la agenda
    if not request.user.is_staff:
        return redirect('home')
        
    entregas = Prenda.objects.filter(validada=False).exclude(fecha_entrega__isnull=True)
    return render(request, 'admin/calendario_logistico.html', {'entregas': entregas})
    
@login_required
def descargar_certificado(request, prenda_id):
    prenda = get_object_or_404(Prenda, id=prenda_id, donante=request.user, validada=True)
    
    # Crear la respuesta HTTP con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificado_Donacion_{prenda.id}.pdf"'

    # Crear el objeto PDF
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # --- Diseño del Certificado ---
    p.setStrokeColorRGB(0.05, 0.43, 0.99) # Azul RopaSolidaria
    p.rect(0.5*inch, 0.5*inch, width-1*inch, height-1*inch, stroke=1, fill=0)

    p.setFont("Helvetica-Bold", 26)
    p.drawCentredString(width/2, height-2*inch, "CERTIFICADO DE DONACIÓN")
    
    p.setFont("Helvetica", 14)
    p.drawCentredString(width/2, height-2.5*inch, "Otorgado por RopaSolidaria")

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height-4*inch, f"¡Gracias, {request.user.username.upper()}!")

    p.setFont("Helvetica", 12)
    texto = (f"Por la presente certificamos la donación de una prenda tipo {prenda.get_tipo_display()} "
             f"talla {prenda.talla}, realizada en el centro {prenda.centro.nombre}.")
    
    # Dibujar texto largo
    text_obj = p.beginText(1*inch, height-5*inch)
    text_obj.setFont("Helvetica", 12)
    text_obj.textLine(texto)
    p.drawText(text_obj)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, height-6*inch, f"Puntos Solidarios Sumados: +10")
    p.drawString(1*inch, height-6.3*inch, f"Fecha de Validación: {prenda.fecha_creacion.strftime('%d/%m/%Y')}")

    # Pie de página
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, 1*inch, "Este documento es un comprobante digital de tu impacto social.")

    p.showPage()
    p.save()
    return response
    
@login_required
def ver_perfil_estadisticas(request):
    # 1. Datos para gráfico mensual (Donaciones del usuario actual)
    stats_mensuales = Prenda.objects.filter(donante=request.user, validada=True) \
        .annotate(mes=TruncMonth('fecha_creacion')) \
        .values('mes') \
        .annotate(total=Count('id')) \
        .order_by('mes')

    # 2. Datos para gráfico Top 10 Donantes por Centro
    # (Agrupamos por centro y usuario para ver quién dona más en cada lugar)
    top_donantes = Prenda.objects.filter(validada=True) \
        .values('centro__nombre', 'donante__username') \
        .annotate(total=Count('id')) \
        .order_by('-total')[:10]

    return render(request, 'donaciones/perfil_stats.html', {
        'stats_mensuales': stats_mensuales,
        'top_donantes': top_donantes,
    })

@login_required
def home(request):
    # Ejemplo: Si el usuario tiene logros pero no ha sido notificado (lógica simple)
    # Aquí puedes integrar una lógica más compleja, por ahora usemos un mensaje de éxito
    total_donaciones = Prenda.objects.filter(validada=True).count()
    centros_activos = CentroAcopio.objects.count()
    
    return render(request, 'donaciones/home.html', {
        'total_donaciones': total_donaciones, 
        'centros_activos': centros_activos
    })

def catalogo_prendas(request):
    # Obtener el parámetro de la URL (ej: ?talla=M)
    talla_buscada = request.GET.get('talla')
    
    prendas = Prenda.objects.filter(validada=True, disponible=True)
    
    if talla_buscada:
        prendas = prendas.filter(talla=talla_buscada)
        
    return render(request, 'donaciones/catalogo.html', {
        'prendas': prendas,
        'tallas': ['S', 'M', 'L', 'XL'], # Para generar los botones
        'talla_activa': talla_buscada
    })

@login_required
def donar_prenda(request):
    if request.method == 'POST':
        form = PrendaForm(request.POST, request.FILES)
        if form.is_valid():
            prenda = form.save(commit=False)
            prenda.donante = request.user
            prenda.save()
            messages.info(request, "❤️ Donación enviada. Será visible cuando un administrador la valide.")
            return redirect('historial')
    else:
        form = PrendaForm()
    return render(request, 'donaciones/donar.html', {'form': form})

@login_required
def solicitar_prenda(request, prenda_id):
    prenda = get_object_or_404(Prenda, id=prenda_id)
    perfil = request.user.perfil
    
    if perfil.puntos >= 20: # Ajustado a >= 20 según tu regla
        perfil.puntos -= 10
        perfil.save()
        prenda.disponible = False
        prenda.save()
        
        Transaccion.objects.create(
            usuario=request.user,
            tipo='RETIRO',
            puntos=10,
            detalle=f"Retiró {prenda.tipo} ({prenda.talla})"
        )
        messages.success(request, "✅ Solicitud procesada. ¡Disfruta tu prenda!")
    else:
        messages.error(request, "❌ Necesitas al menos 20 puntos para solicitar prendas.")
    
    return redirect('catalogo')

@login_required
def ver_historial(request):
    pendientes = Prenda.objects.filter(donante=request.user, validada=False)
    realizadas = Prenda.objects.filter(donante=request.user, validada=True)
    return render(request, 'donaciones/historial.html', {
        'pendientes': pendientes,
        'realizadas': realizadas,
        'puntos': request.user.perfil.puntos
    })
    
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('catalogo')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})
    
def lista_centros(request):
    centros = CentroAcopio.objects.all()
    return render(request, 'donaciones/centros.html', {'centros': centros})