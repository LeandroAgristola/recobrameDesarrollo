from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('lista/', views.lista_crm, name='lista_crm'),
    path('gestion/<int:empresa_id>/', views.dashboard_crm, name='dashboard_crm'),
    path('expediente/eliminar/<int:exp_id>/', views.eliminar_expediente, name='eliminar_expediente'),
    path('expediente/restaurar/<int:exp_id>/', views.restaurar_expediente, name='restaurar_expediente'),
    path('expediente/eliminar-total/<int:exp_id>/', views.eliminar_permanente_expediente, name='eliminar_permanente_expediente'),
    path('api/actualizar-seguimiento/', views.actualizar_seguimiento, name='actualizar_seguimiento'),
    path('api/actualizar-comentario/', views.actualizar_comentario_estandar, name='actualizar_comentario'),
    path('api/actualizar-agente/', views.actualizar_agente, name='actualizar_agente'),
    path('expediente/<int:exp_id>/subir-doc/', views.subir_documento_crm, name='subir_documento_crm'),
    path('buscar-antecedentes/', views.buscar_antecedentes_deudor, name='buscar_antecedentes'),
    path('expediente/editar/<int:exp_id>/', views.editar_expediente, name='editar_expediente'),
    path('documento/eliminar/<int:doc_id>/', views.eliminar_documento_crm, name='eliminar_documento'),
    path('expediente/detalle/<int:exp_id>/', views.detalle_expediente, name='detalle_expediente'),
    path('registrar-pago/<int:expediente_id>/', views.registrar_pago, name='registrar_pago'),
]