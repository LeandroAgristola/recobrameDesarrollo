from django.contrib import admin
from .models import Empresa, TramoComision

# Esto permite agregar tramos de comisión dentro de la misma pantalla de la Empresa
class TramoInline(admin.TabularInline):
    model = TramoComision
    extra = 1

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_comision', 'porcentaje_unico', 'cif_nif', 'is_active')
    list_filter = ('tipo_comision', 'is_active')
    search_fields = ('nombre', 'razon_social')
    
    # Aquí definimos que los Tramos aparezcan dentro de la ficha
    inlines = [TramoInline]
    
    # Organizar los campos visualmente en el admin para que se vea ordenado
    fieldsets = (
        ('Datos Identificativos', {
            'fields': ('nombre', 'razon_social', 'cif_nif')
        }),
        ('Datos Operativos', {
            'fields': ('contacto_incidencias', 'email_incidencias', 'datos_bancarios')
        }),
        ('Documentación Legal', {
            'fields': ('contrato_colaboracion', 'contrato_cesion'),
            'description': 'Subir aquí los contratos firmados.'
        }),
        ('Configuración Económica', {
            'fields': ('tipo_comision', 'porcentaje_unico'),
            'description': 'Si seleccionas "Por Tramos", configura la tabla inferior. Si es "Fijo", usa el campo % Único.'
        }),
    )