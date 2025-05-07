@echo off

pip install -r requirements.txt
python manage.py migrate
python manage.py setup_admin
python manage.py collectstatic --noinput

echo ✅ Configuração inicial concluída com sucesso!
pause