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
from decimal import Decimal

from empresas.models import Empresa
from .models import Expediente, RegistroPago, DocumentoExpediente
from .forms import ExpedienteForm, PagoForm

# --- HELPER PARA CALCULAR DEUDA ---
# ¡IMPORTANTE: SIN @login_required AQUÍ!
def calcular_deuda_actualizada(expediente):
    """
    Calcula la deuda real.
    - Si tiene fechas y cuotas: Calcula mora cronológica.
    - Si NO tiene fechas (Deuda Simple): Es (Total - Pagado).
    """
    # 1. Aseguramos valores numéricos base
    monto_original = float(expediente.monto_original) if expediente.monto_original else 0.0
    monto_recuperado = float(expediente.monto_recuperado) if expediente.monto_recuperado else 0.0

    # 2. LÓGICA DE DEUDA SIMPLE (Si falta fecha de impago O no hay plan de cuotas)
    if not expediente.fecha_impago or not expediente.cuotas_totales:
        # En este caso, la deuda es todo lo que falta pagar, sin calendario.
        deuda_real = monto_original - monto_recuperado
        return max(0.0, deuda_real)

    # -----------------------------------------------------------
    # 3. LÓGICA DE CALENDARIO (Solo si tenemos fecha y cuotas)
    # -----------------------------------------------------------
    
    hoy = timezone.now().date()
    impago = expediente.fecha_impago

    # Si la fecha de impago es futura, teóricamente no debe nada HOY
    if impago > hoy:
        return 0.0

    # Calcular valor de la cuota
    # (Ya validamos arriba que cuotas_totales existe, pero evitamos división por 0 por seguridad)
    if expediente.cuotas_totales <= 0:
        return max(0.0, monto_original - monto_recuperado)
        
    valor_cuota = monto_original / expediente.cuotas_totales

    # Calcular cuántas cuotas han vencido
    meses_diferencia = (hoy.year - impago.year) * 12 + (hoy.month - impago.month)
    
    if hoy.day >= impago.day:
        meses_diferencia += 1
    
    cuotas_vencidas = max(1, meses_diferencia)
    cuotas_vencidas = min(cuotas_vencidas, expediente.cuotas_totales)

    # Deuda teórica acumulada
    deuda_teorica = valor_cuota * cuotas_vencidas

    # Restamos lo pagado
    deuda_real = deuda_teorica - monto_recuperado

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
    
    # Base QuerySet
    expedientes_qs = Expediente.objects.filter(empresa=empresa).order_by('numero_expediente')
    
    # --- 1. ACTUALIZACIÓN AUTOMÁTICA DE DEUDA (Solo activos y con deuda) ---
    # Optimizamos: Solo recalculamos si no se ha hecho hoy o si el usuario entra al dashboard
    # Para evitar sobrecarga en cada refresh, podrías mover esto a una tarea programada (Celery/Cron)
    # Por ahora, lo mantenemos simple pero protegido con try/except
    for exp in expedientes_qs.filter(activo=True, estado='ACTIVO'):
        try:
            nueva_deuda = calcular_deuda_actualizada(exp)
            # Solo guardamos si hay diferencia significativa para no saturar la DB
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
            # Validación de duplicados
            nombre = form.cleaned_data.get('deudor_nombre')
            telefono = form.cleaned_data.get('deudor_telefono')
            
            # Buscamos duplicados solo en esta empresa
            duplicado = expedientes_qs.filter(
                Q(deudor_nombre__iexact=nombre) | Q(deudor_telefono=telefono)
            ).exists()
            
            if duplicado:
                messages.warning(request, f"Nota: Ya existe un expediente similar para {nombre} o {telefono}.")

            nuevo_exp = form.save(commit=False)
            nuevo_exp.empresa = empresa 
            
            # Generar ID Personalizado (Ej: EMP-000001)
            prefix = empresa.nombre[:3].upper()
            count = Expediente.objects.filter(empresa=empresa).count() + 1
            nuevo_exp.numero_expediente = f"{prefix}-{count:06d}"

            # Calcular Deuda Inicial usando la función helper
            try:
                nuevo_exp.monto_actual = Decimal(str(calcular_deuda_actualizada(nuevo_exp)))
            except Exception:
                nuevo_exp.monto_actual = nuevo_exp.monto_original

            nuevo_exp.monto_recuperado = Decimal('0.00')
            nuevo_exp.estado = 'ACTIVO'
            nuevo_exp.activo = True
            nuevo_exp.save()
            
            # Guardar relación ManyToMany (si el form tiene campos m2m)
            form.save_m2m()
            
            messages.success(request, f"Expediente {nuevo_exp.numero_expediente} creado exitosamente.")
            return redirect('crm:dashboard_crm', empresa_id=empresa.id)
        else:
            messages.error(request, "Error al crear expediente. Revisa los campos marcados.")

    # --- 3. LÓGICA DE FILTROS (GET) ---
    # Inicializamos con todos los expedientes de la empresa
    qs_filtrado = expedientes_qs 

    # Búsqueda Global
    q = request.GET.get('q', '')
    if q:
        qs_filtrado = qs_filtrado.filter(
            Q(deudor_nombre__icontains=q) | 
            Q(numero_expediente__icontains=q) |
            Q(deudor_dni__icontains=q) |
            Q(deudor_email__icontains=q) |
            Q(deudor_telefono__icontains=q)
        )

    # Filtros Específicos
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

    # Filtros de Fechas (Rangos)
    f_compra_desde = request.GET.get('f_compra_desde')
    f_compra_hasta = request.GET.get('f_compra_hasta')
    if f_compra_desde: qs_filtrado = qs_filtrado.filter(fecha_compra__gte=f_compra_desde)
    if f_compra_hasta: qs_filtrado = qs_filtrado.filter(fecha_compra__lte=f_compra_hasta)
    
    f_impago_desde = request.GET.get('f_impago_desde')
    f_impago_hasta = request.GET.get('f_impago_hasta')
    if f_impago_desde: qs_filtrado = qs_filtrado.filter(fecha_impago__gte=f_impago_desde)
    if f_impago_hasta: qs_filtrado = qs_filtrado.filter(fecha_impago__lte=f_impago_hasta)

    # Filtro "Menor a X días en impago"
    f_dias_max = request.GET.get('f_dias_max')
    if f_dias_max:
        try:
            dias = int(f_dias_max)
            fecha_limite = timezone.now().date() - timezone.timedelta(days=dias)
            qs_filtrado = qs_filtrado.filter(fecha_impago__gte=fecha_limite)
        except ValueError:
            pass

    # Filtros Booleanos (Ticks W/L y Documentación)
    # Iteramos dinámicamente sobre los campos w1..w5 y ll1..ll5
    for i in range(1, 6):
        if request.GET.get(f'f_w{i}') == 'true':
            qs_filtrado = qs_filtrado.filter(**{f'w{i}': True})
        if request.GET.get(f'f_l{i}') == 'true':
            qs_filtrado = qs_filtrado.filter(**{f'll{i}': True})

    if request.GET.get('f_be') == 'true': qs_filtrado = qs_filtrado.filter(buro_enviado=True)
    if request.GET.get('f_br') == 'true': qs_filtrado = qs_filtrado.filter(buro_recibido=True)
    if request.GET.get('f_as') == 'true': qs_filtrado = qs_filtrado.filter(asnef_inscrito=True)
    if request.GET.get('f_ls') == 'true': qs_filtrado = qs_filtrado.filter(llamada_seguimiento_asnef=True)

    # Filtros de Última Interacción (Mensajes)
    f_msj_desde = request.GET.get('f_msj_desde')
    f_msj_hasta = request.GET.get('f_msj_hasta')
    
    if f_msj_desde or f_msj_hasta:
        # Esto filtra si ALGUNA de las fechas de gestión cae en el rango
        q_msj = Q()
        campos_fecha = [f'fecha_w{i}' for i in range(1,6)] + [f'fecha_ll{i}' for i in range(1,6)]
        
        # Filtramos solo aquellos campos que tienen valor
        for campo in campos_fecha:
            condicion = Q()
            if f_msj_desde: condicion &= Q(**{f"{campo}__date__gte": f_msj_desde})
            if f_msj_hasta: condicion &= Q(**{f"{campo}__date__lte": f_msj_hasta})
            
            if condicion:
                q_msj |= condicion
        
        qs_filtrado = qs_filtrado.filter(q_msj)

    # Filtro Fecha Promesa de Pago
    f_pago_desde = request.GET.get('f_pago_desde')
    f_pago_hasta = request.GET.get('f_pago_hasta')
    if f_pago_desde: qs_filtrado = qs_filtrado.filter(fecha_pago_promesa__gte=f_pago_desde)
    if f_pago_hasta: qs_filtrado = qs_filtrado.filter(fecha_pago_promesa__lte=f_pago_hasta)

    # --- LÓGICA DE RECOBROS (FILTROS INDEPENDIENTES) ---
    recobros_qs = RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago')

    # Filtros con prefijo 'r_' para no chocar con los de impagos
    r_q = request.GET.get('r_q', '')
    r_desde = request.GET.get('r_desde')
    r_hasta = request.GET.get('r_hasta')

    if r_q:
        recobros_qs = recobros_qs.filter(
            Q(expediente__deudor_nombre__icontains=r_q) |
            Q(expediente__numero_expediente__icontains=r_q)
        )
    if r_desde:
        recobros_qs = recobros_qs.filter(fecha_pago__gte=r_desde)
    if r_hasta:
        recobros_qs = recobros_qs.filter(fecha_pago__lte=r_hasta)

    # Contexto actualizado
    context = {
        # ... otros ...
        'recobros': recobros_qs, # Ahora enviamos la lista filtrada
        'filtros_recobros': { # Enviamos los valores para rellenar los inputs
            'r_q': r_q,
            'r_desde': r_desde,
            'r_hasta': r_hasta
        },
        'active_tab': 'recobros' if (r_q or r_desde or r_hasta) else 'impagos' # Truco para mantener pestaña
    }

    # --- 4. PREPARAR CONTEXTO ---
    
    # Listas filtradas para cada pestaña
    # IMPORTANTE: Usamos 'qs_filtrado' que ya tiene todos los filtros aplicados
    impagos = qs_filtrado.filter(activo=True, estado='ACTIVO')
    cedidos = qs_filtrado.filter(activo=True, estado='CEDIDO')
    pagados = qs_filtrado.filter(activo=True, estado='PAGADO')
    
    # La papelera suele mostrarse aparte, sin filtros o con filtros propios, 
    # pero aquí aplicamos los mismos por coherencia (salvo estado activo)
    papelera = expedientes_qs.filter(activo=False).order_by('-fecha_eliminacion')
    
    # Recobros (Pagos registrados)
    # Se muestran todos los de la empresa, ordenados por fecha reciente
    recobros = RegistroPago.objects.filter(expediente__empresa=empresa).order_by('-fecha_pago')

    # Datos auxiliares para los selects de filtro
    agentes_disponibles = User.objects.filter(is_active=True).order_by('username')
    tipos_producto = Expediente.objects.filter(empresa=empresa).values_list('tipo_producto', flat=True).distinct().order_by('tipo_producto')

    context = {
        'empresa': empresa,
        'impagos': impagos,
        'cedidos': cedidos,
        'pagados': pagados,
        'recobros': recobros,  # <--- Vital para la tabla de cobros
        'papelera': papelera,
        'agentes_disponibles': agentes_disponibles,
        'tipos_producto': tipos_producto,
        'form': form,
        'filtros': request.GET # Para mantener los valores en los inputs del HTML
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

@login_required
def editar_expediente(request, exp_id):
    expediente = get_object_or_404(Expediente, id=exp_id)
    empresa = expediente.empresa
    
    if request.method == 'POST':
        form = ExpedienteForm(request.POST, instance=expediente, empresa=empresa)
        if form.is_valid():
            exp = form.save()
            # Recalculamos la deuda por si cambiaron fechas o montos
            exp.monto_actual = calcular_deuda_actualizada(exp)
            exp.save()
            
            messages.success(request, f"Expediente {exp.numero_expediente} actualizado correctamente.")
        else:
            # Si hay errores (ej: un campo obligatorio vacío), los capturamos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")

    # LÓGICA DE RETORNO INTELIGENTE:
    # Intentamos volver a la página anterior (Detalle o Dashboard)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    
    # Si por algún motivo no hay referer, volvemos al dashboard por defecto
    return redirect('crm:dashboard_crm', empresa_id=empresa.id)

@login_required
@require_POST
def eliminar_documento_crm(request, doc_id):
    documento = get_object_or_404(DocumentoExpediente, id=doc_id)
    exp_id = documento.expediente.id
    nombre = documento.nombre_archivo
    documento.delete()
    
    return JsonResponse({'status': 'ok', 'message': f"Documento {nombre} eliminado."})

@login_required
def detalle_expediente(request, exp_id):
    exp = get_object_or_404(Expediente, id=exp_id)
    empresa = exp.empresa
    
    # --- CÁLCULOS FINANCIEROS ---
    valor_cuota = float(exp.monto_original) / exp.cuotas_totales if exp.cuotas_totales > 0 else 0
    deuda_exigible = calcular_deuda_actualizada(exp)
    monto_a_vencer = float(exp.monto_original) - float(exp.monto_recuperado) - deuda_exigible

    # --- DATOS PARA EL MODAL DE EDICIÓN (ESTO ES LO QUE FALTA) ---
    # Obtenemos los tipos de producto únicos que ya existen en la empresa
    # O bien, puedes sacarlos de empresa.tipos_impagos si prefieres esa lista
    tipos_producto = Expediente.objects.filter(empresa=empresa).values_list('tipo_producto', flat=True).distinct()
    
    # También necesitamos los agentes para el select de edición
    agentes_disponibles = User.objects.filter(is_active=True).order_by('username')

    # Antecedentes
    veces_impago = Expediente.objects.filter(
        empresa=empresa, 
        deudor_dni=exp.deudor_dni
    ).count() if exp.deudor_dni else 1

    context = {
        'empresa': empresa,
        'exp': exp,
        'valor_cuota': round(valor_cuota, 2),
        'deuda_vencida': round(deuda_exigible, 2),
        'deuda_futura': round(monto_a_vencer, 2),
        'veces_impago': veces_impago,
        'pagos': exp.pagos.all().order_by('-fecha_pago'),
        
        # Nuevos campos para que el modal funcione correctamente:
        'tipos_producto': tipos_producto,
        'agentes_disponibles': agentes_disponibles,
    }
    return render(request, 'crm/detalle_expediente.html', context)

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


@login_required
@require_POST
def registrar_pago(request, expediente_id):
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    form = PagoForm(request.POST, request.FILES)
    
    if form.is_valid():
        try:
            # 1. Guardar el Pago
            pago = form.save(commit=False)
            pago.expediente = expediente
            pago.comision = pago.monto * Decimal('0.10') # Placeholder 10%
            pago.save()

            # 2. Actualizar el Total Recuperado en el objeto (memoria)
            recuperado_anterior = expediente.monto_recuperado or Decimal('0.00')
            nuevo_recuperado = recuperado_anterior + pago.monto
            expediente.monto_recuperado = nuevo_recuperado

            # 3. RECALCULAR DEUDA (Llamamos a la función YA CORREGIDA)
            # Como ya actualizamos expediente.monto_recuperado arriba, el cálculo será correcto
            nueva_deuda = calcular_deuda_actualizada(expediente)
            expediente.monto_actual = Decimal(str(nueva_deuda))

            # 4. Verificar cancelación total
            monto_original = expediente.monto_original or Decimal('0.00')
            saldo_total = monto_original - nuevo_recuperado
            
            if saldo_total <= Decimal('1.00'):
                expediente.estado = 'PAGADO'
                expediente.causa_impago = 'PAGADO'
                expediente.activo = False
                expediente.monto_actual = Decimal('0.00')
            
            # 5. GUARDAR CAMBIOS EN EXPEDIENTE
            expediente.save()
            
            messages.success(request, f"Pago de {pago.monto}€ registrado. Nueva deuda: {expediente.monto_actual}€")
        
        except Exception as e:
            messages.error(request, f"Error interno: {str(e)}")
    else:
        messages.error(request, "Datos inválidos en el formulario.")

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'crm:dashboard_crm', empresa_id=expediente.empresa.id)