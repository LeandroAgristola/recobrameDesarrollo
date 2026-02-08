from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Expediente, RegistroPago
from .forms import ExpedienteForm

# Vista principal actualizada con el formulario
def dashboard_crm(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    expedientes_qs = Expediente.objects.filter(empresa=empresa)
    
    if request.method == 'POST':
        form = ExpedienteForm(request.POST)
        if form.is_valid():
            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa
            nuevo_exp.monto_actual = nuevo_exp.monto_original # Inicializamos deuda
            nuevo_exp.save()
            messages.success(request, "Cliente registrado correctamente.")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
    else:
        form = ExpedienteForm()

    context = {
        'empresa': empresa,
        'form': form,
        'impagos': expedientes_qs.filter(activo=True, monto_actual__gt=0).exclude(estado='CEDIDO'),
        'cedidos': expedientes_qs.filter(activo=True, estado='CEDIDO'),
        'pagados': expedientes_qs.filter(activo=True, monto_actual__lte=0),
        'papelera': expedientes_qs.filter(activo=False),
    }
    return render(request, 'crm/dashboard_empresa.html', context)

# Funcionalidad Papelera
def eliminar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    exp.eliminar_logico()
    messages.warning(request, f"Expediente de {exp.deudor_nombre} movido a la papelera.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

def restaurar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    exp.restaurar()
    messages.success(request, f"Expediente de {exp.deudor_nombre} restaurado.")
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)