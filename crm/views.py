from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from empresas.models import Empresa
from .models import Expediente, RegistroPago
from .forms import ExpedienteForm

# 1. LISTADO GENERAL (El que faltaba y causaba el error)
def lista_crm(request):
    """Vista para el listado general de empresas en el CRM"""
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})

# 2. DASHBOARD OPERATIVO
def dashboard_crm(request, empresa_id):
    """Dashboard principal de una empresa con todas sus pestañas y formulario de alta"""
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    expedientes_qs = Expediente.objects.filter(empresa=empresa)
    
    # Manejo del Formulario de Nuevo Registro (Modal)
    if request.method == 'POST':
        form = ExpedienteForm(request.POST)
        if form.is_valid():
            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa
            nuevo_exp.monto_actual = nuevo_exp.monto_original
            nuevo_exp.save()
            messages.success(request, f"Cliente {nuevo_exp.deudor_nombre} registrado correctamente.")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
    else:
        form = ExpedienteForm()

    # Contexto unificado para los includes del dashboard
    context = {
        'empresa': empresa,
        'form': form,
        'impagos': expedientes_qs.filter(activo=True, monto_actual__gt=0).exclude(estado='CEDIDO'),
        'cedidos': expedientes_qs.filter(activo=True, estado='CEDIDO'),
        'pagados': expedientes_qs.filter(activo=True, monto_actual__lte=0), # <--- Esta variable
        'recobros': RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago'), # <--- Y esta
        'papelera': expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion'),
    }
    return render(request, 'crm/dashboard_empresa.html', context)

# 3. ACCIONES DE EXPEDIENTE
def eliminar_expediente(request, exp_id):
    """Mueve un expediente a la papelera (activo=False)"""
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    exp.eliminar_logico()
    messages.warning(request, f"Expediente de {exp.deudor_nombre} movido a la papelera.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

def restaurar_expediente(request, exp_id):
    """Restaura un expediente de la papelera (activo=True)"""
    exp = get_object_or_404(Expediente, id=exp_id)
    exp.restaurar()
    messages.success(request, f"Expediente de {exp.deudor_nombre} restaurado.")
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)