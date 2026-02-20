from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta  # Se usa para calcular fechas
from empresas.models import Empresa, OPCIONES_IMPAGOS # Importamos todo junto aquí

class CRMConfig(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='crm_config')
    tiene_cedidos = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CRM - {self.empresa.nombre}"
    
class Expediente(models.Model):
    ESTADOS_GESTION = [
        ('ACTIVO', 'Con Deuda'),
        ('PAGADO', 'Deuda Cero'),
        ('CEDIDO', 'Cedido'),
        ('ACUERDO', 'Acuerdo de Pago'),
        ('INUBICABLE', 'Inubicable'),
    ]

    CAUSAS_IMPAGO = [
        ('NO_QUIERE', 'No quiere pagar'),
        ('CORTA', 'Atiende y corta'),
        ('AYUDA_FAMILIAR', 'Buscando ayuda familiar'),
        ('INEXISTENTE', 'Teléfono inexistente'),
        ('FUERA_SERVICIO', 'Teléfono fuera de servicio'),
        ('EQUIVOCADO', 'Teléfono equivocado'),
        ('NO_ATIENDE', 'No atiende'),
        ('INTENTARA', 'Va a intentar conseguir el dinero'),
        ('PAGARA', 'Pagará'),
        ('REEMBOLSADO', 'Reembolsado'),
        ('SE_REEMBOLSA', 'Se reembolsará'),
        ('NO_PUEDE', 'No puede pagar'),
        ('ESPERANDO', 'Esperando respuesta'),
    ]

    OPCIONES_COMENTARIO = [
        ('SIN_RESPUESTA', 'No tiene respuesta de la academia'),
        ('ESTAFADO', 'Se siente estafado'),
        ('SIN_TRABAJO', 'Se encuentra sin trabajo'),
        ('DESCONOCE', 'No conoce la academia'),
        ('INCUMPLIMIENTO', 'No cumple el compromiso'),
    ]

    # Relaciones
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='expedientes')
    agente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cartera')
    
    # Datos Deudor
    numero_expediente = models.CharField(max_length=100, unique=True, blank=True)
    deudor_nombre = models.CharField(max_length=255)
    deudor_dni = models.CharField(max_length=20, blank=True, null=True)
    deudor_telefono = models.CharField(max_length=50)
    deudor_email = models.EmailField(blank=True, null=True)
    deudor_direccion = models.TextField(blank=True, null=True) 
    fecha_cesion = models.DateField(null=True, blank=True)
    
    # Datos Financieros
    tipo_producto = models.CharField(max_length=50, choices=OPCIONES_IMPAGOS, blank=True, null=True)
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=12, decimal_places=2)
    monto_recuperado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cuotas_totales = models.IntegerField(default=1, null=True, blank=True)
    
    fecha_compra = models.DateField(null=True, blank=True)
    fecha_impago = models.DateField(null=True, blank=True)
    fecha_recepcion = models.DateField(default=timezone.now)

    # Estado y Seguimiento
    estado = models.CharField(max_length=20, choices=ESTADOS_GESTION, default='ACTIVO')
    causa_impago = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    comentario_estandar = models.CharField(max_length=50, choices=OPCIONES_COMENTARIO, blank=True, null=True)
    fecha_pago_promesa = models.DateField(null=True, blank=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    motivo_eliminacion = models.TextField(blank=True, null=True)
    comprobante = models.FileField(upload_to='crm/pagos/', null=True, blank=True)
    
    # Tics Seguimiento
    
    # W1
    w1 = models.BooleanField(default=False)
    fecha_w1 = models.DateTimeField(null=True, blank=True)
    estado_w1 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # LL1
    ll1 = models.BooleanField(default=False)
    fecha_ll1 = models.DateTimeField(null=True, blank=True)
    estado_ll1 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # W2
    w2 = models.BooleanField(default=False)
    fecha_w2 = models.DateTimeField(null=True, blank=True)
    estado_w2 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # LL2
    ll2 = models.BooleanField(default=False)
    fecha_ll2 = models.DateTimeField(null=True, blank=True)
    estado_ll2 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # W3
    w3 = models.BooleanField(default=False)
    fecha_w3 = models.DateTimeField(null=True, blank=True)
    estado_w3 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # LL3
    ll3 = models.BooleanField(default=False)
    fecha_ll3 = models.DateTimeField(null=True, blank=True)
    estado_ll3 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # W4
    w4 = models.BooleanField(default=False)
    fecha_w4 = models.DateTimeField(null=True, blank=True)
    estado_w4 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # LL4
    ll4 = models.BooleanField(default=False)
    fecha_ll4 = models.DateTimeField(null=True, blank=True)
    estado_ll4 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # W5
    w5 = models.BooleanField(default=False)
    fecha_w5 = models.DateTimeField(null=True, blank=True)
    estado_w5 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    
    # LL5
    ll5 = models.BooleanField(default=False)
    fecha_ll5 = models.DateTimeField(null=True, blank=True)
    estado_ll5 = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)

     # --- 6. GESTIÓN BURÓ / ASNEF ---

    # A. Buró Enviado (BE)
    buro_enviado = models.BooleanField(default=False)
    fecha_buro_enviado = models.DateTimeField(null=True, blank=True)

    # B. Buró Recibido (BR)
    buro_recibido = models.BooleanField(default=False)
    fecha_buro_recibido = models.DateTimeField(null=True, blank=True)

    # C. Llamada Seguimiento Buró (LLB)
    llamada_seguimiento_buro = models.BooleanField(default=False)
    fecha_llamada_seguimiento_buro = models.DateTimeField(null=True, blank=True)
    estado_llamada_seguimiento_buro = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)

    # D. Inscripción ASNEF
    asnef_inscrito = models.BooleanField(default=False)
    fecha_asnef_inscrito = models.DateTimeField(null=True, blank=True)

    # E. Llamada Salida ASNEF (LLA)
    llamada_seguimiento_asnef = models.BooleanField(default=False)
    fecha_llamada_seguimiento_asnef = models.DateTimeField(null=True, blank=True)
    estado_llamada_seguimiento_asnef = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)

    def eliminar_logico(self, motivo=None):
            self.activo = False
            self.fecha_eliminacion = timezone.now()
            if motivo:
                self.motivo_eliminacion = motivo
            self.save()

    def restaurar(self):
            self.activo = True
            self.fecha_eliminacion = None
            self.motivo_eliminacion = None
            self.save()

    def __str__(self):
        return f"{self.numero_expediente} - {self.deudor_nombre}"
    
    @property
    def ultimo_mensaje_fecha(self):
        # NOTA: Agregué los nuevos campos (LLB y LLA) al cálculo
        fechas = [
            self.fecha_w1, self.fecha_ll1, 
            self.fecha_w2, self.fecha_ll2, 
            self.fecha_w3, self.fecha_ll3, 
            self.fecha_w4, self.fecha_ll4, 
            self.fecha_w5, self.fecha_ll5,
            self.fecha_llamada_seguimiento_buro, # LLB
            self.fecha_llamada_seguimiento_asnef # LLA
        ]
        fechas_reales = [f for f in fechas if f is not None]
        if fechas_reales:
            return max(fechas_reales)
        return None

    @property
    def tiempo_en_impago(self):
        if self.fecha_impago:
            delta = timezone.now().date() - self.fecha_impago
            return delta.days
        return 0

    @property
    def deuda_pendiente(self):
        return self.monto_original - self.monto_recuperado

    @property
    def fecha_finalizacion_financiacion(self):
        """Calcula cuándo termina de pagar basándose en la fecha de compra y cuotas totales"""
        if not self.fecha_compra or not self.cuotas_totales:
            return None
        # AQUÍ QUITAMOS EL IMPORT INTERNO PORQUE YA LO PUSIMOS ARRIBA
        return self.fecha_compra + relativedelta(months=self.cuotas_totales)

    @property
    def cuotas_pagadas_estimadas(self):
        if self.monto_original <= 0 or self.cuotas_totales <= 0:
            return 0
        valor_cuota = float(self.monto_original) / self.cuotas_totales
        return int(float(self.monto_recuperado) // valor_cuota)

    @property
    def cuotas_restantes(self):
        return max(0, self.cuotas_totales - self.cuotas_pagadas_estimadas)

    @property
    def deuda_total_sistema(self):
        return float(self.monto_original) - float(self.monto_recuperado)
    
    @property
    def veces_en_impago(self):
        return Expediente.objects.filter(
            empresa=self.empresa,
            deudor_nombre__iexact=self.deudor_nombre
        ).count()
    
    def get_descuento_acumulado(self):
        """Suma el campo 'descuento' de todos los pagos registrados"""
        from django.db.models import Sum
        total = self.pagos.aggregate(total=Sum('descuento'))['total']
        return total or 0.00
    
    @property
    def puede_ser_cedido(self):
        """Condición visual para habilitar el botón de cesión"""
        # 1. ¿La empresa tiene módulo de cedidos activo?
        if not hasattr(self.empresa, 'crm_config') or not self.empresa.crm_config.tiene_cedidos:
            return False
            
        # 2. CORRECCIÓN: ¿El producto específico admite cesión?
        PRODUCTOS_CESIBLES = ['SEQURA_MANUAL', 'AUTOFINANCIACION', 'AUTOFINANCIADO']
        if self.tipo_producto not in PRODUCTOS_CESIBLES:
            return False
            
        # 3. Solo aplica a impagos activos
        if self.estado != 'ACTIVO':
            return False
            
        # 4. Superar 67 días de mora
        dias_mora = (timezone.now().date() - self.fecha_impago).days if self.fecha_impago else 0
        return dias_mora > 67

    @property
    def faltantes_cesion(self):
        """Devuelve una lista con los errores si falta algún requisito estricto"""
        errores = []
        
        if not hasattr(self.empresa, 'crm_config') or not self.empresa.crm_config.tiene_cedidos:
            errores.append("La empresa no admite cesiones de cartera.")
            
        # CORRECCIÓN: Validar Producto
        PRODUCTOS_CESIBLES = ['SEQURA_MANUAL', 'AUTOFINANCIACION', 'AUTOFINANCIADO']
        if self.tipo_producto not in PRODUCTOS_CESIBLES:
            errores.append(f"El producto '{self.get_tipo_producto_display()}' no es apto para cesiones.")
            
        dias_mora = (timezone.now().date() - self.fecha_impago).days if self.fecha_impago else 0
        if dias_mora <= 67:
            errores.append(f"El expediente debe superar los 67 días de mora (actual: {dias_mora} días).")
            
        # Validar Documentación individualizada
        if not self.documentos.filter(tipo='CONTRATO').exists():
            errores.append("Falta cargar el 'Contrato de Cesión' en la pestaña de documentos de este expediente.")
            
        return errores
    
    @property
    def tiene_contrato_cesion(self):
        """Devuelve True si el expediente ya tiene el contrato de cesión cargado."""
        return self.documentos.filter(tipo='CONTRATO').exists()

    @property
    def user(self):
        """Redirige las peticiones de .user a .agente para evitar errores de atributos"""
        return self.agente

class RegistroPago(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_pago = models.DateField(default=timezone.now) 
    metodo_pago = models.CharField(max_length=100, default='TRANSFERENCIA')
    comprobante = models.FileField(upload_to='pagos/comprobantes/', null=True, blank=True)
    comision = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.monto} - {self.expediente.deudor_nombre}"
    
class DocumentoExpediente(models.Model):
    TIPO_DOC = [
        ('CONTRATO', 'Contrato de Cesión'),
        ('OTRO', 'Otra Documentación'),
    ]
    
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=20, choices=TIPO_DOC)
    archivo = models.FileField(upload_to='crm/documentos/')
    nombre_archivo = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.expediente.deudor_nombre}"