from django.db import models
from empresas.models import Empresa
from django.utils import timezone

class CRMConfig(models.Model):
    """Asocia una empresa con su configuración de CRM"""
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='crm_config')
    tiene_cedidos = models.BooleanField(default=False) # Se activará si hay SeQura Manual
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __clanes__(self):
        return f"CRM - {self.empresa.nombre}"

class Expediente(models.Model):
    ESTADOS = [
        ('ACTIVO', 'Con Deuda'),
        ('PAGADO', 'Deuda Cero'),
        ('CEDIDO', 'Cedido (SeQura)'),
    ]

    activo = models.BooleanField(default=True) # True = Lista principal, False = Papelera
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='expedientes')
    numero_expediente = models.CharField(max_length=100, unique=True)
    deudor_nombre = models.CharField(max_length=255)
    deudor_dni = models.CharField(max_length=20)
    
    monto_original = models.DecimalField(max_digits=12, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=12, decimal_places=2) # Este bajará con los pagos
    
    tipo_producto = models.CharField(max_length=50) # Stripe, SeQura Manual, etc.
    fecha_recepcion = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVO')

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

class RegistroPago(models.Model):
    """Para la pestaña REG_recobro"""
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    metodo_pago = models.CharField(max_length=100) # Transferencia, tarjeta, etc.
    comprobante = models.FileField(upload_to='pagos/comprobantes/', null=True, blank=True)