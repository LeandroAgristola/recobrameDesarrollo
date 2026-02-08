from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('lista/', views.lista_crm, name='lista_crm'),
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
    path('expediente/eliminar/<int:exp_id>/', views.eliminar_expediente, name='eliminar_expediente'),
    path('expediente/restaurar/<int:exp_id>/', views.restaurar_expediente, name='restaurar_expediente'),
]