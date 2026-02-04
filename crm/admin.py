from django.contrib import admin
from .models import Expediente, RegistroPago, CRMConfig

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('numero_expediente', 'deudor_nombre', 'monto_actual', 'estado', 'causa_impago', 'agente')
    list_filter = ('estado', 'causa_impago', 'empresa')
    search_fields = ('deudor_nombre', 'numero_expediente', 'deudor_dni')
    readonly_fields = ('fecha_recepcion',)

admin.site.register(RegistroPago)
admin.site.register(CRMConfig)