from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import TimeStampedModel

class Empresa(TimeStampedModel):
    class TipoComision(models.TextChoices):
        PORCENTAJE_FIJO = 'FIJO', _('Porcentaje Fijo Único')
        POR_TRAMOS = 'TRAMOS', _('Por Tramos (Escalonada)')

    # --- DATOS IDENTIFICATIVOS ---
    # Quitamos unique=True de nombre para permitir duplicados si la razón social es distinta
    nombre = models.CharField(_('Nombre Comercial'), max_length=100) 
    razon_social = models.CharField(_('Razón Social'), max_length=150, blank=True)
    
    # Grid Fila 2
    cif_nif = models.CharField(_('CIF/NIF'), max_length=20, blank=True)
    persona_contacto = models.CharField(_('Persona de Contacto (General)'), max_length=100, blank=True)
    telefono_contacto = models.CharField(_('Teléfono General'), max_length=20, blank=True) # <--- NUEVO
    
    # Grid Fila 3
    email_contacto = models.EmailField(_('Email General'), blank=True)
    fecha_alta = models.DateField(_('Fecha de Alta'), default=timezone.now)
    
    # Grid Fila 4
    direccion = models.CharField(_('Dirección'), max_length=250, blank=True)
    
    # --- DATOS OPERATIVOS ---
    contacto_incidencias = models.CharField(_('Contacto Incidencias'), max_length=100, blank=True)
    email_incidencias = models.EmailField(_('Email Incidencias'), blank=True)
    datos_bancarios = models.TextField(_('Datos Bancarios'), blank=True)
    
    tipos_impagos = models.TextField(_('Tipos de Impagos'), blank=True)
    cursos = models.TextField(_('Cursos / Productos'), blank=True)
    notas = models.TextField(_('Notas Internas'), blank=True)

    # --- DOCUMENTACIÓN ---
    # Colaboración NO tiene blank=True (es obligatorio)
    contrato_colaboracion = models.FileField(upload_to='contratos/colaboracion/') 
    contrato_cesion = models.FileField(upload_to='contratos/cesion/', blank=True, null=True)

    # --- CONFIGURACIÓN ECONOMICA ---
    tipo_comision = models.CharField(max_length=6, choices=TipoComision.choices, default=TipoComision.PORCENTAJE_FIJO)
    porcentaje_unico = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    fecha_baja = models.DateField(_('Fecha de Baja'), null=True, blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']
        # REGLA: No puede existir una empresa con el MISMO nombre Y la MISMA razón social
        constraints = [
            models.UniqueConstraint(fields=['nombre', 'razon_social'], name='unique_empresa_nombre_razon')
        ]

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