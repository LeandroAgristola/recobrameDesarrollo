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
from django.core.paginator import Paginator
from decimal import Decimal
from django.db.models import Sum

from empresas.models import Empresa
from .models import Expediente, RegistroPago, DocumentoExpediente
from .forms import ExpedienteForm, PagoForm


# --- HELPER PARA CALCULAR DEUDA ---
# ¡IMPORTANTE: SIN @login_required AQUÍ!
def calcular_deuda_actualizada(expediente):
    """
    Calcula la deuda real:
    - Resta pagos recuperados
    - Resta descuentos acumulados
    - Soporta deuda simple, deuda con calendario y deuda cedida
    """

    # 1. Valores base
    monto_original = float(expediente.monto_original) if expediente.monto_original else 0.0
    monto_recuperado = float(expediente.monto_recuperado) if expediente.monto_recuperado else 0.0

    # 2. Descuentos acumulados
    total_descuentos = expediente.pagos.aggregate(
        total=Sum('descuento')
    )['total'] or 0.0
    total_descuentos = float(total_descuentos)

    # -----------------------------------------------------------
    # 3. VENCIMIENTO ANTICIPADO → DEUDA CEDIDA
    # -----------------------------------------------------------
    if expediente.estado == 'CEDIDO':
        deuda_total = monto_original - monto_recuperado - total_descuentos
        return max(0.0, round(deuda_total, 2))

    # -----------------------------------------------------------
    # 4. DEUDA SIMPLE (sin fecha de impago o sin plan de cuotas)
    # -----------------------------------------------------------
    if not expediente.fecha_impago or not expediente.cuotas_totales:
        deuda = monto_original - (monto_recuperado + total_descuentos)
        return max(0.0, deuda)

    # -----------------------------------------------------------
    # 5. DEUDA CON CALENDARIO
    # -----------------------------------------------------------
    hoy = timezone.now().date()
    impago = expediente.fecha_impago

    if impago > hoy:
        return 0.0

    if expediente.cuotas_totales <= 0:
        deuda = monto_original - (monto_recuperado + total_descuentos)
        return max(0.0, deuda)

    valor_cuota = monto_original / expediente.cuotas_totales

    meses_diferencia = (hoy.year - impago.year) * 12 + (hoy.month - impago.month)
    if hoy.day >= impago.day:
        meses_diferencia += 1

    cuotas_vencidas = min(max(1, meses_diferencia), expediente.cuotas_totales)

    deuda_teorica = valor_cuota * cuotas_vencidas
    deuda_real = deuda_teorica - monto_recuperado - total_descuentos

    return max(0.0, deuda_real)

@login_required
def lista_crm(request):
    empresas = Empresa.objects.filter(is_active=True) 
    return render(request, 'crm/lista_crm.html', {'empresas': empresas})

