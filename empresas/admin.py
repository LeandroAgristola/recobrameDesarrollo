from django.contrib import admin
from .models import Empresa, EsquemaComision, TramoComision

# 1. Configuración de Tramos (Se verán dentro del Esquema)
class TramoInline(admin.TabularInline):
    model = TramoComision
    extra = 1

# 2. Configuración de Esquemas (Se verán dentro de la Empresa)
class EsquemaComisionInline(admin.StackedInline):
    model = EsquemaComision
    extra = 0
    show_change_link = True
    inlines = [TramoInline] # Nota: Django nativo no soporta inlines anidados fácilmente, 
                            # pero dejamos el link para editarlo aparte.

# 3. Admin Principal de EMPRESA
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Quitamos 'tipo_comision' y 'porcentaje_unico' que ya no existen
    list_display = ('nombre', 'razon_social', 'cif_nif', 'fecha_alta', 'is_active')
    
    # Quitamos el filtro viejo
    list_filter = ('is_active',)
    
    search_fields = ('nombre', 'razon_social', 'cif_nif', 'email_contacto')
    
    # Agregamos los esquemas como inline para verlos aquí
    inlines = [EsquemaComisionInline]

# 4. Admin de ESQUEMAS (Para poder editarlos con sus tramos)
@admin.register(EsquemaComision)
class EsquemaComisionAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'tipo_caso', 'tipo_producto', 'modalidad')
    list_filter = ('tipo_caso', 'modalidad')
    search_fields = ('empresa__nombre',)
    
    # Aquí sí podemos meter los tramos
    inlines = [TramoInline]