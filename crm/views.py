from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q 
from django.utils import timezone
from datetime import date
from empresas.models import Empresa
from .models import Expediente, RegistroPago
from .forms import ExpedienteForm

# --- HELPER PARA CALCULAR DEUDA ---
def calcular_deuda_actualizada(expediente):
    """
    Calcula la deuda exigible basándose en la fecha de impago y la fecha actual.
    Logica: (Cuotas Vencidas * Valor Cuota) - Lo que ya pagó
    """
    # Validaciones básicas para evitar división por cero
    if not expediente.fecha_impago or expediente.monto_original <= 0 or expediente.cuotas_totales <= 0:
        return expediente.monto_original

    hoy = timezone.now().date()
    impago = expediente.fecha_impago

    # Si la fecha de impago es futura, la deuda exigible hoy es 0
    if impago > hoy:
        return 0

    # 1. Calcular valor de la cuota
    # Convertimos a float para cálculos matemáticos
    valor_cuota = float(expediente.monto_original) / expediente.cuotas_totales

    # 2. Calcular cuántas cuotas han vencido desde la fecha de impago (inclusive)
    # Diferencia de meses base (Año * 12 + Meses)
    meses_diferencia = (hoy.year - impago.year) * 12 + (hoy.month - impago.month)
    
    # Si el día de hoy es igual o mayor al día del impago, suma el mes actual
    # Ej: Impago el 1, hoy es 9 -> Ya venció este mes
    if hoy.day >= impago.day:
        meses_diferencia += 1
    
    # Ajuste: al menos 1 cuota (la del primer impago)
    cuotas_vencidas = max(1, meses_diferencia)
    
    # No podemos cobrar más cuotas de las totales del plan
    cuotas_vencidas = min(cuotas_vencidas, expediente.cuotas_totales)

    # 3. Calculamos la deuda teórica acumulada
    deuda_teorica = valor_cuota * cuotas_vencidas

    # 4. Restamos lo que ya haya recuperado (si hubo pagos parciales)
    deuda_real = deuda_teorica - float(expediente.monto_recuperado)

    # La deuda no puede ser negativa
    return max(0.0, deuda_real)

# --- VISTAS ---

@login_required
def dashboard_crm(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    expedientes_qs = Expediente.objects.filter(empresa=empresa)
    
    # --- ACTUALIZACIÓN AUTOMÁTICA DE DEUDA ---
    # Al entrar al dashboard, recalculamos la deuda de los activos
    # para asegurar que si cambió de mes, la deuda suba sola.
    for exp in expedientes_qs.filter(activo=True, estado='ACTIVO'):
        try:
            nueva_deuda = calcular_deuda_actualizada(exp)
            # Solo guardamos si hay una diferencia real (evitamos guardados innecesarios)
            if abs(float(exp.monto_actual) - nueva_deuda) > 0.01: 
                exp.monto_actual = nueva_deuda
                exp.save()
        except Exception:
            continue # Si falla un cálculo, seguimos con el siguiente

    # --- PROCESAR FORMULARIO DE ALTA ---
    if request.method == 'POST':
        form = ExpedienteForm(request.POST, empresa=empresa)
        if form.is_valid():
            # 1. Validación de Duplicados
            nombre = form.cleaned_data.get('deudor_nombre')
            telefono = form.cleaned_data.get('deudor_telefono')
            
            duplicado = expedientes_qs.filter(
                Q(deudor_nombre__iexact=nombre) | Q(deudor_telefono=telefono)
            ).exists()

            if duplicado:
                messages.error(request, f"Ya existe un expediente para {nombre} o el teléfono {telefono}.")
                return redirect('crm:dashboard_crm', empresa_id=empresa.id)

            # 2. Preparar objeto
            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa
            
            # 3. Generar ID Único (Ej: EMP-00001)
            count = expedientes_qs.count() + 1
            prefix = empresa.nombre[:3].upper()
            nuevo_exp.numero_expediente = f"{prefix}-{count:05d}"
            
            # 4. Inicializar Valores
            nuevo_exp.monto_recuperado = 0
            nuevo_exp.estado = 'ACTIVO'
            nuevo_exp.activo = True
            
            # 5. CALCULAR DEUDA INICIAL
            # Calculamos cuánto debe HOY basado en la fecha de impago que cargaste
            deuda_inicial = calcular_deuda_actualizada(nuevo_exp)
            nuevo_exp.monto_actual = deuda_inicial
            
            nuevo_exp.save()
            
            messages.success(request, f"Expediente registrado. Deuda al día: {nuevo_exp.monto_actual:.2f}€")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
        else:
            messages.error(request, "Error en el formulario. Verifique los datos.")
    else:
        form = ExpedienteForm(empresa=empresa)

    # --- CONTEXTO ---
    context = {
        'empresa': empresa,
        'form': form,
        'impagos': expedientes_qs.filter(activo=True, estado='ACTIVO'),
        'cedidos': expedientes_qs.filter(activo=True, estado='CEDIDO'),
        'pagados': expedientes_qs.filter(activo=True, estado='PAGADO'),
        'recobros': RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago'),
        'papelera': expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion'),
    }
    return render(request, 'crm/dashboard_empresa.html', context)

# --- VISTAS DE ACCIÓN ---

@login_required
def eliminar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    exp.eliminar_logico()
    messages.warning(request, f"Expediente de {exp.deudor_nombre} movido a la papelera.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

@login_required
def restaurar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    exp.restaurar()
    messages.success(request, f"Expediente de {exp.deudor_nombre} restaurado.")
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)

@login_required
def eliminar_permanente_expediente(request, exp_id):
    """Elimina el registro FÍSICAMENTE de la base de datos"""
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    nombre = exp.deudor_nombre
    exp.delete()
    messages.success(request, f"El expediente de {nombre} ha sido eliminado definitivamente.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

@login_required
def lista_crm(request):
    """Vista para el listado general de empresas en el CRM"""
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})