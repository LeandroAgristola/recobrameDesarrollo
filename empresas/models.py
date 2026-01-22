from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import TimeStampedModel

class Empresa(TimeStampedModel):
    class TipoComision(models.TextChoices):
        PORCENTAJE_FIJO = 'FIJO', _('Porcentaje Fijo Único')
        POR_TRAMOS = 'TRAMOS', _('Por Tramos (Escalonada)')

    # --- DATOS IDENTIFICATIVOS ---
    nombre = models.CharField(_('Nombre Comercial'), max_length=100, unique=True)
    razon_social = models.CharField(_('Razón Social'), max_length=150, blank=True)
    cif_nif = models.CharField(_('CIF/NIF'), max_length=20, blank=True)
    direccion = models.CharField(_('Dirección'), max_length=250, blank=True)
    fecha_alta = models.DateField(_('Fecha de Alta'), default=timezone.now)
    
    # --- DATOS OPERATIVOS ---
    contacto_incidencias = models.CharField(_('Contacto Incidencias'), max_length=100, blank=True)
    email_incidencias = models.EmailField(_('Email Incidencias'), blank=True)
    datos_bancarios = models.TextField(_('Datos Bancarios'), blank=True)
    
    # Campos de texto libre para información variada
    tipos_impagos = models.TextField(_('Tipos de Impagos'), blank=True, help_text="Ej: Tarjeta, Transferencia, Recibo...") 
    cursos = models.TextField(_('Cursos / Productos'), blank=True, help_text="Listado de cursos o productos que vende") 
    notas = models.TextField(_('Notas Internas'), blank=True) 

    # --- DOCUMENTACIÓN ---
    contrato_colaboracion = models.FileField(
        _('Contrato de Colaboración'),
        upload_to='contratos/colaboracion/',
        blank=True, null=True
    )
    contrato_cesion = models.FileField(
        _('Contrato de Cesión de Crédito'),
        upload_to='contratos/cesion/',
        blank=True, null=True,
        help_text="Opcional. Requerido para ASNEF/Buró"
    )

    # --- CONFIGURACIÓN ECONOMICA ---
    tipo_comision = models.CharField(
        _('Esquema de Comisiones'),
        max_length=6,
        choices=TipoComision.choices,
        default=TipoComision.PORCENTAJE_FIJO
    )
    
    porcentaje_unico = models.DecimalField(
        _('% Único'),
        max_digits=5, decimal_places=2,
        default=0.00,
        blank=True, null=True
    )
    
    # Soft Delete (Desactivación lógica)
    fecha_baja = models.DateField(_('Fecha de Baja'), null=True, blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class TramoComision(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tramos')
    monto_minimo = models.DecimalField(_('Desde (€)'), max_digits=10, decimal_places=2)
    monto_maximo = models.DecimalField(_('Hasta (€)'), max_digits=10, decimal_places=2, null=True, blank=True)
    porcentaje = models.DecimalField(_('% Comisión'), max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Tramo de Comisión"
        verbose_name_plural = "Tramos de Comisión"
        ordering = ['monto_minimo']