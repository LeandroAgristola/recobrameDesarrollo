from django import forms
from .models import Empresa, TramoComision

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nombre', 'razon_social', 'cif_nif', 'direccion', 'fecha_alta',
            'contacto_incidencias', 'email_incidencias', 'datos_bancarios',
            'tipos_impagos', 'cursos', 'notas',
            'contrato_colaboracion', 'contrato_cesion',
            'tipo_comision', 'porcentaje_unico'
        ]
        widgets = {
            'fecha_alta': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'datos_bancarios': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cif_nif': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_incidencias': forms.TextInput(attrs={'class': 'form-control'}),
            'email_incidencias': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipos_impagos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'cursos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'tipo_comision': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_comision'}),
            'porcentaje_unico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'contrato_colaboracion': forms.FileInput(attrs={'class': 'form-control'}),
            'contrato_cesion': forms.FileInput(attrs={'class': 'form-control'}),
        }