from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

from empresas.models import Empresa
from crm.models import Expediente, RegistroPago

class Perfil(models.Model):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('AGENTE', 'Agente de Recobro'),
        ('CONTABLE', 'Contable'),
        ('ABOGADO', 'Abogado'),
        ('CLIENTE', 'Cliente'),
    ]

    # Enlace al usuario nativo de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='CLIENTE')
    
    # --- DATOS COMUNES ---
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    # Cambio a ImageField nativo para usar con Render Storage
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    # --- CAMPOS DE ESTADO Y FECHAS ---
    fecha_alta = models.DateField(default=timezone.now, null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    requiere_cambio_clave = models.BooleanField(default=True, help_text="Exige al usuario cambiar su clave autogenerada al iniciar sesión por primera vez.")
    clave_temporal = models.CharField(max_length=50, blank=True, null=True, help_text="Almacena la clave generada automáticamente para mostrarla en el detalle.")
    
    # --- DATOS EXCLUSIVOS STAFF ---
    dni_nie = models.CharField(max_length=20, blank=True, null=True)
    netelip_number = models.CharField(max_length=20, blank=True, null=True, help_text="Número telefónico de Netelip")
    netelip_ext = models.CharField(max_length=20, blank=True, null=True)
    netelip_user = models.CharField(max_length=100, blank=True, null=True, help_text="Usuario de Netelip (Softphone)")
    netelip_pass = models.CharField(max_length=100, blank=True, null=True, help_text="Contraseña de Netelip")
    netelip_server = models.CharField(max_length=100, blank=True, null=True, help_text="Servidor SIP de Netelip")
    mercateli_id = models.CharField(max_length=50, blank=True, null=True)
    mercateli_despacho = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del despacho en Mercateli")
    contrato_colaboracion = models.FileField(upload_to='contratos_staff/', blank=True, null=True)

    # --- DATOS EXCLUSIVOS CLIENTES ---
    empresas_asignadas = models.ManyToManyField(Empresa, blank=True, related_name='usuarios_clientes')

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"

    # =======================================================
    # MÉTRICAS EN TIEMPO REAL PARA AGENTES
    # =======================================================
    @property
    def total_recobros(self):
        total = RegistroPago.objects.filter(expediente__agente=self.user).aggregate(Sum('monto'))['monto__sum']
        return total or 0.00

    @property
    def total_comisiones(self):
        total = RegistroPago.objects.filter(expediente__agente=self.user).aggregate(Sum('comision'))['comision__sum']
        return total or 0.00

    @property
    def casos_en_gestion(self):
        return Expediente.objects.filter(agente=self.user, activo=True, estado='ACTIVO').count()

    @property
    def casos_finalizados(self):
        # Count cases that are marked as paid (estado='PAGADO')
        return Expediente.objects.filter(
            agente=self.user,
            estado='PAGADO'
        ).count()

    @property
    def recobros_cantidad(self):
        return RegistroPago.objects.filter(expediente__agente=self.user).count()

    @property
    def cobro_promedio(self):
        pagos = RegistroPago.objects.filter(expediente__agente=self.user)
        if pagos.exists():
            total = pagos.aggregate(Sum('monto'))['monto__sum'] or 0
            return total / pagos.count()
        return 0.00

    @property
    def efectividad(self):
        total_casos = Expediente.objects.filter(agente=self.user).count()
        if total_casos > 0:
            return round((self.casos_finalizados / total_casos) * 100, 2)
        return 0.00

    @property
    def incidencia(self):
        total_agente = self.total_recobros
        total_global = RegistroPago.objects.aggregate(Sum('monto'))['monto__sum'] or 1
        if total_global > 1:
            return round((float(total_agente) / float(total_global)) * 100, 2)
        return 0.00