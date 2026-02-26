from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('baja/<int:perfil_id>/', views.baja_usuario, name='baja_usuario'),
    path('restaurar/<int:perfil_id>/', views.restaurar_usuario, name='restaurar_usuario'),
]