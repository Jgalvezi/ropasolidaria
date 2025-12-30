"""
URL configuration for RopaSolidaria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from donaciones import views
#from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Login/Logout/Password
    path('registro/', views.registro, name='registro'),
    path('', views.home, name='home'), # Página de inicio   
    path('catalogo/', views.catalogo_prendas, name='catalogo'), 
 
    path('donar/', views.donar_prenda, name='donar'),
# Gestión de prendas y usuario
    path('historial/', views.ver_historial, name='historial'),
    path('cancelar-entrega/<int:prenda_id>/', views.cancelar_entrega, name='cancelar_entrega'),
    
    path('solicitar/<int:prenda_id>/', views.solicitar_prenda, name='solicitar'),
    path('centros/', views.lista_centros, name='centros'),
    path('certificado/<int:prenda_id>/', views.descargar_certificado, name='certificado'),
    path('admin/calendario/', views.calendario_entregas, name='admin_calendario'),  
 
    path('admin-logistica/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logistica/usuarios/', views.buscar_usuarios_admin, name='buscar_usuarios'),

# Gestión administrativa
    path('admin-logistica/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logistica/usuarios/', views.buscar_usuarios_admin, name='buscar_usuarios'),
    path('admin-logistica/calendario/', views.calendario_entregas, name='calendario_logistico'),

    path('admin-logistica/perfil/<int:user_id>/', views.perfil_usuario_admin, name='perfil_usuario_admin'),
    path('leaderboard/', views.leaderboard, name='leaderboard'), # Nueva URL para el ranking


    path('misiones/', views.misiones_semanales, name='misiones'),
    path('cancelar-entrega/<int:prenda_id>/', views.cancelar_entrega, name='cancelar_entrega'),

# Reseñas
    path('centro/<int:centro_id>/resena/', views.dejar_resena, name='dejar_resena'),
]
# Esto es lo que permite que las fotos se vean en el navegador durante desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)