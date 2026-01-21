from django.contrib import admin
from .models import Periodo

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    # Qué columnas mostrar en la lista
    list_display = ('codigo', 'tipo', 'fecha_inicio', 'fecha_fin', 'cerrado', 'is_active')
    
    # Filtros laterales
    list_filter = ('tipo', 'cerrado', 'is_active')
    
    # Buscador
    search_fields = ('codigo',)
    
    # Ordenar por fecha (descendente) está en el modelo, pero aquí podemos forzar otro si queremos