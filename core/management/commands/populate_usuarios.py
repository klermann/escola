from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import *

class Command(BaseCommand):
    help = 'Popula o banco de dados com grupos e permissões padrão para o sistema escolar'

    def handle(self, *args, **kwargs):
        # Grupos principais
        grupos = {
            'aluno': 'Usuários com perfil de aluno',
            'professor': 'Usuários com perfil de professor',
            'diretor': 'Usuários com perfil de diretor',
            'diretor_admin': 'Usuários com perfil de diretor administrativo',
            'administrador': 'Usuários com perfil de administrador do sistema'
        }

        # Permissões específicas para cada modelo (ajuste conforme seus modelos)
        modelos_permissões = {
            'aluno': ['view', 'change'],  # Alunos podem ver e editar apenas seus dados
            'boletim': ['view'],
            'avaliacao': ['view'],
            'frequencia': ['view'],
            'turma': ['view'],
            'disciplina': ['view'],
        }

        permissoes_especiais = {
            'professor': {
                'avaliacao': ['add', 'change', 'view'],
                'frequencia': ['add', 'change', 'view'],
                'turma': ['view'],
                'disciplina': ['view'],
            },
            'diretor': {
                'aluno': ['view', 'change', 'add'],
                'professor': ['view', 'change', 'add'],
                'boletim': ['view', 'change'],
                'avaliacao': ['view', 'change'],
                'frequencia': ['view', 'change'],
                'turma': ['view', 'change', 'add'],
                'disciplina': ['view', 'change', 'add'],
            },
            'diretor_admin': {
                'aluno': ['view', 'change', 'add', 'delete'],
                'professor': ['view', 'change', 'add', 'delete'],
                'boletim': ['view', 'change', 'delete'],
                'avaliacao': ['view', 'change', 'delete'],
                'frequencia': ['view', 'change', 'delete'],
                'turma': ['view', 'change', 'add', 'delete'],
                'disciplina': ['view', 'change', 'add', 'delete'],
            },
            'administrador': {
                # Todos os direitos
            }
        }

        # Criar grupos
        for nome, descricao in grupos.items():
            grupo, created = Group.objects.get_or_create(name=nome)
            grupo.description = descricao
            grupo.save()
            self.stdout.write(self.style.SUCCESS(f'Grupo "{nome}" criado/atualizado'))

            # Adicionar permissões básicas para alunos
            if nome == 'aluno':
                for modelo, perms in modelos_permissões.items():
                    for perm in perms:
                        codename = f'{perm}_{modelo}'
                        try:
                            perm_obj = Permission.objects.get(codename=codename)
                            grupo.permissions.add(perm_obj)
                        except Permission.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Permissão "{codename}" não encontrada'))

            # Adicionar permissões especiais para outros grupos
            if nome in permissoes_especiais:
                for modelo, perms in permissoes_especiais[nome].items():
                    for perm in perms:
                        codename = f'{perm}_{modelo}'
                        try:
                            perm_obj = Permission.objects.get(codename=codename)
                            grupo.permissions.add(perm_obj)
                        except Permission.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Permissão "{codename}" não encontrada'))

                # Administradores têm todas as permissões
                if nome == 'administrador':
                    grupo.permissions.set(Permission.objects.all())

        self.stdout.write(self.style.SUCCESS('População de grupos e permissões concluída com sucesso!'))