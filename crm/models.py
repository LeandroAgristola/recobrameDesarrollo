# crm/models.py
from django.db import models
from empresas.models import Empresa
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta

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
    # Agregamos blank=True para que el formulario permita enviarlo vacío y la vista lo calcule
    numero_expediente = models.CharField(max_length=100, unique=True, blank=True)
    deudor_nombre = models.CharField(max_length=255)
    deudor_dni = models.CharField(max_length=20, blank=True, null=True)
    deudor_telefono = models.CharField(max_length=50)
    deudor_email = models.EmailField(blank=True, null=True)
    deudor_direccion = models.TextField(blank=True, null=True) 
    fecha_cesion = models.DateField(null=True, blank=True)
    
    # Datos Financieros
    tipo_producto = models.CharField(max_length=50)
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=12, decimal_places=2)
    monto_recuperado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cuotas_totales = models.IntegerField(default=1)
    
    fecha_compra = models.DateField(null=True, blank=True)
    fecha_impago = models.DateField()
    fecha_recepcion = models.DateField(default=timezone.now)

    # Estado y Seguimiento
    estado = models.CharField(max_length=20, choices=ESTADOS_GESTION, default='ACTIVO')
    causa_impago = models.CharField(max_length=50, choices=CAUSAS_IMPAGO, blank=True, null=True)
    comentarios = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    comentario_estandar = models.CharField(max_length=50, choices=OPCIONES_COMENTARIO, blank=True, null=True)
    fecha_pago_promesa = models.DateField(null=True, blank=True) # Para la lógica de "PAGARA"
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    motivo_eliminacion = models.TextField(blank=True, null=True)
    comprobante = models.FileField(upload_to='crm/pagos/', null=True, blank=True)
    
    # Tics Seguimiento
    # Almacenamos: boolean para UI, fecha de acción, y estado (causa_impago) en ese momento
    
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

    # ASNEF / BURO
    buro_enviado = models.BooleanField(default=False)
    buro_recibido = models.BooleanField(default=False)
    asnef_inscrito = models.BooleanField(default=False)
    llamada_seguimiento_asnef = models.BooleanField(default=False)

    def eliminar_logico(self, motivo=None): # <--- Actualizamos esto
            self.activo = False
            self.fecha_eliminacion = timezone.now()
            if motivo:
                self.motivo_eliminacion = motivo # Guardamos el motivo
            self.save()

    def restaurar(self):
            self.activo = True
            self.fecha_eliminacion = None
            self.motivo_eliminacion = None # <--- Limpiamos el motivo al restaurar
            self.save()

    def __str__(self):
        return f"{self.numero_expediente} - {self.deudor_nombre}"
    
    # Propiedad para obtener la última fecha de gestión automáticamente
    @property
    def ultimo_mensaje_fecha(self):
        fechas = [
            self.fecha_w1, self.fecha_ll1, 
            self.fecha_w2, self.fecha_ll2, 
            self.fecha_w3, self.fecha_ll3, 
            self.fecha_w4, self.fecha_ll4, 
            self.fecha_w5, self.fecha_ll5
        ]
        # Filtramos las que no son None
        fechas_reales = [f for f in fechas if f is not None]
        if fechas_reales:
            return max(fechas_reales)
        return None

    @property
    def tiempo_en_impago(self):
        delta = timezone.now().date() - self.fecha_impago
        return delta.days

    @property
    def deuda_pendiente(self):
        return self.monto_original - self.monto_recuperado

    @property
    def fecha_finalizacion_financiacion(self):
        """Calcula cuándo termina de pagar basándose en la fecha de compra y cuotas totales"""
        if not self.fecha_compra or not self.cuotas_totales:
            return None
        from dateutil.relativedelta import relativedelta
        return self.fecha_compra + relativedelta(months=self.cuotas_totales)

    @property
    def cuotas_pagadas_estimadas(self):
        """Calcula cuántas cuotas ha cubierto con el monto recuperado"""
        if self.monto_original <= 0 or self.cuotas_totales <= 0:
            return 0
        valor_cuota = float(self.monto_original) / self.cuotas_totales
        return int(float(self.monto_recuperado) // valor_cuota)

    @property
    def cuotas_restantes(self):
        """Cuotas que faltan para completar el plan (pagadas vs totales)"""
        return max(0, self.cuotas_totales - self.cuotas_pagadas_estimadas)

    @property
    def deuda_total_sistema(self):
        """
        Deuda total absoluta: 
        Lo que debería haber pagado a fecha de hoy (impagas) + lo que falta por vencer (deuda futura)
        Es simplemente: Monto Original - Monto Recuperado
        """
        return float(self.monto_original) - float(self.monto_recuperado)
    
    @property
    def veces_en_impago(self):
        """
        Cuenta cuántas veces ha figurado este nombre en la base de datos
        para la misma empresa (incluyendo registros actuales, pagados o en papelera).
        """
        return Expediente.objects.filter(
            empresa=self.empresa,
            deudor_nombre__iexact=self.deudor_nombre
        ).count()

    def __str__(self):
        return f"{self.numero_expediente} - {self.deudor_nombre}"


class RegistroPago(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=100)
    comprobante = models.FileField(upload_to='pagos/comprobantes/', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

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

