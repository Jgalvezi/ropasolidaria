from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class CentroAcopio(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    google_maps_link = models.TextField(blank=True)
    
    # NUEVOS CAMPOS
    capacidad_maxima = models.IntegerField(default=50, help_text="Máximo de prendas que puede almacenar")
    en_vacaciones = models.BooleanField(default=False, help_text="Marcar si el centro está cerrado temporalmente")

    def prendas_actuales(self):
        # Cuenta cuántas prendas hay físicas (validadas pero aún no retiradas/entregadas a destino final)
        # Asumiendo que las prendas validadas ocupan espacio en el inventario
        return self.prenda_set.filter(validada=True).count()

    def porcentaje_ocupacion(self):
        if self.capacidad_maxima > 0:
            return (self.prendas_actuales() * 100) / self.capacidad_maxima
        return 0

    def esta_lleno(self):
        return self.prendas_actuales() >= self.capacidad_maxima

    def __str__(self):
        return self.nombre
        
class ResenaCentro(models.Model):
    centro = models.ForeignKey('CentroAcopio', on_delete=models.CASCADE, related_name='resenas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    calificacion = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) # 1 a 5 estrellas
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.centro.nombre}"

class Logro(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255)
    icono = models.CharField(max_length=50, help_text="Clase de Bootstrap Icon (ej: bi-star-fill)")
    color = models.CharField(max_length=20, default="#FFD700")

    def __str__(self):
        return self.nombre

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    puntos = models.IntegerField(default=0)
    centros = models.ManyToManyField(CentroAcopio, related_name="usuarios")
    logros = models.ManyToManyField(Logro, blank=True)

    def tiene_bloqueo_por_mora(self):
        hoy = timezone.now().date()
        # Contamos cuántas prendas vencidas (no validadas y fecha pasada) tiene
        moras = self.user.prenda_set.filter(validada=False, fecha_entrega__lt=hoy).count()
        return moras >= 3 # Bloqueo si debe 3 o más entregas

    # Sistema de Niveles Lógico
    def get_nivel(self):
        if self.puntos < 50:
            return {'nombre': 'Bronce', 'color': '#cd7f32', 'icon': 'bi-shield-shaded'}
        elif self.puntos < 150:
            return {'nombre': 'Plata', 'color': '#c0c0c0', 'icon': 'bi-shield-fill'}
        else:
            return {'nombre': 'Oro', 'color': '#ffd700', 'icon': 'bi-trophy-fill'}

    def __str__(self):
        return f"{self.user.username} - {self.get_nivel()['nombre']}"
        
        
class Prenda(models.Model):
    # Opciones para el tipo de ropa
    TIPOS_ROPA = [('CAMISA', 'Camisa'),('POLERA', 'Polera'),('PANTALON', 'Pantalón'),('ZAPATOS', 'Zapatos'),('CHALECO', 'Chaleco'),('POLERON', 'Polerón'),('ABRIGO', 'Abrigo')]
    TALLAS = [('S', 'S - Pequeño'), ('M', 'M - Medio'), ('L', 'L - Largo'), ('XL', 'XL - Extra Largo'), ('T33-34', 'T33-34'), ('T35-36', 'T35-36'), ('T37-38', 'T37-38'), 
        ('T39-40', 'T39-40'), ('T41-42', 'T41-42'), ('T43-44', 'T43-44')]
    CONDICIONES = [('NUEVO', 'Nuevo'), ('USADO_EXC', 'Usado (Excelente)'), ('USADO_BUENO', 'Usado (Buen estado)'), ('USADO_DET', 'Usado (Con detalles)')]
    
    donante = models.ForeignKey(User, on_delete=models.CASCADE)
    centro = models.ForeignKey(CentroAcopio, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS_ROPA) # Ahora con choices
    talla = models.CharField(max_length=20, choices=TALLAS)
    condicion = models.CharField(max_length=20, choices=CONDICIONES)
    fecha_creacion = models.DateTimeField(auto_now_add=True) # Para el gráfico mensual

    # Fotos
    foto1 = models.ImageField(upload_to='prendas/') # Obligatoria
    foto2 = models.ImageField(upload_to='prendas/', blank=True, null=True) # Opcional
    foto3 = models.ImageField(upload_to='prendas/', blank=True, null=True) # Opcional
    
    disponible = models.BooleanField(default=True)
    validada = models.BooleanField(default=False) # Nueva línea
    fecha_entrega = models.DateField(
            null=True, 
            blank=True, 
            help_text="¿Qué día aproximado llevarás la prenda al centro?"
        )
 
    def __str__(self):
        estado = "✅" if self.validada else "⏳"
        return f"{estado} {self.tipo} - {self.donante.username}"
        
class Transaccion(models.Model):
    TIPO_CHOICES = [('DONACION', 'Donación'), ('RETIRO', 'Retiro')]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    puntos = models.IntegerField()
    detalle = models.CharField(max_length=200) # Ej: "Donó Camisa XL"
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha'] # Lo más reciente primero
        
