from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Empresa
from .forms import EmpresaForm, TramoComisionFormSet
from django.core.paginator import Paginator

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

@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        formset = TramoComisionFormSet(request.POST)
        
        if form.is_valid():
            # VALIDACIÓN EXTRA: Si eligió Tramos, verificar que el formset tenga datos válidos
            tipo_comision = form.cleaned_data.get('tipo_comision')
            tramos_validos = 0
            
            # Contamos cuántos formularios del formset tienen datos y no están marcados para borrar
            if formset.is_valid():
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE'):
                        tramos_validos += 1
            
            if tipo_comision == 'TRAMOS' and tramos_validos == 0:
                messages.error(request, "Si selecciona Comisión por Tramos, debe agregar al menos una fila en la tabla.")
            elif formset.is_valid():
                # Si pasa todas las validaciones
                empresa = form.save()
                formset.instance = empresa
                formset.save()
                messages.success(request, f"Empresa {empresa.nombre} creada correctamente.")
                return redirect('empresas:lista_empresas')
            else:
                 messages.error(request, "Error en la tabla de tramos.")
        else:
            messages.error(request, "Error en el formulario principal. Revise los campos obligatorios.")
    else:
        form = EmpresaForm()
        formset = TramoComisionFormSet()

    return render(request, 'empresas/form_empresa.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva Empresa'
    })

@login_required
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        formset = TramoComisionFormSet(request.POST, instance=empresa)
        
        if form.is_valid():
            # MISMA VALIDACIÓN EXTRA
            tipo_comision = form.cleaned_data.get('tipo_comision')
            tramos_validos = 0
            if formset.is_valid():
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE'):
                        tramos_validos += 1
            
            if tipo_comision == 'TRAMOS' and tramos_validos == 0:
                messages.error(request, "Debe configurar al menos un tramo o cambiar a Comisión Fija.")
            elif formset.is_valid():
                form.save()
                formset.save()
                messages.success(request, "Datos actualizados correctamente.")
                return redirect('empresas:lista_empresas')
            else:
                messages.error(request, "Error en los tramos.")
        else:
             messages.error(request, "Verifique los errores en el formulario.")
    else:
        form = EmpresaForm(instance=empresa)
        formset = TramoComisionFormSet(instance=empresa)

    return render(request, 'empresas/form_empresa.html', {
        'form': form,
        'formset': formset,
        'titulo': f'Editar {empresa.nombre}',
        'editando': True
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
    return render(request, 'empresas/detalle_empresa.html', {'empresa': empresa})