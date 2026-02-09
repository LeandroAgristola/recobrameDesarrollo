from django import forms
from .models import Expediente
from empresas.models import EsquemaComision

class ExpedienteForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            'agente', 'tipo_producto', 
            'deudor_nombre', 'deudor_telefono', 
            'deudor_dni', 'deudor_email', # <--- RESTAURADOS
            'monto_original', 'cuotas_totales', 
            'fecha_compra', 'fecha_impago'
        ]
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'type': 'date'}),
            'fecha_impago': forms.DateInput(attrs={'type': 'date'}),
            'agente': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        # Tipo de producto dinámico según empresa
        if empresa:
            tipos = EsquemaComision.objects.filter(empresa=empresa).values_list('tipo_producto', 'tipo_producto').distinct()
            self.fields['tipo_producto'] = forms.ChoiceField(
                choices=tipos, 
                widget=forms.Select(attrs={'class': 'form-select'})
            )