# --- VISTA DE BÚSQUEDA DE ANTECEDENTES (AJAX) ---
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
        ).order_by('-id').first() # <--- ¡CORRECCIÓN AQUÍ! Usamos '-id' en lugar de fecha_creacion

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
    
    # --- 1. LÓGICA DE EXPEDIENTES ---
    expedientes_qs = Expediente.objects.filter(empresa=empresa).order_by('numero_expediente')
    
    # Actualización automática de deuda (Solo activos ACTIVO)
    for exp in expedientes_qs.filter(activo=True, estado='ACTIVO'):
        try:
            nueva_deuda = calcular_deuda_actualizada(exp)
            if exp.monto_actual is None or abs(float(exp.monto_actual) - nueva_deuda) > 0.01:
                exp.monto_actual = Decimal(str(nueva_deuda))
                exp.save(update_fields=['monto_actual'])
        except Exception:
            continue

    # --- 2. PROCESAMIENTO DEL FORMULARIO DE ALTA (POST) ---
    form = ExpedienteForm(empresa=empresa)

    if request.method == 'POST' and 'nuevo_expediente' in request.POST:
        form = ExpedienteForm(request.POST, request.FILES, empresa=empresa)

        if form.is_valid():
            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa

            prefix = f"{empresa.nombre[:3].upper()}{empresa.id}"
            count = Expediente.objects.filter(empresa=empresa).count() + 1
            nuevo_numero = f"{prefix}-{count:06d}"

            while Expediente.objects.filter(numero_expediente=nuevo_numero).exists():
                count += 1
                nuevo_numero = f"{prefix}-{count:06d}"

            nuevo_exp.numero_expediente = nuevo_numero

            try:
                nuevo_exp.monto_actual = Decimal(str(calcular_deuda_actualizada(nuevo_exp)))
            except:
                nuevo_exp.monto_actual = nuevo_exp.monto_original

            nuevo_exp.monto_recuperado = Decimal('0.00')
            nuevo_exp.estado = 'ACTIVO'
            nuevo_exp.activo = True
            nuevo_exp.save()
            form.save_m2m()

            messages.success(request, f"Expediente {nuevo_exp.numero_expediente} creado correctamente.")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
        else:
            messages.error(request, "Error al crear expediente. Revisa los campos.")

    # --- 3. FILTROS IMPAGOS ---
    qs_filtrado = expedientes_qs
    q = request.GET.get('q', '')

    if q:
        qs_filtrado = qs_filtrado.filter(
            Q(deudor_nombre__icontains=q) |
            Q(numero_expediente__icontains=q) |
            Q(deudor_dni__icontains=q) |
            Q(deudor_email__icontains=q) |
            Q(deudor_telefono__icontains=q)
        )

    # Filtros por columna
    f_agente = request.GET.get('f_agente')
    if f_agente: qs_filtrado = qs_filtrado.filter(agente_id=f_agente)

    f_tel = request.GET.get('f_tel')
    if f_tel: qs_filtrado = qs_filtrado.filter(deudor_telefono__icontains=f_tel)

    f_tipo = request.GET.get('f_tipo')
    if f_tipo: qs_filtrado = qs_filtrado.filter(tipo_producto__icontains=f_tipo)

    f_monto = request.GET.get('f_monto')
    if f_monto: qs_filtrado = qs_filtrado.filter(monto_original=f_monto)

    f_cuotas = request.GET.get('f_cuotas')
    if f_cuotas: qs_filtrado = qs_filtrado.filter(cuotas_totales=f_cuotas)

    f_estado = request.GET.get('f_estado')
    if f_estado: qs_filtrado = qs_filtrado.filter(causa_impago=f_estado)

    f_comentario = request.GET.get('f_comentario')
    if f_comentario: qs_filtrado = qs_filtrado.filter(comentario_estandar=f_comentario)

    # Filtros fechas
    f_compra_desde = request.GET.get('f_compra_desde')
    f_compra_hasta = request.GET.get('f_compra_hasta')
    if f_compra_desde: qs_filtrado = qs_filtrado.filter(fecha_compra__gte=f_compra_desde)
    if f_compra_hasta: qs_filtrado = qs_filtrado.filter(fecha_compra__lte=f_compra_hasta)

    f_impago_desde = request.GET.get('f_impago_desde')
    f_impago_hasta = request.GET.get('f_impago_hasta')
    if f_impago_desde: qs_filtrado = qs_filtrado.filter(fecha_impago__gte=f_impago_desde)
    if f_impago_hasta: qs_filtrado = qs_filtrado.filter(fecha_impago__lte=f_impago_hasta)

    # --- BASE ACTIVA PARA TABS ---
    base_qs = qs_filtrado.filter(activo=True)

    impagos = base_qs.filter(estado='ACTIVO')
    cedidos = base_qs.filter(estado='CEDIDO')

    # --- PAGADOS SEPARADOS ---
    pagados_base = base_qs.filter(estado='PAGADO')
    pagados_impagos = pagados_base.filter(fecha_cesion__isnull=True)
    pagados_cedidos = pagados_base.filter(fecha_cesion__isnull=False)

    # --- PAPELERA SEPARADA ---
    papelera_base = expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion')
    papelera_impagos = papelera_base.filter(fecha_cesion__isnull=True)
    papelera_cedidos = papelera_base.filter(fecha_cesion__isnull=False)

    # --- 4. FILTROS RECOBROS ---
    # PRIMERO: Creamos la consulta base de recobros
    recobros_qs = RegistroPago.objects.filter(
        expediente__empresa=empresa
    ).select_related('expediente').order_by('-fecha_pago')

    r_q = request.GET.get('r_q', '')
    r_desde = request.GET.get('r_desde')
    r_hasta = request.GET.get('r_hasta')

    # SEGUNDO: Aplicamos las búsquedas y fechas (si las hay)
    if r_q:
        recobros_qs = recobros_qs.filter(
            Q(expediente__deudor_nombre__icontains=r_q) |
            Q(expediente__numero_expediente__icontains=r_q) |
            Q(monto__icontains=r_q)
        )

    if r_desde: recobros_qs = recobros_qs.filter(fecha_pago__gte=r_desde)
    if r_hasta: recobros_qs = recobros_qs.filter(fecha_pago__lte=r_hasta)

    # TERCERO: Dividimos la consulta para las sub-pestañas "Pills"
    recobros_impagos = recobros_qs.filter(expediente__fecha_cesion__isnull=True)
    recobros_cedidos = recobros_qs.filter(expediente__fecha_cesion__isnull=False)

    # --- 5. UI ---
    tab_activa = request.GET.get('tab', 'impagos')
    if r_q or r_desde or r_hasta:
        tab_activa = 'recobros'


    hay_filtros_impagos = any(key.startswith('f_') for key in request.GET) or (q != '')

    context = {
        'empresa': empresa,

        # Tabs principales
        'impagos': impagos,
        'cedidos': cedidos,

        # Pagados separados
        'pagados_impagos': pagados_impagos,
        'pagados_cedidos': pagados_cedidos,

        # Papelera separada
        'papelera_impagos': papelera_impagos,
        'papelera_cedidos': papelera_cedidos,

        # Recobros filtrados
        'recobros_impagos': recobros_impagos,
        'recobros_cedidos': recobros_cedidos,

        'recobros': recobros_qs,

        'agentes_disponibles': User.objects.filter(is_active=True).order_by('username'),
        'tipos_producto': Expediente.objects.filter(empresa=empresa)
                        .values_list('tipo_producto', flat=True)
                        .distinct()
                        .order_by('tipo_producto'),

        'form': form,

        'q': q,
        'filtros_recobros': {'r_q': r_q, 'r_desde': r_desde, 'r_hasta': r_hasta},
        'tab_activa': tab_activa,
        'hay_filtros_impagos': hay_filtros_impagos,
        'filtros': request.GET
    }

    return render(request, 'crm/dashboard_empresa.html', context)

