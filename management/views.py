from django.http import HttpResponse

def dashboard_view(request):
    return HttpResponse("<h1>Panel de Management - Recobrame</h1><p>Próximamente Dashboard de Agentes</p>")