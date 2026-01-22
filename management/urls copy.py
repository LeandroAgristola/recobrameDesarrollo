from django.urls import path
from . import views

app_name = 'management' # Define el espacio de nombres

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel/', views.panel, name='panel'), # La URL para el panel
]