# --- VISTAS DE ACCIÓN ---

# Vista para editar un expediente, con lógica de validación y actualización de deuda, y redirección inteligente a la página anterior o al dashboard si no hay referer válido
@login_required
@require_POST
def editar_expediente(request, exp_id):
    expediente = get_object_or_404(Expediente, id=exp_id)
    empresa = expediente.empresa
    
    if request.method == 'POST':
        form = ExpedienteForm(request.POST, instance=expediente, empresa=empresa)
        
        if form.is_valid():
            # 1. Guardamos en memoria (sin afectar la base de datos todavía)
            exp = form.save(commit=False)
            
            # 2. FORZAMOS atrapar la Financiación (evita errores de validación)
            nuevo_tipo = request.POST.get('tipo_producto')
            if nuevo_tipo:
                exp.tipo_producto = nuevo_tipo
                
            # 3. LÓGICA DE REVERSIÓN DE CESIÓN
            # Si el estado actual es CEDIDO, validamos si los nuevos datos aún lo permiten
            if exp.estado == 'CEDIDO' and exp.faltantes_cesion:
                exp.estado = 'ACTIVO'
                messages.warning(request, f"El expediente {exp.numero_expediente} volvió a Impagos porque el nuevo método de financiación no admite cesión.")
                
            # Guardamos los datos base actualizados
            exp.save()
            
            # 4. RECALCULAMOS la deuda (Tomará en cuenta si volvió a ACTIVO o sigue CEDIDO)
            exp.monto_actual = Decimal(str(calcular_deuda_actualizada(exp)))
            exp.save()
            
            messages.success(request, f"Expediente {exp.numero_expediente} actualizado correctamente.")
        else:
            # LÓGICA DE RESPALDO SI EL FORM FALLA EN VALIDACIÓN ESTRICTA
            nuevo_tipo = request.POST.get('tipo_producto')
            nuevo_monto = request.POST.get('monto_original')
            
            if nuevo_tipo:
                expediente.tipo_producto = nuevo_tipo
            if nuevo_monto:
                expediente.monto_original = Decimal(nuevo_monto)
                
            # También verificamos reversión en el respaldo
            if expediente.estado == 'CEDIDO' and expediente.faltantes_cesion:
                expediente.estado = 'ACTIVO'
                messages.warning(request, f"El expediente {expediente.numero_expediente} volvió a Impagos porque el nuevo método de financiación no admite cesión.")
                
            expediente.save()
            expediente.monto_actual = Decimal(str(calcular_deuda_actualizada(expediente)))
            expediente.save()
            
            messages.success(request, f"Expediente {expediente.numero_expediente} forzado y actualizado correctamente.")

    # LÓGICA DE RETORNO INTELIGENTE:
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    
    return redirect('crm:dashboard_crm', empresa_id=empresa.id)

