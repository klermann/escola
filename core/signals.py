from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from admin_interface.models import Theme

@receiver(post_migrate)
def setup_default_theme(sender, **kwargs):
    if sender.name == 'admin_interface':
        default_theme = settings.ADMIN_INTERFACE_CONFIG.get('default_theme', {})
        Theme.objects.update_or_create(
            name='Default',
            defaults={
                'active': True,
                'title': settings.ADMIN_INTERFACE_CONFIG.get('name', 'Admin'),
                **default_theme
            }
        )