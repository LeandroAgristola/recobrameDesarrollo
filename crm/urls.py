from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('lista/', views.lista_crm, name='lista_crm'),
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
    path('expediente/eliminar/<int:exp_id>/', views.eliminar_expediente, name='eliminar_expediente'),
    path('expediente/restaurar/<int:exp_id>/', views.restaurar_expediente, name='restaurar_expediente'),
    path('expediente/eliminar-total/<int:exp_id>/', views.eliminar_permanente_expediente, name='eliminar_permanente_expediente'),
    path('api/actualizar-seguimiento/', views.actualizar_seguimiento, name='actualizar_seguimiento'),
    path('api/actualizar-comentario/', views.actualizar_comentario_estandar, name='actualizar_comentario'),
    path('api/actualizar-agente/', views.actualizar_agente, name='actualizar_agente'),
]