# Vista para eliminar un expediente (eliminación lógica), con mensaje de advertencia y redirección inteligente a la página anterior o al dashboard si no hay referer válido
@login_required
def eliminar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    if request.method == 'POST':
        motivo = request.POST.get('motivo_eliminacion')
        exp.eliminar_logico(motivo)
        messages.warning(request, f"Expediente movido a la papelera.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

# Vista para restaurar un expediente desde la papelera, con mensaje de éxito
@login_required
def restaurar_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    exp.restaurar()
    messages.success(request, f"Expediente de {exp.deudor_nombre} restaurado.")
    return redirect('crm:dashboard_crm', empresa_id=exp.empresa.id)

# Vista para eliminar definitivamente un expediente desde la papelera, con confirmación y mensaje de éxito
@login_required
def eliminar_permanente_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa_id = exp.empresa.id
    if request.method == 'POST':
        nombre = exp.deudor_nombre
        exp.delete()
        messages.success(request, f"El expediente de {nombre} ha sido eliminado definitivamente.")
    return redirect('crm:dashboard_crm', empresa_id=empresa_id)

# Vista para actualizar el estado de seguimiento (ticks) de forma rápida sin recargar toda la página
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
            
            # --- LÓGICA DE LIMPIEZA DE FECHAS ---
            if nuevo_estado == 'PAGARA' and fecha_promesa:
                exp.fecha_pago_promesa = fecha_promesa
            else:
                # Si el estado NO es PAGARA, borramos cualquier fecha de promesa previa
                exp.fecha_pago_promesa = None
    else:
        # Si desmarcan el tick, limpiamos todo lo relacionado a ese seguimiento
        setattr(exp, accion, False)
        setattr(exp, f'fecha_{accion}', None)
        if hasattr(exp, f'estado_{accion}'):
            setattr(exp, f'estado_{accion}', None)
        # Opcional: ¿Si desmarcan el tick también quieres borrar la promesa general?
        # exp.fecha_pago_promesa = None 

    exp.save()
    exp.refresh_from_db()

    # Preparar respuesta para el Frontend
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
            'fecha_ultimo': exp.ultimo_mensaje_fecha.strftime("%d/%m/%Y") if hasattr(exp, 'ultimo_mensaje_fecha') and exp.ultimo_mensaje_fecha else "-",
            'estado_legible': exp.get_causa_impago_display() or "-",
            'estado_tick_legible': estado_tick_legible or "-",
            'fecha_promesa_legible': exp.fecha_pago_promesa.strftime("%d/%m") if exp.fecha_pago_promesa else "-"
        })

