# empresas/models.py (Reemplaza o actualiza tu archivo)

from django.db import models
from django.utils import timezone

# Mantenemos tus opciones (Agregamos SEQURA_PASS si no estaba)
OPCIONES_IMPAGOS = [
    ('SEQURA_HOTMART', 'SeQura Hotmart'),
    ('SEQURA_MANUAL', 'SeQura Manual'),
    ('SEQURA_COPECART', 'SeQura Copecart'),
    ('SEQURA_PASS', 'SeQura Pass'),
    ('AUTO_STRIPE', 'Auto Stripe'),
    ('AUTOFINANCIACION', 'Autofinanciación'),
]

class Empresa(models.Model):
    # === DATOS IDENTIDAD ===
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=100)
    cif_nif = models.CharField(max_length=20)
    fecha_alta = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    fecha_baja = models.DateField(null=True, blank=True)
    
    # === CONTACTO ===
    persona_contacto = models.CharField(max_length=100, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=50, null=True, blank=True)
    email_contacto = models.EmailField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    
    # === OPERATIVA ===
    contacto_incidencias = models.CharField(max_length=100, null=True, blank=True)
    email_incidencias = models.EmailField(max_length=100, null=True, blank=True)
    
    # === CONFIGURACIÓN GENERAL ===
    # Guardamos los tipos seleccionados como texto separado por comas
    # Ej: "SEQURA_HOTMART, AUTO_STRIPE"
    tipos_impagos = models.CharField(max_length=255, blank=True)
    
    cursos = models.TextField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    datos_bancarios = models.TextField(blank=True, null=True)
    
    # === ARCHIVOS ===
    contrato_colaboracion = models.FileField(upload_to='contratos/', null=True, blank=True)
    contrato_cesion = models.FileField(upload_to='contratos/', null=True, blank=True)

    # NOTA: Eliminamos tipo_comision, porcentaje_unico y porcentaje_base
    # Ahora la lógica estará en el modelo EsquemaComision

    # === PROPERTIES PARA LISTADO (Placeholders) ===
    @property
    def total_recobrado(self): return 0.00
    @property
    def deuda_actual(self): return 0.00
    @property
    def cantidad_recuperados(self): return 0
    @property
    def deuda_total(self): return 0.00
    @property
    def cantidad_activos(self): return 0
    @property
    def total_comisionado(self): return 0.00

    def __str__(self):
        return self.nombre

# === NUEVO MODELO PARA REGLAS DE COMISIÓN ===
class EsquemaComision(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='esquemas')
    
    # 1. ¿A qué aplica esta regla?
    TIPO_CASO_CHOICES = [('IMPAGO', 'Gestión de Impago'), ('CEDIDO', 'Cartera Cedida')]
    tipo_caso = models.CharField(max_length=20, choices=TIPO_CASO_CHOICES, default='IMPAGO')

    # Si es NULL, aplica a "Todos los productos". Si tiene valor, solo a ese.
    tipo_producto = models.CharField(
        max_length=50, 
        choices=OPCIONES_IMPAGOS, 
        blank=True, null=True
    )

    # 2. ¿Cómo se cobra?
    MODALIDAD_CHOICES = [('FIJO', 'Porcentaje Fijo'), ('TRAMOS', 'Escala por Tramos')]
    modalidad = models.CharField(max_length=10, choices=MODALIDAD_CHOICES, default='FIJO')
    
    porcentaje_fijo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        prod = self.get_tipo_producto_display() or "Todos"
        return f"{self.empresa} - {self.tipo_caso} - {prod}"

# === MODELO DE TRAMOS (AHORA APUNTA A ESQUEMA) ===
class TramoComision(models.Model):
    esquema = models.ForeignKey(EsquemaComision, on_delete=models.CASCADE, related_name='tramos')
    monto_minimo = models.DecimalField(max_digits=12, decimal_places=2)
    monto_maximo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)