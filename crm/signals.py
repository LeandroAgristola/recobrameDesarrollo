from django.db.models.signals import post_save
from django.dispatch import receiver
from empresas.models import Empresa
from .models import CRMConfig

@receiver(post_save, sender=Empresa)
def gestionar_crm_empresa(sender, instance, created, **kwargs):
    if created:
        # 1. Verificamos si usa SeQura Manual
        # Buscamos en el string de tipos_impagos (ej: "STRIPE, SEQURA_MANUAL")
        metodos = [m.strip() for m in instance.tipos_impagos.split(',')]
        
        # 2. El CRM se crea SIEMPRE, pero 'tiene_cedidos' depende de SM
        usa_sequra_manual = 'SEQURA_MANUAL' in metodos
        
        CRMConfig.objects.create(
            empresa=instance,
            tiene_cedidos=usa_sequra_manual
        )