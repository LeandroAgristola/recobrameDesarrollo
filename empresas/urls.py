from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # Listados (Pestañas)
    path('', views.lista_empresas, name='lista_empresas'),          # Tab Activas
    path('papelera/', views.papelera_empresas, name='papelera_empresas'), # Tab Papelera
    
    # CRUD
    path('nueva/', views.crear_empresa, name='crear_empresa'),
    path('detalle/<int:empresa_id>/', views.detalle_empresa, name='detalle_empresa'),
    path('editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    
    # Acciones de Estado
    path('desactivar/<int:empresa_id>/', views.desactivar_empresa, name='desactivar_empresa'), # Mover a papelera
    path('reactivar/<int:empresa_id>/', views.reactivar_empresa, name='reactivar_empresa'),    # Sacar de papelera
    path('eliminar/<int:empresa_id>/', views.eliminar_empresa, name='eliminar_empresa'),       # Eliminar DB (Físico)
]