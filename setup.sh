#!/bin/bash

# Instala dependências
pip install -r requirements.txt

# Aplica migrações
python manage.py migrate

# Configura o admin interface
python manage.py setup_admin

# Coleta arquivos estáticos
python manage.py collectstatic --noinput

echo "✅ Configuração inicial concluída com sucesso!"