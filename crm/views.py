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

# --- HELPER PARA CALCULAR DEUDA ---
def calcular_deuda_actualizada(expediente):
    """
    Calcula la deuda exigible basándose en la fecha de impago y la fecha actual.
    Logica: (Cuotas Vencidas * Valor Cuota) - Lo que ya pagó
    """
    """
    Calcula la DEUDA EXIGIBLE (Lo que ya venció y no se pagó).
    """
    if not expediente.fecha_impago or expediente.monto_original <= 0 or expediente.cuotas_totales <= 0:
        return 0

    hoy = timezone.now().date()
    impago = expediente.fecha_impago

    if impago > hoy:
        return 0

    valor_cuota = float(expediente.monto_original) / expediente.cuotas_totales

    # Calculamos meses desde el primer impago hasta hoy usando relativedelta
    from dateutil.relativedelta import relativedelta
    diff = relativedelta(hoy, impago)
    meses_vencidos = diff.years * 12 + diff.months + 1  # +1 porque el mes de impago ya cuenta

    # No puede superar las cuotas totales del contrato
    cuotas_vencidas_reales = min(meses_vencidos, expediente.cuotas_totales)
    deuda_que_deberia_existir = valor_cuota * cuotas_vencidas_reales

    deuda_exigible = deuda_que_deberia_existir - float(expediente.monto_recuperado)
    return max(0.0, deuda_exigible)

# --- VISTAS ---

@login_required
def dashboard_crm(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id, is_active=True)
    expedientes_qs = Expediente.objects.filter(empresa=empresa)
    
    # --- 1. CAPTURA DE PARÁMETROS ---
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
    f_estado = request.GET.get('f_estado') # Causa Impago
    f_deuda = request.GET.get('f_deuda')

    # Filtros Booleanos (ASNEF, BURO)
    f_be = request.GET.get('f_be') # Buro Enviado
    f_br = request.GET.get('f_br') # Buro Recibido
    f_as = request.GET.get('f_as') # ASNEF Inscrito
    f_ls = request.GET.get('f_ls') # Llamada Seguimiento

    # --- 2. APLICACIÓN DE FILTROS ---
    
    # Búsqueda General
    if q:
        expedientes_qs = expedientes_qs.filter(
            Q(deudor_nombre__icontains=q) | 
            Q(deudor_telefono__icontains=q) | 
            Q(numero_expediente__icontains=q) |
            Q(deudor_dni__icontains=q)
        )

    # Filtros Específicos
    if f_agente:
        expedientes_qs = expedientes_qs.filter(agente_id=f_agente)
    if f_nombre:
        expedientes_qs = expedientes_qs.filter(deudor_nombre__icontains=f_nombre)
    if f_tel:
        expedientes_qs = expedientes_qs.filter(deudor_telefono__icontains=f_tel)
    if f_tipo:
        expedientes_qs = expedientes_qs.filter(tipo_producto__icontains=f_tipo)
    if f_monto:
        expedientes_qs = expedientes_qs.filter(monto_original__icontains=f_monto)
    if f_cuotas:
        expedientes_qs = expedientes_qs.filter(cuotas_totales=f_cuotas)
    if f_fecha_compra:
        expedientes_qs = expedientes_qs.filter(fecha_compra=f_fecha_compra)
    if f_fecha_impago:
        expedientes_qs = expedientes_qs.filter(fecha_impago=f_fecha_impago)
    
    # Filtro Días (Mayor o igual a)
    if f_dias:
        try:
            dias = int(f_dias)
            fecha_limite = timezone.now().date() - timezone.timedelta(days=dias)
            expedientes_qs = expedientes_qs.filter(fecha_impago__lte=fecha_limite)
        except ValueError:
            pass

    if f_estado:
        expedientes_qs = expedientes_qs.filter(causa_impago=f_estado)
    if f_deuda:
        expedientes_qs = expedientes_qs.filter(monto_actual__icontains=f_deuda)

    # --- 3. FILTROS DINÁMICOS DE TICKS (W1-W5, L1-L5) ---
    for i in range(1, 6):
        # Filtro Whatsapp (w1...w5)
        val_w = request.GET.get(f'f_w{i}')
        if val_w in ['true', 'false']:
            is_true = (val_w == 'true')
            # Construimos el nombre del campo dinámicamente: w1, w2...
            kwargs = {f'w{i}': is_true}
            expedientes_qs = expedientes_qs.filter(**kwargs)

        # Filtro Llamada (ll1...ll5)
        val_l = request.GET.get(f'f_l{i}')
        if val_l in ['true', 'false']:
            is_true = (val_l == 'true')
            # Construimos el nombre del campo: ll1, ll2...
            kwargs = {f'll{i}': is_true}
            expedientes_qs = expedientes_qs.filter(**kwargs)

    # --- 4. FILTROS BOOLEANOS ASNEF ---
    if f_be in ['true', 'false']:
        expedientes_qs = expedientes_qs.filter(buro_enviado=(f_be == 'true'))
    if f_br in ['true', 'false']:
        expedientes_qs = expedientes_qs.filter(buro_recibido=(f_br == 'true'))
    if f_as in ['true', 'false']:
        expedientes_qs = expedientes_qs.filter(asnef_inscrito=(f_as == 'true'))
    if f_ls in ['true', 'false']:
        expedientes_qs = expedientes_qs.filter(llamada_seguimiento_asnef=(f_ls == 'true'))

    # ... Resto de tu lógica (Agentes, Contexto, Render) se mantiene igual ...
    
    context = {
        'empresa': empresa,
        'q': q, # Mantenemos búsqueda
        # Pasamos los QuerySets filtrados
        'impagos': expedientes_qs.filter(activo=True, estado='ACTIVO'),
        'cedidos': expedientes_qs.filter(activo=True, estado='CEDIDO'),
        'pagados': expedientes_qs.filter(activo=True, estado='PAGADO'),
        'papelera': expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion'),
        'agentes_disponibles': User.objects.filter(is_active=True).order_by('username'),
        'form': ExpedienteForm(empresa=empresa),
        # ...
    }
    return render(request, 'crm/dashboard_empresa.html', context)
