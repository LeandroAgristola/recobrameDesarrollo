from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('staff/<int:perfil_id>/', views.detalle_staff, name='detalle_staff'),
    path('staff/<int:perfil_id>/generar_clave/', views.generar_nueva_clave_staff, name='generar_nueva_clave_staff'),
    path('baja/<int:perfil_id>/', views.baja_usuario, name='baja_usuario'),
    path('restaurar/<int:perfil_id>/', views.restaurar_usuario, name='restaurar_usuario'),
    path('eliminar_definitivo/<int:perfil_id>/', views.eliminar_usuario_papelera, name='eliminar_usuario_papelera'),
    path('staff/<int:perfil_id>/editar/', views.editar_staff, name='editar_staff'),
]