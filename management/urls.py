from django.urls import path
from .views import dashboard_view, CustomLoginView, CustomLogoutView

app_name = 'management' # Namespace para usar 'management:home'

urlpatterns = [
    # Ruta Login
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # Ruta Logout
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Ruta Home / Dashboard
    path('', dashboard_view, name='home'),
]