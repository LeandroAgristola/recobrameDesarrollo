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

        if empresa and empresa.tipos_impagos:
            tipos = [t.strip() for t in empresa.tipos_impagos.split(',')]
            
            # NUEVO: Filtramos 'TRANSFERENCIA' para que no sea un método de financiación
            tipos = [t for t in tipos if t != 'TRANSFERENCIA']

            from empresas.models import OPCIONES_IMPAGOS
            nombres_dict = dict(OPCIONES_IMPAGOS)
            opciones = [(cod, nombres_dict.get(cod, cod)) for cod in tipos]
            
            self.fields['tipo_producto'].choices = opciones
            
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
    class Meta:
        model = RegistroPago
        fields = ['monto', 'descuento', 'metodo_pago', 'comprobante']

    def __init__(self, *args, **kwargs):
        self.expediente = kwargs.pop('expediente', None)
        super().__init__(*args, **kwargs)
        # Hacemos el descuento opcional en un único bloque __init__
        self.fields['descuento'].required = False

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is None or monto <= 0:
            raise forms.ValidationError("El monto ingresado debe ser mayor a 0.")
        return monto
    
    def clean_descuento(self):
        descuento = self.cleaned_data.get('descuento')
        # Si llega vacío (None) o es negativo, forzamos un 0.00 matemático
        if descuento is None or descuento < 0:
            return Decimal('0.00')
        return descuento