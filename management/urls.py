from django.contrib import admin
from django.urls import path
from management.views import dashboard_view # <--- Importar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='home'), # <--- Ruta raíz apunta al management
]