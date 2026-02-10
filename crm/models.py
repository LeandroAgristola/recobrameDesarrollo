# crm/models.py
from django.db import models
from empresas.models import Empresa
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

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
    
    # Tics Seguimiento
    # Tics Seguimiento (Mantenemos los booleanos para el checkbox visual, agregamos fechas para la lógica)
    # Tics Seguimiento (Agregamos las fechas)
    w1 = models.BooleanField(default=False)
    fecha_w1 = models.DateTimeField(null=True, blank=True)
    
    ll1 = models.BooleanField(default=False)
    fecha_ll1 = models.DateTimeField(null=True, blank=True)
    
    w2 = models.BooleanField(default=False)
    fecha_w2 = models.DateTimeField(null=True, blank=True)
    
    ll2 = models.BooleanField(default=False)
    fecha_ll2 = models.DateTimeField(null=True, blank=True)
    
    w3 = models.BooleanField(default=False)
    fecha_w3 = models.DateTimeField(null=True, blank=True)
    
    ll3 = models.BooleanField(default=False)
    fecha_ll3 = models.DateTimeField(null=True, blank=True)
    
    w4 = models.BooleanField(default=False)
    fecha_w4 = models.DateTimeField(null=True, blank=True)
    
    ll4 = models.BooleanField(default=False)
    fecha_ll4 = models.DateTimeField(null=True, blank=True)
    
    w5 = models.BooleanField(default=False)
    fecha_w5 = models.DateTimeField(null=True, blank=True)
    
    ll5 = models.BooleanField(default=False)
    fecha_ll5 = models.DateTimeField(null=True, blank=True)

    # ASNEF / BURO
    buro_enviado = models.BooleanField(default=False)
    buro_recibido = models.BooleanField(default=False)
    asnef_inscrito = models.BooleanField(default=False)
    llamada_seguimiento_asnef = models.BooleanField(default=False)

    def eliminar_logico(self):
        self.activo = False
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restaurar(self):
        self.activo = True
        self.fecha_eliminacion = None
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
    

