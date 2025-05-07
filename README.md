Sistema Escolar - Configuração do Painel Administrativo
📦 Pré-requisitos

Python 3.8+
Django 4.0+
Git instalado

🚀 Instalação Inicial
1. Clone o repositório
git clone https://github.com/seu-usuario/seu-projeto.git
cd seu-projeto

2. Configure o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

3. Instale as dependências
pip install -r requirements.txt

🔧 Configuração do Admin Interface
1. Adicione ao settings.py
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',  # Necessário para admin_interface
    'django.contrib.admin',
    # ... outros apps ...
]

ADMIN_INTERFACE_CONFIG = {
    'name': 'Sistema Escolar',
    'default_theme': {
        'css_header_background_color': '#2A3F54',
        'css_header_text_color': '#FFFFFF',
        'css_module_background_color': '#FFFFFF',
        'css_module_text_color': '#333333',
        'css_module_link_color': '#2A3F54',
        'list_filter_dropdown': True,
        'related_modal_active': True,
        'css_generic_link_color': '#2A3F54',
        'css_save_button_background_color': '#5CB85C',
        'css_delete_button_background_color': '#D9534F',
    }
}

2. Crie o comando de configuração
Crie o arquivo core/management/commands/setup_admin.py:
from django.core.management.base import BaseCommand
from admin_interface.models import Theme
from django.conf import settings

class Command(BaseCommand):
    help = 'Configura o tema padrão do admin'

    def handle(self, *args, **options):
        config = settings.ADMIN_INTERFACE_CONFIG
        
        theme, created = Theme.objects.update_or_create(
            name='Default',
            defaults={
                'active': True,
                'title': config.get('name', 'Admin'),
                'logo': config.get('logo', ''),
                **config.get('default_theme', {})
            }
        )
        
        status = 'criado' if created else 'atualizado'
        self.stdout.write(self.style.SUCCESS(f'Tema {status} com sucesso!'))

🛠️ Script de Instalação Automática
Para Linux/Mac (setup.sh)
#!/bin/bash

# Ativa o ambiente virtual
source venv/bin/activate

# Instala dependências
pip install -r requirements.txt

# Aplica migrações
python manage.py migrate

# Configura o tema admin
python manage.py setup_admin

# Coleta arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Configuração concluída com sucesso!"

Para Windows (setup.bat)
@echo off

:: Ativa o ambiente virtual
call venv\Scripts\activate

:: Instala dependências
pip install -r requirements.txt

:: Aplica migrações
python manage.py migrate

:: Configura o tema admin
python manage.py setup_admin

:: Coleta arquivos estáticos
python manage.py collectstatic --noinput

echo ✅ Configuração concluída com sucesso!
pause

Dê permissão de execução (Linux/Mac):
chmod +x setup.sh

🔄 Fluxo de Trabalho para Novas Máquinas

Clone o repositório

Execute o script de instalação:
./setup.sh  # Linux/Mac
setup.bat   # Windows


O sistema estará pronto com:

Tema admin configurado
Banco de dados migrado
Arquivos estáticos coletados



🎨 Personalização do Tema
Para modificar o tema após instalação:

Acesse /admin/admin_interface/theme/
Ou edite o ADMIN_INTERFACE_CONFIG no settings.py
Execute novamente para aplicar:python manage.py setup_admin



📝 Modelo de requirements.txt
Certifique-se que seu arquivo inclua:
django-admin-interface==3.0.0
django-colorfield==0.8.0

⁉️ Solução de Problemas
Se o tema não aparecer corretamente:

Verifique se os apps estão na ordem correta no INSTALLED_APPS
Confira se todas as migrações foram aplicadas:python manage.py showmigrations


Execute o comando de setup manualmente:python manage.py setup_admin



🌟 Dicas Extras

Para um tema dark mode, modifique as cores no ADMIN_INTERFACE_CONFIG
Adicione seu logo em static/images/logo.png e referencie no settings:ADMIN_INTERFACE_CONFIG = {
    'logo': 'images/logo.png',
    # ... outras configs
}



Este README fornece todas as instruções necessárias para configurar o ambiente do zero, garantindo consistência visual em todas as instalações do projeto.
