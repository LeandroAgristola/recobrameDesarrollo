from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q 
from django.utils import timezone
from datetime import date
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST    
from django.http import JsonResponse
import json
from django.contrib.auth.models import User

from empresas.models import Empresa
from .models import Expediente, RegistroPago, DocumentoExpediente
from .forms import ExpedienteForm

# --- HELPER PARA CALCULAR DEUDA (LÓGICA ORIGINAL RESTAURADA) ---
def calcular_deuda_actualizada(expediente):
    """
    Calcula la deuda exigible basándose en la fecha de impago y la fecha actual.
    Logica: (Cuotas Vencidas * Valor Cuota) - Lo que ya pagó
    """
    # Validaciones básicas para evitar división por cero
    if not expediente.fecha_impago or not expediente.monto_original or not expediente.cuotas_totales:
        return 0
    
    if expediente.monto_original <= 0 or expediente.cuotas_totales <= 0:
        return float(expediente.monto_original)

    hoy = timezone.now().date()
    impago = expediente.fecha_impago

    # Si la fecha de impago es futura, la deuda exigible hoy es 0
    if impago > hoy:
        return 0

    # 1. Calcular valor de la cuota
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
    recuperado = float(expediente.monto_recuperado) if expediente.monto_recuperado else 0.0
    deuda_real = deuda_teorica - recuperado

    # La deuda no puede ser negativa
    return max(0.0, deuda_real)