# --- VISTAS DE ACCIÓN ---

@login_required
def eliminar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    
    # Ahora esperamos un POST desde el modal
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
    """Elimina FÍSICAMENTE tras confirmar en modal"""
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    
    if request.method == 'POST': # Seguridad extra
        nombre = exp.deudor_nombre
        exp.delete()
        messages.success(request, f"El expediente de {nombre} ha sido eliminado definitivamente.")
        
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

@login_required
def lista_crm(request):
    """Vista para el listado general de empresas en el CRM"""
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})

# crm/views.py

# ... imports ...

@login_required
@require_POST
def actualizar_seguimiento(request):
    data = json.loads(request.body)
    exp_id = data.get('expediente_id')
    accion = data.get('tipo_accion') 
    valor = data.get('valor')        
    nuevo_estado = data.get('nuevo_estado')
    fecha_promesa = data.get('fecha_promesa') # <--- NUEVO

    exp = get_object_or_404(Expediente, id=exp_id)
    
    if valor:
        setattr(exp, accion, True)
        setattr(exp, f'fecha_{accion}', timezone.now())
        
        if nuevo_estado:
            exp.causa_impago = nuevo_estado
            
            # --- NUEVO: GUARDAR EL ESTADO EN EL HISTORIAL DEL TICK ---
            # Guardamos el estado seleccionado EN EL CAMPO DEL TICK ESPECÍFICO
            # Ej: estado_w1 = 'NO_QUIERE'
            if hasattr(exp, f'estado_{accion}'):
                setattr(exp, f'estado_{accion}', nuevo_estado)

            if nuevo_estado == 'PAGARA' and fecha_promesa:
                exp.fecha_pago_promesa = fecha_promesa
    else:
        setattr(exp, accion, False)
        setattr(exp, f'fecha_{accion}', None)
        # Limpiamos el historial si se desmarca
        if hasattr(exp, f'estado_{accion}'):
            setattr(exp, f'estado_{accion}', None)

    exp.save()
    exp.refresh_from_db()

    # Obtener nombre legible del estado específico del tick (ej: estado_w1)
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
    """Actualiza el select de comentarios de la tabla"""
    data = json.loads(request.body)
    exp = get_object_or_404(Expediente, id=data.get('expediente_id'))
    exp.comentario_estandar = data.get('comentario')
    exp.save()
    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def actualizar_agente(request):
    """
    Permite cambiar el agente asignado.
    Solo permitido para ADMINS o STAFF.
    """
    if not request.user.is_staff: # Validación de seguridad
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
    
    return JsonResponse({
        'status': 'ok',
        'agente_nombre': nombre_agente
    })

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

@login_required
def buscar_antecedentes_deudor(request):
    nombre = request.GET.get('nombre', '').strip()
    empresa_id = request.GET.get('empresa_id')
    
    if not nombre or not empresa_id:
        return JsonResponse({'status': 'empty'})

    # Buscamos el último registro (incluso si está en papelera o pagado)
    antecedente = Expediente.objects.filter(
        empresa_id=empresa_id,
        deudor_nombre__iexact=nombre
    ).order_by('-fecha_creacion').first()

    if antecedente:
        return JsonResponse({
            'status': 'success',
            'datos': {
                'telefono': antecedente.deudor_telefono,
                'email': antecedente.deudor_email,
                'dni': antecedente.deudor_dni,
            }
        })
    
    return JsonResponse({'status': 'not_found'})