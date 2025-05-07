# core/management/commands/populate_usuarios_exemplo.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Aluno, Professor


class Command(BaseCommand):
    help = 'Cria usuários de exemplo para cada nível de acesso'

    def handle(self, *args, **kwargs):
        # Dados dos usuários de exemplo
        usuarios = [
            {'username': 'aluno1', 'password': 'aluno123', 'grupo': 'aluno', 'email': 'aluno1@escola.com'},
            {'username': 'prof1', 'password': 'prof123', 'grupo': 'professor', 'email': 'prof1@escola.com'},
            {'username': 'diretor1', 'password': 'diretor123', 'grupo': 'diretor', 'email': 'diretor1@escola.com'},
            {'username': 'diretor_adm1', 'password': 'diradm123', 'grupo': 'diretor_admin',
             'email': 'diradm1@escola.com'},
            {'username': 'admin', 'password': 'admin123', 'grupo': 'administrador', 'email': 'admin@escola.com'},
        ]

        for user_data in usuarios:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']}
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                grupo = Group.objects.get(name=user_data['grupo'])
                user.groups.add(grupo)

                # Criar perfil específico
                if user_data['grupo'] == 'aluno':
                    Aluno.objects.create(usuario=user, nome=f"Aluno {user_data['username']}")
                elif user_data['grupo'] == 'professor':
                    Professor.objects.create(usuario=user, nome=f"Professor {user_data['username']}")

                self.stdout.write(self.style.SUCCESS(f'Usuário {user_data["username"]} criado com sucesso'))
            else:
                self.stdout.write(self.style.WARNING(f'Usuário {user_data["username"]} já existe'))

        self.stdout.write(self.style.SUCCESS('População de usuários de exemplo concluída!'))