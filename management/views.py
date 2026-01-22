from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

# 1. Vista de Login Personalizada
class CustomLoginView(LoginView):
    template_name = 'management/login.html'
    redirect_authenticated_user = True # Si ya está logueado, lo manda al home
    
    def get_success_url(self):
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