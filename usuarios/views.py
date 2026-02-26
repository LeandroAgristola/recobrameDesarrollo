from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Perfil
from .forms import NuevoStaffForm, NuevoClienteForm

@login_required
def lista_usuarios(request):
    # --- 1. PROCESAMIENTO DE FORMULARIOS POST ---
    form_staff = NuevoStaffForm()
    form_cliente = NuevoClienteForm()

    if request.method == 'POST':
        if 'crear_staff' in request.POST:
            form_staff = NuevoStaffForm(request.POST)
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
                perfil.netelip_ext = form_staff.cleaned_data['netelip_ext']
                perfil.mercateli_id = form_staff.cleaned_data['mercateli_id']
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
                perfil.save()
                perfil.empresas_asignadas.set(form_cliente.cleaned_data['empresas'])

                messages.success(request, f"✅ Cliente creado. Contraseña temporal: {password} (Cópiala)")
                return redirect('usuarios:lista_usuarios')

    # --- 2. LÓGICA DE LISTADOS Y BUSCADOR ---
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
    perfil.save()
    
    perfil.user.is_active = True
    perfil.user.save()

    messages.success(request, f"Usuario {perfil.user.first_name} restaurado con éxito.")
    return redirect(f"/usuarios/?tab=papelera")