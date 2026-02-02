from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Empresa
from .forms import EmpresaForm, EsquemaComisionForm, TramoFormSet
from django.core.paginator import Paginator
from .models import Empresa, EsquemaComision, TramoComision
from .forms import EmpresaForm, EsquemaComisionForm, TramoFormSet
from .models import OPCIONES_IMPAGOS

# === HELPER PARA BÚSQUEDA (Para no repetir código en ambas vistas) ===
def aplicar_busqueda(queryset, busqueda):
    if busqueda:
        return queryset.filter(
            Q(nombre__icontains=busqueda) | 
            Q(razon_social__icontains=busqueda) | 
            Q(cif_nif__icontains=busqueda)
        )
    return queryset

@login_required
def lista_empresas(request):
    """
    PESTAÑA 1: Empresas Activas
    """
    busqueda = request.GET.get('busqueda', '')
    
    # Solo Activas
    empresas_list = Empresa.objects.filter(is_active=True).order_by('-fecha_alta')
    empresas_list = aplicar_busqueda(empresas_list, busqueda)

    # Paginación
    paginator = Paginator(empresas_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'empresas/lista_empresas.html', {
        'page_obj': page_obj,
        'filtros': {'busqueda': busqueda},
        'active_tab': 'activas' # Variable clave para la pestaña
    })

def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f"Empresa creada. Configuremos las comisiones.")
            # REDIRECCIÓN CLAVE: Al paso 2 (Configuración)
            return redirect('empresas:configurar_comisiones', empresa_id=empresa.id)
    else:
        form = EmpresaForm()
    
    return render(request, 'empresas/form_empresa.html', {'form': form})

        
@login_required
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        # Ya no usamos formsets aquí, solo el formulario principal
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de la empresa actualizados correctamente.")
            return redirect('empresas:detalle_empresa', empresa_id=empresa.id)
    else:
        form = EmpresaForm(instance=empresa)
    
    # Reutilizamos el template form_empresa.html que ya arreglamos
    return render(request, 'empresas/form_empresa.html', {
        'form': form, 
        'titulo': f'Editar {empresa.nombre}'
    })

@login_required
def papelera_empresas(request):
    """
    PESTAÑA 2: Papelera (Empresas desactivadas)
    """
    busqueda = request.GET.get('busqueda', '')
    
    empresas_list = Empresa.objects.filter(is_active=False).order_by('-fecha_baja')
    empresas_list = aplicar_busqueda(empresas_list, busqueda)

    paginator = Paginator(empresas_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'empresas/papelera_empresas.html', {
        'page_obj': page_obj,
        'filtros': {'busqueda': busqueda},
        'active_tab': 'papelera'
    })

@login_required
def desactivar_empresa(request, empresa_id):
    """Baja lógica (Mover a Papelera)"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.is_active = False
        empresa.fecha_baja = timezone.now().date()
        empresa.save()
        messages.warning(request, f"Empresa '{empresa.nombre}' movida a la papelera.")
    return redirect('empresas:lista_empresas')

@login_required
def reactivar_empresa(request, empresa_id):
    """Recuperar de Papelera"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.is_active = True
        empresa.fecha_baja = None # Limpiamos fecha baja, MANTENEMOS fecha alta original
        empresa.save()
        messages.success(request, f"Empresa '{empresa.nombre}' reactivada correctamente.")
    
    return redirect('empresas:papelera_empresas')

@login_required
def eliminar_empresa(request, empresa_id):
    """Eliminación Física (Definitiva)"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    nombre = empresa.nombre
    
    empresa.delete()
    
    messages.error(request, f"La empresa '{nombre}' ha sido eliminada definitivamente.")
    return redirect('empresas:papelera_empresas')

@login_required
def detalle_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    
    esquemas = empresa.esquemas.all().prefetch_related('tramos').order_by('tipo_caso', 'tipo_producto')
    
    # Procesamos la lista de impagos para mostrar las etiquetas (Badges)
    lista_impagos = []
    if empresa.tipos_impagos:
        # Convertimos "SEQURA, STRIPE" -> ['SEQURA', 'STRIPE']
        raw_list = empresa.tipos_impagos.split(',')
        lista_impagos = [item.strip() for item in raw_list if item.strip()]

    return render(request, 'empresas/detalle_empresa.html', {
        'empresa': empresa,
        'esquemas': esquemas,
        'lista_impagos': lista_impagos,
    })

@login_required
def configurar_comisiones(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    esquemas = empresa.esquemas.all().order_by('tipo_caso', 'tipo_producto')
    
    seleccionados = [c.strip() for c in empresa.tipos_impagos.split(',') if c.strip()]
    configurados = empresa.esquemas.filter(tipo_caso='IMPAGO').values_list('tipo_producto', flat=True)
    faltantes = []
    nombres_dict = dict(OPCIONES_IMPAGOS)
    
    for codigo in seleccionados:
        if codigo not in configurados:
            faltantes.append(nombres_dict.get(codigo, codigo))

    if request.method == 'POST':
        form = EsquemaComisionForm(request.POST, empresa=empresa)
        tramo_formset = TramoFormSet(request.POST)
        
        if form.is_valid():
            esquema = form.save(commit=False)
            esquema.empresa = empresa
            esquema.save()

            if esquema.modalidad == 'TRAMOS':
                tramo_formset = TramoFormSet(request.POST, instance=esquema)
                if tramo_formset.is_valid():
                    tramo_formset.save()
            
            messages.success(request, "Regla guardada correctamente.")
            return redirect('empresas:configurar_comisiones', empresa_id=empresa.id)
    else:
        form = EsquemaComisionForm(empresa=empresa)
        tramo_formset = TramoFormSet()

    return render(request, 'empresas/configurar_comisiones.html', {
        'empresa': empresa,
        'esquemas': esquemas,
        'form': form,
        'tramo_formset': tramo_formset,
        'faltantes': faltantes,
    })

@login_required
def editar_esquema(request, esquema_id):
    esquema = get_object_or_404(EsquemaComision, id=esquema_id)
    
    if request.method == 'POST':
        form = EsquemaComisionForm(request.POST, instance=esquema, empresa=esquema.empresa)
        tramo_formset = TramoFormSet(request.POST, instance=esquema)
        
        if form.is_valid():
            # Guardamos el esquema
            obj = form.save()
            
            # Si cambió a TRAMOS, validamos y guardamos el formset
            if obj.modalidad == 'TRAMOS':
                if tramo_formset.is_valid():
                    tramo_formset.save()
                    messages.success(request, "Esquema actualizado correctamente.")
                    return redirect('empresas:configurar_comisiones', empresa_id=esquema.empresa.id)
            else:
                # Si cambió a FIJO, podríamos querer borrar los tramos viejos
                esquema.tramos.all().delete()
                messages.success(request, "Esquema actualizado a Fijo.")
                return redirect('empresas:configurar_comisiones', empresa_id=esquema.empresa.id)
    else:
        form = EsquemaComisionForm(instance=esquema, empresa=esquema.empresa)
        tramo_formset = TramoFormSet(instance=esquema)
    
    return render(request, 'empresas/form_esquema.html', {
        'form': form,
        'tramo_formset': tramo_formset,
        'esquema': esquema,
        'titulo': f"Editar Regla: {esquema}"
    })

@login_required
def eliminar_esquema(request, esquema_id):
    esquema = get_object_or_404(EsquemaComision, id=esquema_id)
    empresa_id = esquema.empresa.id
    esquema.delete()
    messages.warning(request, "Esquema de comisión eliminado.")
    return redirect('empresas:configurar_comisiones', empresa_id=empresa_id)