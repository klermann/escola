from django.core.management.base import BaseCommand
from admin_interface.models import Theme

class Command(BaseCommand):
    help = 'Configura o admin_interface como tema padrão do Django Admin'

    def handle(self, *args, **options):
        from django.conf import settings
        default_theme = settings.ADMIN_INTERFACE_CONFIG.get('default_theme', {})

        theme, created = Theme.objects.update_or_create(
            name='Default',
            defaults={
                'active': True,
                'show_logo': False,  # Desativa o logo
                'title': settings.ADMIN_INTERFACE_CONFIG.get('name', 'Admin'),
                'logo': 'static/images/logo-escola.png',
                'css_header_background_color': '#2A3F54',  # Azul escuro
                'css_header_text_color': '#FFFFFF',        # Branco
                'css_header_link_color': '#FFFFFF',
                'css_header_link_hover_color': '#F5DD5D',
                'css_module_background_color': '#FFFFFF',
                'css_module_text_color': '#333333',
                'css_module_link_color': '#2A3F54',
                'css_module_link_hover_color': '#1C2E3F',
                'css_module_rounded_corners': True,
                'css_generic_link_color': '#2A3F54',
                'css_generic_link_hover_color': '#1C2E3F',
                'css_save_button_background_color': '#5CB85C',
                'css_save_button_background_hover_color': '#449D44',
                'css_delete_button_background_color': '#D9534F',
                'css_delete_button_background_hover_color': '#C9302C',
                'css': '',
                'related_modal_active': True,
                'related_modal_background_color': '#000000',
                'related_modal_background_opacity': 0.3,
                'related_modal_rounded_corners': True,
                'related_modal_close_button_visible': True,
                'list_filter_dropdown': True,
                'recent_actions_visible': True,
                'favicon': '',
                'env_name': 'AMBIENTE DE PRODUÇÃO',
                'env_color': '#E74C3C',  # Vermelho (pode mudar para #2ECC71 em desenvolvimento)
                'env_visible_in_header': True,
                'env_visible_in_favicon': True,
                **default_theme
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✅ Tema admin_interface configurado com sucesso!'))
        else:
            theme.active = True
            theme.save()
            self.stdout.write(self.style.SUCCESS('ℹ️ Tema admin_interface já existia e foi ativado'))