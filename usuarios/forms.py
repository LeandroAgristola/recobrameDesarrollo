from django import forms
from django.contrib.auth.models import User
from empresas.models import Empresa
from .models import Perfil

class NuevoStaffForm(forms.Form):
    nombre = forms.CharField(max_length=50, required=True)
    apellido = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    rol = forms.ChoiceField(choices=[
        ('ADMIN', 'Administrador'), 
        ('AGENTE', 'Agente de Recobro'), 
        ('CONTABLE', 'Contable'), 
        ('ABOGADO', 'Abogado')
    ])
    telefono = forms.CharField(max_length=20, required=False)
    dni_nie = forms.CharField(max_length=20, required=False)
    netelip_ext = forms.CharField(max_length=20, required=False)
    mercateli_id = forms.CharField(max_length=50, required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email

class NuevoClienteForm(forms.Form):
    nombre = forms.CharField(max_length=50, required=True)
    apellido = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.filter(is_active=True), 
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select select2-empresas'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email