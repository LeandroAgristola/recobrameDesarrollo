import datetime
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# 1. MODELO ABSTRACTO (Plantilla)
# Este modelo NO crea una tabla en la base de datos.
# Sirve de molde para que otros modelos hereden sus campos.
class TimeStampedModel(models.Model):
    """
    Un modelo base abstracto que proporciona campos auto-actualizados
    de creación y modificación.
    """
    created_at = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True, # Se pone la fecha actual solo al crear
        help_text="Fecha y hora en que se creó el registro."
    )
    updated_at = models.DateTimeField(
        _('Última modificación'),
        auto_now=True, # Se actualiza cada vez que guardas el registro
        help_text="Fecha y hora de la última modificación."
    )
    is_active = models.BooleanField(
        _('Activo'),
        default=True,
        help_text="Indica si el registro está activo en el sistema."
    )

    class Meta:
        abstract = True # ¡Clave! Esto le dice a Django que no cree tabla para esto.

class PeriodoManager(models.Manager):
    def get_periodo_actual(self):
        """
        Devuelve el periodo semanal actual basado en la fecha de hoy.
        Si no existe, lo crea automáticamente siguiendo la regla Viernes-Jueves.
        """
        hoy = timezone.localdate()
        
        # En Python: Lunes=0, ..., Jueves=3, Viernes=4, ... Domingo=6
        # Queremos encontrar el último viernes (start_date)
        # Si hoy es Viernes (4), restamos 0 días.
        # Si hoy es Sábado (5), restamos 1 día.
        # Si hoy es Jueves (3), restamos 6 días (3 - 4 = -1 % 7 = 6).
        dias_para_atras = (hoy.weekday() - 4) % 7
        fecha_inicio = hoy - datetime.timedelta(days=dias_para_atras)
        fecha_fin = fecha_inicio + datetime.timedelta(days=6)
        
        # Generar un código único, ej: "SEM-2025-10-24" (Fecha del viernes de inicio)
        codigo = f"SEM-{fecha_inicio.strftime('%Y-%m-%d')}"
        
        periodo, created = self.get_or_create(
            codigo=codigo,
            defaults={
                'tipo': Periodo.TipoPeriodo.SEMANAL,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'cerrado': False
            }
        )
        return periodo

class Periodo(TimeStampedModel):
    # ... (Tus campos anteriores: tipo, fechas, cerrado, codigo) ...
    class TipoPeriodo(models.TextChoices):
        SEMANAL = 'SEM', _('Semanal (Vie-Jue)')
        MENSUAL = 'MEN', _('Mensual (Calendario)')

    tipo = models.CharField(max_length=3, choices=TipoPeriodo.choices, default=TipoPeriodo.SEMANAL)
    fecha_inicio = models.DateField(_('Fecha de inicio'))
    fecha_fin = models.DateField(_('Fecha de fin'))
    cerrado = models.BooleanField(_('Cerrado'), default=False)
    codigo = models.CharField(_('Código identificador'), max_length=50, unique=True)

    objects = PeriodoManager() # <--- Conectamos el cerebro aquí

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        estado = "CERRADO" if self.cerrado else "ACTIVO"
        return f"{self.codigo} ({self.fecha_inicio} al {self.fecha_fin}) [{estado}]"