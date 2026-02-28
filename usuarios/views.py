from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Perfil
from .forms import NuevoStaffForm, NuevoClienteForm, EditarStaffForm

@login_required
def lista_usuarios(request):
    # --- 1. PROCESAMIENTO DE FORMULARIOS POST ---
    form_staff = NuevoStaffForm()
    form_cliente = NuevoClienteForm()

    if request.method == 'POST':
        if 'crear_staff' in request.POST:
            form_staff = NuevoStaffForm(request.POST, request.FILES)
            if form_staff.is_valid():
                # 1. Crear el usuario nativo
                email = form_staff.cleaned_data['email']
                user = User.objects.create(
                    username=email, email=email,
                    first_name=form_staff.cleaned_data['nombre'],
                    last_name=form_staff.cleaned_data['apellido']
                )
                # Seguridad: Contraseña generada automáticamente
                password = get_random_string(10)
                user.set_password(password)
                user.save()

                # 2. Actualizar el Perfil (ya fue creado por las signals)
                perfil = user.perfil
                perfil.rol = form_staff.cleaned_data['rol']
                perfil.telefono = form_staff.cleaned_data['telefono']
                perfil.dni_nie = form_staff.cleaned_data['dni_nie']
                perfil.netelip_number = form_staff.cleaned_data.get('netelip_number', '')
                perfil.netelip_ext = form_staff.cleaned_data['netelip_ext']
                perfil.netelip_user = form_staff.cleaned_data.get('netelip_user', '')
                perfil.netelip_pass = form_staff.cleaned_data.get('netelip_pass', '')
                perfil.netelip_server = form_staff.cleaned_data.get('netelip_server', '')
                perfil.mercateli_id = form_staff.cleaned_data['mercateli_id']
                perfil.mercateli_despacho = form_staff.cleaned_data.get('mercateli_despacho', '')
                perfil.requiere_cambio_clave = True # Por defecto es True, pero forzamos
                perfil.clave_temporal = password
                perfil.fecha_alta = form_staff.cleaned_data.get('fecha_alta') or timezone.now().date()
                
                if form_staff.cleaned_data.get('foto_perfil'):
                    perfil.foto_perfil = form_staff.cleaned_data['foto_perfil']
                if form_staff.cleaned_data.get('contrato_colaboracion'):
                    perfil.contrato_colaboracion = form_staff.cleaned_data['contrato_colaboracion']
                    
                perfil.save()

                messages.success(request, f"✅ Staff creado. Contraseña temporal: {password} (Cópiala)")
                return redirect('usuarios:lista_usuarios')

        elif 'crear_cliente' in request.POST:
            form_cliente = NuevoClienteForm(request.POST)
            if form_cliente.is_valid():
                email = form_cliente.cleaned_data['email']
                user = User.objects.create(
                    username=email, email=email,
                    first_name=form_cliente.cleaned_data['nombre'],
                    last_name=form_cliente.cleaned_data['apellido']
                )
                password = get_random_string(10)
                user.set_password(password)
                user.save()

                perfil = user.perfil
                perfil.rol = 'CLIENTE'
                perfil.telefono = form_cliente.cleaned_data['telefono']
                perfil.requiere_cambio_clave = True
                perfil.clave_temporal = password
                perfil.save()
                perfil.empresas_asignadas.set(form_cliente.cleaned_data['empresas'])

                messages.success(request, f"✅ Cliente creado. Contraseña temporal: {password} (Cópiala)")
                return redirect('usuarios:lista_usuarios')

        # La edición de staff ahora se maneja en su propia vista editar_staff()    # --- 2. LÓGICA DE LISTADOS Y BUSCADOR ---
    q = request.GET.get('q', '')
    perfiles_qs = Perfil.objects.select_related('user').all()

    if q:
        perfiles_qs = perfiles_qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(telefono__icontains=q)
        )

    # Dividimos entre Activos (Principal) e Inactivos (Papelera)
    staff_activos = perfiles_qs.exclude(rol='CLIENTE').filter(activo=True).order_by('user__first_name')
    clientes_activos = perfiles_qs.filter(rol='CLIENTE', activo=True).prefetch_related('empresas_asignadas').order_by('user__first_name')
    
    staff_inactivos = perfiles_qs.exclude(rol='CLIENTE').filter(activo=False).order_by('-fecha_baja')
    clientes_inactivos = perfiles_qs.filter(rol='CLIENTE', activo=False).order_by('-fecha_baja')

    tab_activa = request.GET.get('tab', 'staff')

    context = {
        'staff': staff_activos, 'clientes': clientes_activos,
        'papelera_staff': staff_inactivos, 'papelera_clientes': clientes_inactivos,
        'q': q, 'tab_activa': tab_activa,
        'form_staff': form_staff, 'form_cliente': form_cliente,
    }
    return render(request, 'usuarios/lista_usuarios.html', context)