# Esta vista es para actualizar el comentario estándar (dropdown) de forma rápida sin recargar toda la página
@login_required
@require_POST
def actualizar_comentario_estandar(request):
    data = json.loads(request.body)
    exp = get_object_or_404(Expediente, id=data.get('expediente_id'))
    exp.comentario_estandar = data.get('comentario')
    exp.save()
    return JsonResponse({'status': 'ok'})

# Esta vista es para actualizar el comentario libre (textarea) de forma rápida sin recargar toda la página
@login_required
@require_POST
def guardar_comentario_libre(request, expediente_id):
    # Buscamos el expediente asegurando que pertenezca a una empresa del usuario (seguridad)
    expediente = get_object_or_404(Expediente, id=expediente_id)
    
    # Obtenemos el texto del textarea
    comentario = request.POST.get('comentarios', '').strip()
    
    # Guardamos
    expediente.comentarios = comentario
    expediente.save()
    
    messages.success(request, "Nota guardada correctamente.")
    
    # Redirigimos a la página anterior (el dashboard)
    return redirect(request.META.get('HTTP_REFERER', 'crm:dashboard_crm'))

# Esta vista es para actualizar el agente asignado de forma rápida sin recargar toda la página
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

# Vistas para subir y eliminar documentos relacionados a un expediente
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

# Vista para eliminar un documento específico (AJAX)
@login_required
@require_POST
def eliminar_documento_crm(request, doc_id):
    documento = get_object_or_404(DocumentoExpediente, id=doc_id)
    exp_id = documento.expediente.id
    nombre = documento.nombre_archivo
    documento.delete()
    
    return JsonResponse({'status': 'ok', 'message': f"Documento {nombre} eliminado."})

# Vista de detalle del expediente, donde se muestran los datos completos, pagos realizados, y el formulario para registrar un nuevo pago
@login_required
def detalle_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa = exp.empresa
    
    # --- CÁLCULOS FINANCIEROS ---
    valor_cuota = float(exp.monto_original) / exp.cuotas_totales if exp.cuotas_totales > 0 else 0
    deuda_exigible = calcular_deuda_actualizada(exp)
    monto_a_vencer = float(exp.monto_original) - float(exp.monto_recuperado) - deuda_exigible

    # --- DATOS PARA MODALES ---
    tipos_producto = (
        Expediente.objects
        .filter(empresa=empresa)
        .exclude(tipo_producto='TRANSFERENCIA')
        .values_list('tipo_producto', flat=True)
        .distinct()
    )
    agentes_disponibles = User.objects.filter(is_active=True).order_by('username')

    # --- ANTECEDENTES (LA CORRECCIÓN DEL CONTADOR) ---
    # Si tiene DNI, buscamos por DNI (más exacto)
    if exp.deudor_dni:
        veces_impago = Expediente.objects.filter(
            empresa=empresa, 
            deudor_dni__iexact=exp.deudor_dni.strip(),
            activo=True # Incluye a los que ya están PAGADOS, excluye Papelera
        ).count()
    # Si NO tiene DNI (como tu prueba de Carlos), buscamos por nombre
    else:
        veces_impago = Expediente.objects.filter(
            empresa=empresa,
            deudor_nombre__iexact=exp.deudor_nombre.strip(),
            activo=True
        ).count()

    context = {
        'empresa': empresa,
        'exp': exp,
        'valor_cuota': round(valor_cuota, 2),
        'deuda_vencida': round(deuda_exigible, 2),
        'deuda_futura': round(monto_a_vencer, 2),
        'veces_impago': veces_impago,
        'pagos': exp.pagos.all().order_by('-fecha_pago'),
        'tipos_producto': tipos_producto,
        'agentes_disponibles': agentes_disponibles,
    }
    return render(request, 'crm/detalle_expediente.html', context)

