from django import forms  # <-- Corregido aquí
from .models import Expediente
from django.contrib.auth.models import User

class ExpedienteForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            'agente', 'numero_expediente', 'deudor_nombre', 'deudor_dni', 
            'deudor_telefono', 'deudor_email', 'tipo_producto', 
            'monto_original', 'cuotas_totales', 'fecha_compra', 
            'fecha_impago', 'estado', 'causa_impago', 'comentarios'
        ]
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_impago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'agente': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'causa_impago': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'