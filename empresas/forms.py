from django import forms
from django.forms import inlineformset_factory
from .models import Empresa, EsquemaComision, TramoComision, OPCIONES_IMPAGOS

# 1. FORMULARIO PRINCIPAL
class EmpresaForm(forms.ModelForm):
    tipos_impagos = forms.MultipleChoiceField(
        choices=OPCIONES_IMPAGOS,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Tipos de Impagos"
    )

    class Meta:
        model = Empresa
        fields = [
            'nombre', 'razon_social', 'cif_nif', 'fecha_alta', 
            'persona_contacto', 'telefono_contacto', 'email_contacto', 
            'direccion', 'contacto_incidencias', 'email_incidencias', 
            'datos_bancarios', 'tipos_impagos', 'cursos', 'notas',
            'contrato_colaboracion', 'contrato_cesion'
        ]
        # ESTA PARTE ES CRUCIAL PARA EL ESTILO VISUAL:
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cif_nif': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_alta': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'persona_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_incidencias': forms.TextInput(attrs={'class': 'form-control'}),
            'email_incidencias': forms.EmailInput(attrs={'class': 'form-control'}),
            'datos_bancarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cursos': forms.Textarea(attrs={'class': 'form-control', 'style': 'height: 150px;'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'contrato_colaboracion': forms.FileInput(attrs={'class': 'form-control'}),
            'contrato_cesion': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tipos_impagos:
            self.initial['tipos_impagos'] = self.instance.tipos_impagos.split(', ')

    def clean_tipos_impagos(self):
        return ', '.join(self.cleaned_data['tipos_impagos'])

# 2. FORMULARIO DE ESQUEMA (Configuración posterior)
class EsquemaComisionForm(forms.ModelForm):
    class Meta:
        model = EsquemaComision
        fields = ['tipo_caso', 'tipo_producto', 'modalidad', 'porcentaje_fijo']
        widgets = {
            'tipo_caso': forms.Select(attrs={'class': 'form-select'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-select'}),
            'modalidad': forms.Select(attrs={'class': 'form-select', 'id': 'id_modalidad'}),
            # QUITAR EL REQUIRED AQUÍ
            'porcentaje_fijo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '%'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos el argumento 'empresa' si viene
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Lógica de filtrado
        if empresa and empresa.tipos_impagos:
            # Convertimos el string "A, B, C" en lista ['A', 'B', 'C']
            codigos_seleccionados = [codigo.strip() for codigo in empresa.tipos_impagos.split(',')]
            
            # Filtramos las opciones originales de OPCIONES_IMPAGOS
            # Solo dejamos las que estén en la lista de seleccionados
            opciones_filtradas = [
                (codigo, nombre) 
                for codigo, nombre in OPCIONES_IMPAGOS 
                if codigo in codigos_seleccionados
            ]
            
            # Asignamos las nuevas opciones al campo
            self.fields['tipo_producto'].choices = [('', '---------')] + opciones_filtradas
        elif empresa:
            # Si la empresa no tiene tipos seleccionados, vaciamos el select (o dejamos solo vacío)
            self.fields['tipo_producto'].choices = [('', '---------')]
            
# 3. FORMSET TRAMOS
TramoFormSet = inlineformset_factory(
    EsquemaComision, TramoComision,
    fields=['monto_minimo', 'monto_maximo', 'porcentaje'],
    extra=1, can_delete=True,
    widgets={
        # QUITAR EL REQUIRED AQUÍ TAMBIÉN
        'monto_minimo': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        'monto_maximo': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        'porcentaje': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
    }
)