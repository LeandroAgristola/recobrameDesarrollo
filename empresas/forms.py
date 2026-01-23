from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
import re
from .models import Empresa, TramoComision

OPCIONES_IMPAGOS = [
    ('SEQURA_HOTMART', 'SeQura Hotmart'),
    ('SEQURA_MANUAL', 'SeQura Manual'),
    ('SEQURA_COPECART', 'SeQura Copecart'),
    ('AUTO_STRIPE', 'Auto Stripe'),
    ('AUTOFINANCIACION', 'Autofinanciación'),
]

class EmpresaForm(forms.ModelForm):
    tipos_impagos = forms.MultipleChoiceField(
        choices=OPCIONES_IMPAGOS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Tipos de Impagos",
        error_messages={'required': 'Debe seleccionar al menos un tipo de impago.'}
    )

    class Meta:
        model = Empresa
        fields = [
            'nombre', 'razon_social', 'cif_nif', 'fecha_alta', 
            'persona_contacto', 'telefono_contacto',
            'email_contacto', 'direccion', 
            'contacto_incidencias', 'email_incidencias', 
            'datos_bancarios', 'tipos_impagos', 'cursos', 'notas',
            'contrato_colaboracion', 'contrato_cesion',
            'tipo_comision', 'porcentaje_unico'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cif_nif': forms.TextInput(attrs={'class': 'form-control'}),
            
            # --- CORRECCIÓN AQUÍ ---
            # Agregamos format='%Y-%m-%d' para que el input type="date" lea bien el valor
            'fecha_alta': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            
            'persona_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_incidencias': forms.TextInput(attrs={'class': 'form-control'}),
            'email_incidencias': forms.EmailInput(attrs={'class': 'form-control'}),
            'datos_bancarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cursos': forms.Textarea(attrs={'class': 'form-control', 'style': 'height: 150px;'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tipo_comision': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_comision'}),
            'porcentaje_unico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contrato_colaboracion': forms.FileInput(attrs={'class': 'form-control'}),
            'contrato_cesion': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_persona_contacto(self):
        nombre = self.cleaned_data.get('persona_contacto')
        if nombre:
            if not re.match(r'^[a-zA-Z\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
                raise ValidationError("El nombre de contacto solo puede contener letras.")
        return nombre

    def clean_tipos_impagos(self):
        data = self.cleaned_data['tipos_impagos']
        if not data:
            raise ValidationError("Seleccione al menos una opción.")
        return ', '.join(data)

    def clean(self):
        cleaned_data = super().clean()
        
        c_incidencias = cleaned_data.get('contacto_incidencias')
        e_incidencias = cleaned_data.get('email_incidencias')
        
        if not c_incidencias and not e_incidencias:
            msg = "Debe indicar un Contacto o un Email para incidencias (o ambos)."
            self.add_error('contacto_incidencias', msg)
            self.add_error('email_incidencias', msg)

        tipo_com = cleaned_data.get('tipo_comision')
        pct_unico = cleaned_data.get('porcentaje_unico')
        
        if tipo_com == 'FIJO':
            if pct_unico is None or pct_unico == '':
                self.add_error('porcentaje_unico', "Si la comisión es Fija, debe indicar el porcentaje.")
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contacto_incidencias'].required = False
        self.fields['email_incidencias'].required = False
        self.fields['nombre'].required = True
        self.fields['razon_social'].required = True
        
        if self.instance and self.instance.pk and self.instance.tipos_impagos:
            self.initial['tipos_impagos'] = self.instance.tipos_impagos.split(', ')

# (El FormSet de Tramos queda igual, no hace falta tocarlo)
class TramoComisionFormSetBase(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        tramos = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                minimo = form.cleaned_data.get('monto_minimo')
                tramos.append(minimo)
        if len(tramos) != len(set(tramos)):
             raise ValidationError("No puede haber dos tramos que empiecen en el mismo monto.")

TramoComisionFormSet = inlineformset_factory(
    Empresa, 
    TramoComision,
    formset=TramoComisionFormSetBase,
    fields=['monto_minimo', 'monto_maximo', 'porcentaje'],
    extra=1,
    can_delete=True,
    widgets={
        'monto_minimo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Desde (€)'}),
        'monto_maximo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hasta (€)'}),
        'porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '%', 'step': '0.01'}),
    }
)