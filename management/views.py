from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

# 1. Vista de Login Personalizada con ruteo por roles
class CustomLoginView(LoginView):
    template_name = 'management/login.html'
    redirect_authenticated_user = True # Si ya está logueado, lo manda al home
    
    def get_success_url(self):
        # Intentamos leer el perfil
        try:
            perfil = self.request.user.perfil
        except:
            return reverse_lazy('management:home')

        # Ruteo inteligente según el ROL
        if perfil.rol == 'ADMIN':
            return reverse_lazy('management:home') # El admin va al panel principal
        
        elif perfil.rol == 'CLIENTE':
            # TODO: Cambiar por la url del panel de clientes cuando lo construyamos
            return reverse_lazy('management:home') 
            
        else:
            # Es AGENTE, ABOGADO o CONTABLE. 
            # TODO: Cambiar por la url de su dashboard personal cuando lo construyamos
            return reverse_lazy('management:home')

# 2. Vista de Logout Personalizada
class CustomLogoutView(LogoutView):
    next_page = 'management:login' # Al salir, vuelve al login

# 3. Dashboard (Protegido con @login_required)
@login_required(login_url='management:login')
def dashboard_view(request):
    """
    Vista principal del dashboard. Solo accesible si estás logueado.
    """
    context = {
        'titulo': 'Resumen General',
        # Aquí pasaremos los datos reales más adelante (Empresas, Deudas, etc.)
    }
    return render(request, 'management/panel.html', context)