# --- ACCIONES DE BAJA Y RESTAURACIÓN ---
@login_required
@require_POST
def baja_usuario(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    fecha_baja = request.POST.get('fecha_baja')

    perfil.activo = False
    perfil.fecha_baja = fecha_baja or timezone.now().date()
    perfil.save()
    
    # Desactivamos el login de Django
    perfil.user.is_active = False
    perfil.user.save()

    messages.warning(request, f"El usuario {perfil.user.first_name} ha sido enviado a la papelera.")
    return redirect('usuarios:lista_usuarios')

@login_required
def restaurar_usuario(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    perfil.activo = True
    perfil.fecha_baja = None
    perfil.fecha_alta = timezone.now().date()
    perfil.save()
    
    perfil.user.is_active = True
    perfil.user.save()

    messages.success(request, f"Usuario {perfil.user.first_name} restaurado con éxito.")
    return redirect(f"/usuarios/?tab=papelera")

@login_required
def detalle_staff(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    # Seguridad básica por ahora
    if perfil.rol == 'CLIENTE':
        return redirect('usuarios:lista_usuarios')
    
    # Importar RegistroPago aquí para evitar dependencias circulares
    from crm.models import RegistroPago
    recobros_agente = RegistroPago.objects.filter(
        expediente__agente=perfil.user
    ).select_related('expediente__empresa').order_by('-fecha_pago')
    
    context = {
        'perfil': perfil,
        'recobros_agente': recobros_agente
    }
    return render(request, 'usuarios/detalle_staff.html', context)

@login_required
@require_POST
def generar_nueva_clave_staff(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    
    # Solo administradores pueden regenerar claves de staff o el mismo usuario
    if request.user.perfil.rol != 'ADMIN' and request.user.perfil.id != perfil.id:
        messages.error(request, "No tienes permisos para regenerar esta clave.")
        return redirect('usuarios:detalle_staff', perfil_id=perfil.id)

    nueva_clave = get_random_string(10)
    user = perfil.user
    user.set_password(nueva_clave)
    user.save()

    perfil.clave_temporal = nueva_clave
    perfil.requiere_cambio_clave = True
    perfil.save()

    messages.success(request, f"Se ha generado una nueva clave para {user.first_name}.")
    return redirect('usuarios:detalle_staff', perfil_id=perfil.id)

@login_required
@require_POST
def editar_staff(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    form_editar = EditarStaffForm(request.POST, request.FILES)
    if form_editar.is_valid():
        user = perfil.user
        user.first_name = form_editar.cleaned_data['nombre']
        user.last_name = form_editar.cleaned_data['apellido']
        user.save()

        perfil.rol = form_editar.cleaned_data['rol']
        perfil.telefono = form_editar.cleaned_data['telefono']
        perfil.dni_nie = form_editar.cleaned_data['dni_nie']
        perfil.netelip_number = form_editar.cleaned_data.get('netelip_number', '')
        perfil.netelip_ext = form_editar.cleaned_data['netelip_ext']
        perfil.netelip_user = form_editar.cleaned_data.get('netelip_user', '')
        perfil.netelip_pass = form_editar.cleaned_data.get('netelip_pass', '')
        perfil.netelip_server = form_editar.cleaned_data.get('netelip_server', '')
        perfil.mercateli_id = form_editar.cleaned_data.get('mercateli_id', '')
        perfil.mercateli_despacho = form_editar.cleaned_data.get('mercateli_despacho', '')
        
        if form_editar.cleaned_data.get('foto_perfil'):
            perfil.foto_perfil = form_editar.cleaned_data['foto_perfil']
        if form_editar.cleaned_data.get('contrato_colaboracion'):
            perfil.contrato_colaboracion = form_editar.cleaned_data['contrato_colaboracion']
            
        perfil.save()

        messages.success(request, f"✅ Staff {user.first_name} actualizado correctamente.")
    else:
        messages.error(request, "Error al actualizar staff.")
    
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:lista_usuarios'))

@login_required
@require_POST
def eliminar_usuario_papelera(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    if perfil.activo:
        messages.error(request, "No se puede eliminar un usuario activo.")
        return redirect('usuarios:lista_usuarios')
    
    user = perfil.user
    first_name = user.first_name
    user.delete() # Esto también borra el perfil debido a on_delete=models.CASCADE
    
    messages.success(request, f"Usuario {first_name} eliminado permanentemente.")
    return redirect(f"/usuarios/?tab=papelera")