# --- BÚSQUEDA AJAX PARA AUTOCOMPLETADO ---
@login_required
def buscar_antecedentes_deudor(request):
    try:
        nombre = request.GET.get('nombre', '').strip()
        empresa_id = request.GET.get('empresa_id')
        if not nombre or not empresa_id:
            return JsonResponse({'status': 'empty'})

        antecedente = Expediente.objects.filter(
            empresa_id=empresa_id,
            deudor_nombre__iexact=nombre
        ).order_by('-fecha_creacion').first()

        if antecedente:
            data = {
                'status': 'success',
                'datos': {
                    'telefono': antecedente.deudor_telefono or '',
                    'email': antecedente.deudor_email or '',
                    'dni': antecedente.deudor_dni or '',
                }
            }
        else:
            data = {'status': 'not_found'}

        return JsonResponse(data)
    except Exception as e:
        print(f"Error en buscar_antecedentes: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# --- VISTA PRINCIPAL (DASHBOARD) ---
@login_required
def dashboard_crm(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    expedientes_qs = Expediente.objects.filter(empresa=empresa)
    
    # --- ACTUALIZACIÓN AUTOMÁTICA DE DEUDA (RESTAURADO) ---
    # Al entrar al dashboard, recalculamos la deuda de los activos
    for exp in expedientes_qs.filter(activo=True, estado='ACTIVO'):
        try:
            nueva_deuda = calcular_deuda_actualizada(exp)
            # Solo guardamos si hay una diferencia real > 0.01
            if exp.monto_actual is None or abs(float(exp.monto_actual) - nueva_deuda) > 0.01: 
                exp.monto_actual = nueva_deuda
                exp.save()
        except Exception:
            continue 

    # ---------------------------------------------------------
    # 1. PROCESAMIENTO DEL FORMULARIO DE ALTA (POST)
    # ---------------------------------------------------------
    if request.method == 'POST' and 'nuevo_expediente' in request.POST:
        form = ExpedienteForm(request.POST, empresa=empresa) 
        if form.is_valid():
            # Validación de duplicados básica
            nombre = form.cleaned_data.get('deudor_nombre')
            telefono = form.cleaned_data.get('deudor_telefono')
            duplicado = expedientes_qs.filter(
                Q(deudor_nombre__iexact=nombre) | Q(deudor_telefono=telefono)
            ).exists()
            
            if duplicado:
                messages.warning(request, f"Atención: Ya existe un expediente para {nombre} o el teléfono {telefono}.")
                # No bloqueamos, pero avisamos. Si quieres bloquear, usa return redirect aquí.

            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa 
            
            # --- ID PERSONALIZADO (Ej: PEP-00001) ---
            prefix = empresa.nombre[:3].upper()
            count = expedientes_qs.count() + 1
            nuevo_exp.numero_expediente = f"{prefix}-{count:06d}"

            # --- CALCULAR DEUDA INICIAL ---
            try:
                nuevo_exp.monto_actual = calcular_deuda_actualizada(nuevo_exp)
            except Exception:
                nuevo_exp.monto_actual = nuevo_exp.monto_original

            # Inicializar valores por defecto
            nuevo_exp.monto_recuperado = 0
            nuevo_exp.estado = 'ACTIVO'
            nuevo_exp.activo = True
            
            nuevo_exp.save()
            
            messages.success(request, f"Expediente {nuevo_exp.numero_expediente} registrado. Deuda al día: {nuevo_exp.monto_actual}€")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
        else:
            messages.error(request, "Error al crear expediente. Revisa los campos.")
            print("Errores del formulario:", form.errors)
    else:
        form = ExpedienteForm(empresa=empresa)

    # ---------------------------------------------------------
    # 2. FILTROS Y BÚSQUEDA (GET)
    # ---------------------------------------------------------
    
    q = request.GET.get('q', '')
    
    # Filtros Básicos
    f_agente = request.GET.get('f_agente')
    f_nombre = request.GET.get('f_nombre')
    f_tel = request.GET.get('f_tel')
    f_tipo = request.GET.get('f_tipo')
    f_monto = request.GET.get('f_monto')
    f_cuotas = request.GET.get('f_cuotas')
    f_fecha_compra = request.GET.get('f_fecha_compra')
    f_fecha_impago = request.GET.get('f_fecha_impago')
    f_dias = request.GET.get('f_dias')
    f_estado = request.GET.get('f_estado')
    f_deuda = request.GET.get('f_deuda')

    # Filtros Booleanos
    f_be = request.GET.get('f_be')
    f_br = request.GET.get('f_br')
    f_as = request.GET.get('f_as')
    f_ls = request.GET.get('f_ls')

    # Búsqueda General
    if q:
        expedientes_qs = expedientes_qs.filter(
            Q(deudor_nombre__icontains=q) | 
            Q(deudor_telefono__icontains=q) | 
            Q(numero_expediente__icontains=q) |
            Q(deudor_dni__icontains=q)
        )

    # Aplicación de Filtros
    if f_agente: expedientes_qs = expedientes_qs.filter(agente_id=f_agente)
    if f_nombre: expedientes_qs = expedientes_qs.filter(deudor_nombre__icontains=f_nombre)
    if f_tel: expedientes_qs = expedientes_qs.filter(deudor_telefono__icontains=f_tel)
    if f_tipo: expedientes_qs = expedientes_qs.filter(tipo_producto__icontains=f_tipo)
    if f_monto: expedientes_qs = expedientes_qs.filter(monto_original__icontains=f_monto)
    if f_cuotas: expedientes_qs = expedientes_qs.filter(cuotas_totales=f_cuotas)
    if f_fecha_compra: expedientes_qs = expedientes_qs.filter(fecha_compra=f_fecha_compra)
    if f_fecha_impago: expedientes_qs = expedientes_qs.filter(fecha_impago=f_fecha_impago)
    
    if f_dias:
        try:
            dias = int(f_dias)
            fecha_limite = timezone.now().date() - timezone.timedelta(days=dias)
            expedientes_qs = expedientes_qs.filter(fecha_impago__lte=fecha_limite)
        except ValueError:
            pass

    if f_estado: expedientes_qs = expedientes_qs.filter(causa_impago=f_estado)
    if f_deuda: expedientes_qs = expedientes_qs.filter(monto_actual__icontains=f_deuda)

    # Filtros Dinámicos de Ticks
    for i in range(1, 6):
        val_w = request.GET.get(f'f_w{i}')
        if val_w in ['true', 'false']:
            expedientes_qs = expedientes_qs.filter(**{f'w{i}': (val_w == 'true')})

        val_l = request.GET.get(f'f_l{i}')
        if val_l in ['true', 'false']:
            expedientes_qs = expedientes_qs.filter(**{f'll{i}': (val_l == 'true')})

    # Filtros Booleanos ASNEF
    if f_be in ['true', 'false']: expedientes_qs = expedientes_qs.filter(buro_enviado=(f_be == 'true'))
    if f_br in ['true', 'false']: expedientes_qs = expedientes_qs.filter(buro_recibido=(f_br == 'true'))
    if f_as in ['true', 'false']: expedientes_qs = expedientes_qs.filter(asnef_inscrito=(f_as == 'true'))
    if f_ls in ['true', 'false']: expedientes_qs = expedientes_qs.filter(llamada_seguimiento_asnef=(f_ls == 'true'))

    context = {
        'empresa': empresa,
        'q': q,
        'impagos': expedientes_qs.filter(activo=True, estado='ACTIVO'),
        'cedidos': expedientes_qs.filter(activo=True, estado='CEDIDO'),
        'pagados': expedientes_qs.filter(activo=True, estado='PAGADO'),
        'recobros': RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago'),
        'papelera': expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion'),
        'agentes_disponibles': User.objects.filter(is_active=True).order_by('username'),
        'form': form, 
    }
    return render(request, 'crm/dashboard_empresa.html', context)


# --- VISTAS DE ACCIÓN ---
@login_required
def eliminar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    if request.method == 'POST':
        motivo = request.POST.get('motivo_eliminacion')
        exp.eliminar_logico(motivo)
        messages.warning(request, f"Expediente movido a la papelera.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

@login_required
def restaurar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    exp.restaurar()
    messages.success(request, f"Expediente de {exp.deudor_nombre} restaurado.")
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)

@login_required
def eliminar_permanente_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    if request.method == 'POST':
        nombre = exp.deudor_nombre
        exp.delete()
        messages.success(request, f"El expediente de {nombre} ha sido eliminado definitivamente.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

@login_required
def lista_crm(request):
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})


# --- API / JSON ENDPOINTS ---
@login_required
@require_POST
def actualizar_seguimiento(request):
    data = json.loads(request.body)
    exp_id = data.get('expediente_id')
    accion = data.get('tipo_accion') 
    valor = data.get('valor')        
    nuevo_estado = data.get('nuevo_estado')
    fecha_promesa = data.get('fecha_promesa')

    exp = get_object_or_404(Expediente, id=exp_id)
    
    if valor:
        setattr(exp, accion, True)
        setattr(exp, f'fecha_{accion}', timezone.now())
        if nuevo_estado:
            exp.causa_impago = nuevo_estado
            if hasattr(exp, f'estado_{accion}'):
                setattr(exp, f'estado_{accion}', nuevo_estado)
            if nuevo_estado == 'PAGARA' and fecha_promesa:
                exp.fecha_pago_promesa = fecha_promesa
    else:
        setattr(exp, accion, False)
        setattr(exp, f'fecha_{accion}', None)
        if hasattr(exp, f'estado_{accion}'):
            setattr(exp, f'estado_{accion}', None)
            
    # RECALCULAR DEUDA AL ACTUALIZAR (Opcional, pero recomendado si pasa el tiempo)
    # exp.monto_actual = calcular_deuda_actualizada(exp) # Descomentar si quieres actualización en tiempo real al tocar ticks

    exp.save()
    exp.refresh_from_db()

    estado_tick_legible = None
    field_name = f'estado_{accion}'
    display_method = f'get_{field_name}_display'
    if hasattr(exp, display_method):
        try:
            estado_tick_legible = getattr(exp, display_method)()
        except Exception:
            estado_tick_legible = None

    return JsonResponse({
            'status': 'ok',
            'fecha_ultimo': exp.ultimo_mensaje_fecha.strftime("%d/%m/%Y") if exp.ultimo_mensaje_fecha else "-",
            'estado_legible': exp.get_causa_impago_display() or "-",
            'estado_tick_legible': estado_tick_legible or "-",
            'fecha_promesa_legible': exp.fecha_pago_promesa.strftime("%d/%m") if exp.fecha_pago_promesa else "-"
        })

@login_required
@require_POST
def actualizar_comentario_estandar(request):
    data = json.loads(request.body)
    exp = get_object_or_404(Expediente, id=data.get('expediente_id'))
    exp.comentario_estandar = data.get('comentario')
    exp.save()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def actualizar_agente(request):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'msg': 'No autorizado'}, status=403)

    data = json.loads(request.body)
    exp = get_object_or_404(Expediente, id=data.get('expediente_id'))
    nuevo_agente_id = data.get('agente_id')
    
    if nuevo_agente_id:
        usuario = get_object_or_404(User, id=nuevo_agente_id)
        exp.agente = usuario
        nombre_agente = usuario.username
    else:
        exp.agente = None
        nombre_agente = "Sin asignar"
        
    exp.save()
    return JsonResponse({'status': 'ok', 'agente_nombre': nombre_agente})

@login_required
@require_POST
def subir_documento_crm(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    tipo = request.POST.get('tipo_documento')
    archivo = request.FILES.get('archivo')
    
    if archivo:
        DocumentoExpediente.objects.create(
            expediente=exp,
            tipo=tipo,
            archivo=archivo,
            nombre_archivo=archivo.name
        )
        messages.success(request, f"Documento '{archivo.name}' subido correctamente.")
    else:
        messages.error(request, "No se seleccionó ningún archivo.")
        
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)