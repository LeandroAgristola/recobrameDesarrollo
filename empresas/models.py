from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Q

# Mantenemos tus opciones (Agregamos SEQURA_PASS si no estaba)
# Mantenemos solo los PRODUCTOS reales de deuda
OPCIONES_IMPAGOS = [
    ('SEQURA_HOTMART', 'SeQura Hotmart'),
    ('SEQURA_MANUAL', 'SeQura Manual'),
    ('SEQURA_COPECART', 'SeQura Copecart'),
    ('SEQURA_PASS', 'SeQura Pass'), # Es un producto (refinanciado)
    ('AUTO_STRIPE', 'Auto Stripe'),
    ('AUTOFINANCIACION', 'Autofinanciación'),
    ('TODOS', '--- TODOS LOS PRODUCTOS ---'),
]

class Empresa(models.Model):
    # === DATOS IDENTIDAD ===
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=100)
    cif_nif = models.CharField(max_length=20, unique=True)
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

    # === GESTIÓN DE BURÓ Y ASNEF ===
    costo_buro = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00, 
        help_text="Costo individual de cada Buró enviado"
    )
    habilita_buro_notificacion = models.BooleanField(
        default=False, 
        help_text="Aprobar envío de Buró de Notificación (independiente de cesiones)"
    )
    
    # === ARCHIVOS ===
    contrato_colaboracion = models.FileField(upload_to='contratos/', null=True, blank=True)
    contrato_cesion = models.FileField(upload_to='contratos/', null=True, blank=True)

    # === MÉTRICAS DE CARGA (Nuevos) ===
    casos_nuevos_semana = models.PositiveIntegerField(
        default=0, 
        help_text="Casos que entraron en impago en los últimos 7 días según el último reporte."
    )
    fecha_ultima_importacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha y hora de la última carga masiva."
    )

    # Puedes agregar también el monto para dar más valor
    monto_nuevo_semana = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Suma del monto original de los casos nuevos de la semana."
    )

    # NOTA: Eliminamos tipo_comision, porcentaje_unico y porcentaje_base
    # Ahora la lógica estará en el modelo EsquemaComision

    # === PROPERTIES PARA LISTADO  ===
    # === NUEVA LÓGICA PARA ASNEF ===
    @property
    def admite_asnef(self):
        """
        Verifica si la empresa cumple los requisitos para enviar a ASNEF:
        1. Tener productos que admitan cesión.
        2. Tener el contrato de cesión cargado.
        """
        PRODUCTOS_CESIBLES = ['SEQURA_MANUAL', 'AUTOFINANCIACION', 'SEQURA_PASS']
        
        # Si no hay productos contratados o falta el archivo físico del contrato, es False directo
        if not self.tipos_impagos or not self.contrato_cesion:
            return False
            
        # Convertimos el string de tipos de impago ('SEQURA_MANUAL, AUTO_STRIPE') en una lista
        productos_empresa = [p.strip() for p in self.tipos_impagos.split(',')]
        
        # Verificamos si al menos uno de sus productos coincide con los permitidos para cesión
        tiene_producto_cesible = any(prod in PRODUCTOS_CESIBLES for prod in productos_empresa)
        
        return tiene_producto_cesible


    @property
    def monto_recuperado(self):
        # CAMBIO: self.expedientes en lugar de self.expediente_set
        resultado = self.expedientes.aggregate(total=Sum('monto_recuperado'))
        return resultado['total'] or 0.00

    @property
    def cantidad_recuperados(self):
        return self.expedientes.filter(estado='PAGADO').count()

    @property
    def deuda_actual(self):
        resultado = self.expedientes.filter(activo=True).exclude(estado='PAGADO').aggregate(total=Sum('monto_actual'))
        return resultado['total'] or 0.00

    @property
    def cantidad_activos(self):
        return self.expedientes.filter(activo=True).exclude(estado='PAGADO').count()

    @property
    def total_comisionado(self):
        # Asumiendo relación con RegistroPago
        resultado = self.expedientes.aggregate(total=Sum('pagos__comision'))
        return resultado['total'] or 0.00

    @property
    def deuda_total(self):
        return self.deuda_actual
    
    # Este alias es útil si en algún template usaste 'deuda_total'
    @property
    def deuda_total(self):
        return self.deuda_actual

    def __str__(self):
        return self.nombre

# === NUEVO MODELO PARA REGLAS DE COMISIÓN ===
class EsquemaComision(models.Model):
    CASOS = [('IMPAGO', 'Impago'), ('CEDIDO', 'Cedido')]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='esquemas')
    
    # 1. ¿A qué aplica esta regla?
    tipo_caso = models.CharField(max_length=20, choices=CASOS, default='IMPAGO')

    # Puede ser 'TODOS' para aplicar a todos, o un código específico
    tipo_producto = models.CharField(max_length=50, choices=OPCIONES_IMPAGOS, blank=True)

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