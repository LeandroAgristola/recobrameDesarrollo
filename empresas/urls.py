from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.lista_empresas, name='lista_empresas'),
    path('nueva/', views.crear_empresa, name='crear_empresa'),
    path('detalle/<int:empresa_id>/', views.detalle_empresa, name='detalle_empresa'),
    path('editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    path('desactivar/<int:empresa_id>/', views.desactivar_empresa, name='desactivar_empresa'),
    path('reactivar/<int:empresa_id>/', views.reactivar_empresa, name='reactivar_empresa'),
]