from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Listado de empresas para gestión (lo que vería el agente)
    path('lista/', views.lista_crm, name='lista_crm'),
    # El dashboard de pestañas de una empresa específica
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
]