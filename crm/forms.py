from django import forms
from .models import Expediente, RegistroPago
from empresas.models import EsquemaComision
from decimal import Decimal

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
    
class PagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.expediente = kwargs.pop('expediente', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = RegistroPago
        fields = ['monto', 'fecha_pago', 'metodo_pago', 'comprobante']

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if self.expediente:
            # Tolerancia de 0.01 por posibles redondeos decimales
            if monto > (self.expediente.monto_actual + Decimal('0.01')):
                raise forms.ValidationError(f"El monto excede la deuda actual ({self.expediente.monto_actual}€).")
        return monto

    # === NUEVA VALIDACIÓN PARA MÉTODOS DE PAGO ===
    def clean_metodo_pago(self):
        metodo = self.cleaned_data.get('metodo_pago')
        
        if self.expediente:
            # 1. Reglas para CEDIDOS
            if self.expediente.estado == 'CEDIDO':
                if metodo not in ['TRANSFERENCIA', 'SEQURA_PASS']:
                    raise forms.ValidationError(
                        f"El método '{metodo}' no está admitido para expedientes en estado Cedido."
                    )
            
            # 2. Reglas para IMPAGOS (Solo Transferencia o los configurados en la Empresa)
            else:
                if metodo != 'TRANSFERENCIA':
                    tipos_admitidos = self.expediente.empresa.tipos_impagos or ""
                    
                    if metodo not in tipos_admitidos:
                        raise forms.ValidationError(
                            f"La empresa no tiene habilitado el método de pago: {metodo}."
                        )
                        
        return metodo