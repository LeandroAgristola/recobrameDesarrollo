from django import forms
from .models import Expediente
from empresas.models import EsquemaComision

class ExpedienteForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            'agente', 'tipo_producto', 
            'deudor_nombre', 'deudor_telefono', 
            'deudor_dni', 'deudor_email', 
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

        # HACER OPCIONALES LOS CAMPOS EN EL FORMULARIO
        self.fields['cuotas_totales'].required = False
        self.fields['fecha_compra'].required = False
        self.fields['fecha_impago'].required = False

        if empresa:
            tipos = EsquemaComision.objects.filter(empresa=empresa).values_list('tipo_producto', 'tipo_producto').distinct()
            self.fields['tipo_producto'] = forms.ChoiceField(
                choices=tipos, 
                widget=forms.Select(attrs={'class': 'form-select'})
            )

    def clean(self):
        cleaned_data = super().clean()
        fecha_compra = cleaned_data.get("fecha_compra")
        fecha_impago = cleaned_data.get("fecha_impago")

        # SOLO VALIDAMOS SI AMBAS FECHAS EXISTEN
        if fecha_compra and fecha_impago:
            if fecha_compra > fecha_impago:
                self.add_error('fecha_impago', "La fecha de impago no puede ser anterior a la fecha de compra.")
        
        return cleaned_data