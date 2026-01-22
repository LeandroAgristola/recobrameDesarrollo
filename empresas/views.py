from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Empresa
from .forms import EmpresaForm

@login_required
def lista_empresas(request):
    """
    Lista de empresas con filtros y buscador.
    Separa activas e inactivas.
    """
    busqueda = request.GET.get('busqueda')
    
    # Base QuerySets
    empresas_activas = Empresa.objects.filter(is_active=True)
    empresas_inactivas = Empresa.objects.filter(is_active=False)

    # Filtro Buscador
    if busqueda:
        criterio = Q(nombre__icontains=busqueda) | \
                   Q(razon_social__icontains=busqueda) | \
                   Q(cif_nif__icontains=busqueda)
        empresas_activas = empresas_activas.filter(criterio)
        empresas_inactivas = empresas_inactivas.filter(criterio)

    return render(request, 'empresas/lista_empresas.html', {
        'empresas_activas': empresas_activas,
        'empresas_inactivas': empresas_inactivas,
        'filtros': {'busqueda': busqueda or ''}
    })

@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f"Empresa {empresa.nombre} creada correctamente.")
            return redirect('empresas:lista_empresas')
        else:
            messages.error(request, "Error en el formulario. Verifique los datos.")
    else:
        form = EmpresaForm()

    return render(request, 'empresas/form_empresa.html', {
        'form': form,
        'titulo': 'Nueva Empresa'
    })

@login_required
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos actualizados correctamente.")
            return redirect('empresas:lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'empresas/form_empresa.html', {
        'form': form,
        'titulo': f'Editar {empresa.nombre}',
        'editando': True
    })

@login_required
def desactivar_empresa(request, empresa_id):
    """Baja lógica (Soft Delete)"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.is_active = False
        empresa.fecha_baja = timezone.now().date()
        empresa.save()
        messages.warning(request, f"Empresa {empresa.nombre} desactivada.")
    return redirect('empresas:lista_empresas')

@login_required
def reactivar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.is_active = True
        empresa.fecha_baja = None
        empresa.save()
        messages.success(request, f"Empresa {empresa.nombre} reactivada.")
    return redirect('empresas:lista_empresas')

@login_required
def detalle_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    return render(request, 'empresas/detalle_empresa.html', {'empresa': empresa})