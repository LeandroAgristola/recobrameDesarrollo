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
    
    # --- [NUEVO] Obtener lista de agentes ---
    # Filtramos solo usuarios activos. Puedes ajustar esto si tienes un grupo específico 'Agentes'.
    agentes_disponibles = User.objects.filter(is_active=True).order_by('username')
    
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
            # 1. Validación de Duplicados (Solo bloquea si el cliente está ACTIVO hoy)
            nombre = form.cleaned_data.get('deudor_nombre')
            telefono = form.cleaned_data.get('deudor_telefono')
            
            # Ahora solo bloqueamos si ya existe uno con el mismo nombre/teléfono Y que esté activo
            duplicado_activo = expedientes_qs.filter(
                Q(deudor_nombre__iexact=nombre) | Q(deudor_telefono=telefono),
                activo=True,
                estado='ACTIVO'
            ).exists()

            if duplicado_activo:
                messages.error(request, f"Ya existe una gestión activa para {nombre}. No se puede duplicar.")
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
        'agentes_disponibles': agentes_disponibles,
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

    # Buscamos registros previos que NO estén activos (Pagados o desactivados)
    # Ordenamos por fecha para traer el más reciente
    antecedente = Expediente.objects.filter(
        empresa_id=empresa_id,
        deudor_nombre__iexact=nombre,
        activo=False
    ).order_by('-fecha_recepcion').first()

    # Si no hay en papelera, buscamos en los que ya pagaron
    if not antecedente:
        antecedente = Expediente.objects.filter(
            empresa_id=empresa_id,
            deudor_nombre__iexact=nombre,
            estado='PAGADO'
        ).order_by('-fecha_recepcion').first()

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