# Vista para listar todos los recobros realizados, con filtros de búsqueda y paginación
@login_required
def lista_recobros(request):
    # Obtener todos los pagos ordenados por fecha
    pagos_qs = RegistroPago.objects.all().select_related('expediente', 'expediente__empresa')

    # --- FILTROS ---
    busqueda = request.GET.get('q', '')
    if busqueda:
        pagos_qs = pagos_qs.filter(
            Q(expediente__deudor_nombre__icontains=busqueda) |
            Q(expediente__deudor_telefono__icontains=busqueda) |
            Q(expediente__numero_expediente__icontains=busqueda)
        )
    
    # Filtro por Empresa (si es staff o admin de empresa)
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        pagos_qs = pagos_qs.filter(expediente__empresa_id=empresa_id)

    # Filtro por Fechas
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_desde:
        pagos_qs = pagos_qs.filter(fecha_pago__gte=fecha_desde)
    if fecha_hasta:
        pagos_qs = pagos_qs.filter(fecha_pago__lte=fecha_hasta)

    # Paginación
    paginator = Paginator(pagos_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'crm/lista_recobros.html', {
        'page_obj': page_obj,
        'filtros': request.GET
    })

# Vistas para registrar, editar y eliminar pagos, con lógica de actualización de deuda y estado del expediente
@login_required
@require_POST
def registrar_pago(request, expediente_id):
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    # Django captura 'monto' y 'descuento' automáticamente aquí
    form = PagoForm(request.POST, request.FILES, expediente=expediente)

    if form.is_valid():
        try:
            pago = form.save(commit=False)
            pago.expediente = expediente
            pago.comision = Decimal(str(pago.monto)) * Decimal('0.10')
            pago.save() # Guarda monto, descuento, fecha, etc.

            # 1. Actualizar lo recuperado
            recuperado_anterior = expediente.monto_recuperado or Decimal('0.00')
            expediente.monto_recuperado = recuperado_anterior + pago.monto
            
            # 2. Recalcular deuda actual (Ya toma el descuento de la base de datos)
            nueva_deuda = calcular_deuda_actualizada(expediente)
            expediente.monto_actual = Decimal(str(nueva_deuda))

            # 3. Lógica de cierre limpia
            if expediente.monto_actual <= Decimal('1.00'):
                expediente.estado = 'PAGADO'
                # IMPORTANTE: Se queda en True para verse en la pestaña "Pagados"
                expediente.activo = True 
            else:
                expediente.estado = 'ACTIVO'
                expediente.activo = True

            expediente.save()

            messages.success(
                request, 
                f"Pago registrado correctamente. Nuevo estado: {expediente.get_estado_display()}"
            )

        except Exception as e:
            messages.error(request, f"Error al procesar el pago: {str(e)}")

    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field, errors in form.errors.items():
            messages.error(request, f"{field}: {errors[0]}")

    return redirect(request.META.get('HTTP_REFERER', 'crm:dashboard_crm'))

# Vistas para editar y eliminar pagos, con lógica de actualización de deuda y estado del expediente
@login_required
@require_POST
def eliminar_pago(request, pago_id):
    pago = get_object_or_404(RegistroPago, id=pago_id)
    expediente = pago.expediente
    
    # 1. Eliminar el pago
    pago.delete()
    
    # 2. Recalcular Monto Recuperado (Suma de los pagos restantes)
    total_recuperado = expediente.pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    expediente.monto_recuperado = total_recuperado
    
    # 3. Recalcular Deuda Actual (Ahora la función considera que hay menos descuentos)
    expediente.monto_actual = Decimal(str(calcular_deuda_actualizada(expediente)))
    
    # 4. Actualizar Estado (Si estaba PAGADO, vuelve a ACTIVO)
    if expediente.monto_actual > 0:
        expediente.estado = 'ACTIVO'
        expediente.activo = True
        
    expediente.save()
    
    messages.success(request, "Pago eliminado y deuda restaurada.")
    return redirect(request.META.get('HTTP_REFERER', 'crm:dashboard_crm'))

