from django.db.models.signals import post_save
from django.dispatch import receiver
from empresas.models import Empresa
from .models import CRMConfig

@receiver(post_save, sender=Empresa)
def gestionar_crm_empresa(sender, instance, created, **kwargs):
    if created:
        metodos = [m.strip() for m in instance.tipos_impagos.split(',')]
        
        # Lista de productos que disparan la pestaña de Cedidos
        PRODUCTOS_CON_CESION = ['SEQURA_MANUAL', 'AUTOFINANCIADO']
        
        # El CRM se crea siempre, pero 'tiene_cedidos' ahora es más inclusivo
        activar_cedidos = any(p in metodos for p in PRODUCTOS_CON_CESION)
        
        CRMConfig.objects.create(
            empresa=instance,
            tiene_cedidos=activar_cedidos
        )