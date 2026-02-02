from django.shortcuts import render, get_object_or_404
from empresas.models import Empresa
from .models import Expediente, RegistroPago

def dashboard_crm(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    
    # Filtramos los datos para cada pestaña
    expedientes_empresa = Expediente.objects.filter(empresa=empresa, activo=True)
    
    context = {
        'empresa': empresa,
        'impagos': expedientes_empresa.filter(monto_actual__gt=0),
        'pagados': expedientes_empresa.filter(monto_actual=0),
        'reg_recobro': RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago'),
        'papelera': Expediente.objects.filter(empresa=empresa, activo=False),
    }
    
    return render(request, 'crm/dashboard_empresa.html', context)

def lista_crm(request):
    # Cambiamos 'activo=True' por 'is_active=True'
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})