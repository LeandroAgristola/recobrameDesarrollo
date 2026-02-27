from django import forms
from django.contrib.auth.models import User
from empresas.models import Empresa
from .models import Perfil

class NuevoStaffForm(forms.Form):
    nombre = forms.CharField(max_length=50, required=True)
    apellido = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    rol = forms.ChoiceField(
        choices=[
            ('ADMIN', 'Administrador'), 
            ('AGENTE', 'Agente de Recobro'), 
            ('CONTABLE', 'Contable'), 
            ('ABOGADO', 'Abogado')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    telefono = forms.CharField(max_length=20, required=False)
    dni_nie = forms.CharField(max_length=20, required=False)
    netelip_ext = forms.CharField(max_length=20, required=False)
    netelip_number = forms.CharField(max_length=20, required=False)
    netelip_user = forms.CharField(max_length=100, required=False)
    netelip_pass = forms.CharField(max_length=100, required=False)
    netelip_server = forms.CharField(max_length=100, required=False)
    mercateli_id = forms.CharField(max_length=50, required=False)
    mercateli_despacho = forms.CharField(max_length=100, required=False)
    foto_perfil = forms.ImageField(required=False)
    contrato_colaboracion = forms.FileField(required=False)
    fecha_alta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está en uso.")
        return email

class EditarStaffForm(forms.Form):
    perfil_id = forms.IntegerField(widget=forms.HiddenInput())
    nombre = forms.CharField(max_length=50, required=True)
    apellido = forms.CharField(max_length=50, required=True)
    rol = forms.ChoiceField(
        choices=[
            ('ADMIN', 'Administrador'), 
            ('AGENTE', 'Agente de Recobro'), 
            ('CONTABLE', 'Contable'), 
            ('ABOGADO', 'Abogado')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    telefono = forms.CharField(max_length=20, required=False)
    dni_nie = forms.CharField(max_length=20, required=False)
    netelip_ext = forms.CharField(max_length=20, required=False)
    netelip_number = forms.CharField(max_length=20, required=False)
    netelip_user = forms.CharField(max_length=100, required=False)
    netelip_pass = forms.CharField(max_length=100, required=False)
    netelip_server = forms.CharField(max_length=100, required=False)
    mercateli_id = forms.CharField(max_length=50, required=False)
    mercateli_despacho = forms.CharField(max_length=100, required=False)
    foto_perfil = forms.ImageField(required=False)
    contrato_colaboracion = forms.FileField(required=False)

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