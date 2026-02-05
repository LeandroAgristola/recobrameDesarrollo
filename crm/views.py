from django.shortcuts import render, get_object_or_404
from empresas.models import Empresa
from .models import Expediente, RegistroPago

from django.shortcuts import render, get_object_or_404
from empresas.models import Empresa
from .models import Expediente, RegistroPago

def dashboard_crm(request, empresa_id):
    # Usamos is_active para ser coherentes con el modelo Empresa
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    
    # Filtramos los datos para que cada pestaña reciba lo que le corresponde
    # Impagos: Activos, con monto > 0 y que NO estén cedidos
    impagos = Expediente.objects.filter(empresa=empresa, activo=True, monto_actual__gt=0).exclude(estado='CEDIDO')
    
    # Cedidos: Activos con estado CEDIDO
    cedidos = Expediente.objects.filter(empresa=empresa, activo=True, estado='CEDIDO')
    
    # Ha Pagado: Activos con monto 0 o menor
    pagados = Expediente.objects.filter(empresa=empresa, activo=True, monto_actual__lte=0)
    
    # REG_Recobros: Todos los pagos de la empresa
    recobros = RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago')

    context = {
        'empresa': empresa,
        'impagos': impagos,
        'cedidos': cedidos,
        'pagados': pagados,
        'recobros': recobros,
    }
    
    return render(request, 'crm/dashboard_empresa.html', context)

def lista_crm(request):
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})