# Vista para editar un pago existente, permitiendo modificar monto y descuento, y luego recalculando la deuda y estado del expediente
@login_required
@require_POST
def editar_pago(request, pago_id):
    pago = get_object_or_404(RegistroPago, id=pago_id)
    expediente = pago.expediente
    
    # Obtenemos datos del formulario manual (o usa PagoForm si prefieres)
    nuevo_monto = request.POST.get('monto')
    nuevo_descuento = request.POST.get('descuento', 0)
    
    if nuevo_monto:
        pago.monto = Decimal(nuevo_monto)
        pago.descuento = Decimal(nuevo_descuento)
        pago.save()
        
        # Recalcular todo el expediente
        total_recuperado = expediente.pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        expediente.monto_recuperado = total_recuperado
        expediente.monto_actual = Decimal(str(calcular_deuda_actualizada(expediente)))
        
        # Ajuste de estado
        if expediente.monto_actual <= 0.5: # Margen pequeño
             expediente.estado = 'PAGADO'
        else:
             expediente.estado = 'ACTIVO'
             
        expediente.save()
        messages.success(request, "Pago actualizado correctamente.")
        
    return redirect(request.META.get('HTTP_REFERER', 'crm:dashboard_crm'))

# Vista para confirmar la cesión de un expediente, verificando que cumpla con los requisitos y luego actualizando su estado a CEDIDO, con lógica de aceleración de deuda
@login_required
@require_POST
def confirmar_cesion(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    
    # Verificamos si falta algún requisito usando nuestra regla del modelo
    errores = exp.faltantes_cesion
    
    if errores:
        # Mostramos todos los requisitos faltantes al usuario
        for error in errores:
            messages.error(request, f"No se puede ceder: {error}")
    else:
        # Migramos oficialmente
        exp.estado = 'CEDIDO'
        exp.activo = True 
        
        # Atrapamos la fecha manual del formulario
        fecha_cesion_str = request.POST.get('fecha_cesion')
        if fecha_cesion_str:
            exp.fecha_cesion = fecha_cesion_str
        else:
            # Respaldo de seguridad por si falla el formulario
            exp.fecha_cesion = timezone.now().date()

        # ==========================================================
        # NUEVA LÓGICA: REINICIO DE TICS Y COMPROMISOS (Borrón y cuenta nueva)
        # ==========================================================
        
        # 1. Lista de todos los prefijos de tus secuencias
        etapas_seguimiento = ['w1', 'll1', 'w2', 'll2', 'w3', 'll3', 'w4', 'll4', 'b1'] 
        
        for etapa in etapas_seguimiento:
            # Borra el Checkbox (Pasa a False)
            if hasattr(exp, etapa):
                setattr(exp, etapa, False)
            
            # Borra la fecha de ese tic (Pasa a None)
            if hasattr(exp, f'fecha_{etapa}'):
                setattr(exp, f'fecha_{etapa}', None)
                
            # Borra el estado de resultado de ese tic (Pasa a None)
            if hasattr(exp, f'estado_{etapa}'):
                setattr(exp, f'estado_{etapa}', None)

        # 2. Limpiamos cualquier compromiso de pago general (Ajusta el nombre si en tu modelo se llama distinto)
        if hasattr(exp, 'fecha_compromiso'):
            exp.fecha_compromiso = None
        if hasattr(exp, 'causa_impago'):
            exp.causa_impago = None # Reseteamos el estado general del cliente
            
        # ==========================================================
            
        # MAGIA AQUÍ: Al cambiar el estado a CEDIDO, forzamos el cálculo de "aceleración"
        exp.monto_actual = Decimal(str(calcular_deuda_actualizada(exp)))
        
        exp.save()
        messages.success(request, f"Expediente movido a Cedidos con fecha de cesión: {exp.fecha_cesion}. Secuencias reiniciadas.")
        
    return redirect(request.META.get('HTTP_REFERER', 'crm:dashboard_crm'))