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
    # Validamos que la fecha de impago no sea anterior a la fecha de compra
    def clean(self):
        cleaned_data = super().clean()
        fecha_compra = cleaned_data.get("fecha_compra")
        fecha_impago = cleaned_data.get("fecha_impago")

        # SOLO VALIDAMOS SI AMBAS FECHAS EXISTEN
        if fecha_compra and fecha_impago:
            if fecha_compra > fecha_impago:
                self.add_error('fecha_impago', "La fecha de impago no puede ser anterior a la fecha de compra.")
        
        return cleaned_data

# Formulario para registrar un pago, con validación del monto y método de pago
class PagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.expediente = kwargs.pop('expediente', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = RegistroPago
        fields = ['monto', 'descuento', 'fecha_pago', 'metodo_pago', 'comprobante']

    # Validamos que el monto no exceda la deuda actual del expediente (con una pequeña tolerancia por redondeos)
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if self.expediente:
            # Tolerancia de 0.01 por posibles redondeos decimales
            if monto > (self.expediente.monto_actual + Decimal('0.01')):
                raise forms.ValidationError(f"El monto excede la deuda actual ({self.expediente.monto_actual}€).")
        return monto

    # Validamos que el método de pago sea 'Transferencia' o el tipo de producto del expediente
    def clean_metodo_pago(self):
            metodo = self.cleaned_data.get('metodo_pago')
            
            if self.expediente:
                permitidos = ['TRANSFERENCIA']
                
                if self.expediente.tipo_producto:
                    permitidos.append(self.expediente.tipo_producto)
                
                if metodo not in permitidos:
                    nombre_metodo = self.expediente.get_tipo_producto_display()
                    raise forms.ValidationError(
                        f"Método inválido. Solo se admite 'Transferencia' o '{nombre_metodo}'."
                    )
                            
            return metodo
    
    #valor negativo o nulo se interpreta como sin descuento
    def clean_descuento(self):
        descuento = self.cleaned_data.get('descuento')
        if not descuento or descuento < 0:
            return Decimal('0.00')
        return descuento