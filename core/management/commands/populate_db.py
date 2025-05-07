import os
import django
import sys
from django.db import transaction
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand as ConfigureThemeCommand

# Configuração para funcionar como script independente
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diario_classe.settings')
    django.setup()
except:
    pass  # Já configurado se executado como comando Django

from core.models import (
    Escola, Turma, Aluno, Disciplina, Bimestre,
    Avaliacao, Frequencia, PeriodoLetivo, DiaLetivo, Calendario,
    DiretoriaEnsino, Diretor, Professor
)

# Import models from site_admin app
from site_admin.models import (
    AboutEducenter, AboutUs, FeatureBlock, FeatureItem, HeroContent
)


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de exemplo para o sistema escolar'

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Iniciando a população do banco de dados...'))

            # Configuração do Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diario_classe.settings')
            django.setup()

            # Funções de população
            from core.management.commands.populate_db import populate_database

            # Executa a população
            with transaction.atomic():
                populate_database(self.style)

            self.stdout.write(self.style.SUCCESS('✅ Banco de dados populado com sucesso!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao popular banco de dados: {str(e)}'))
            raise e


def generate_ra():
    """Gera um RA válido no formato 0000 + 9 dígitos + 1 dígito/X"""
    numeros = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    digito = random.choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'X'])
    return f'0000{numeros}{digito}'


def random_date(start_date, end_date):
    """Gera uma data aleatória entre dois intervalos"""
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return start_date + timedelta(days=random_days)


def generate_cpf():
    """Gera um CPF válido"""
    cpf = [random.randint(0, 9) for _ in range(9)]
    soma = sum((10 - i) * num for i, num in enumerate(cpf))
    d1 = 11 - (soma % 11)
    if d1 >= 10:
        d1 = 0
    cpf.append(d1)
    soma = sum((11 - i) * num for i, num in enumerate(cpf))
    d2 = 11 - (soma % 11)
    if d2 >= 10:
        d2 = 0
    cpf.append(d2)
    return f"{''.join(map(str, cpf[:3]))}.{''.join(map(str, cpf[3:6]))}.{''.join(map(str, cpf[6:9]))}-{cpf[9]}{cpf[10]}"


def create_user_groups():
    """Cria grupos de usuários com permissões específicas"""
    grupos = {
        'aluno': {
            'description': 'Usuários com perfil de aluno',
            'permissions': [
                ('view_boletim', 'boletim'),
                ('view_avaliacao', 'avaliacao'),
                ('view_frequencia', 'frequencia'),
            ]
        },
        'professor': {
            'description': 'Usuários com perfil de professor',
            'permissions': [
                ('add_avaliacao', 'avaliacao'),
                ('change_avaliacao', 'avaliacao'),
                ('view_avaliacao', 'avaliacao'),
                ('add_frequencia', 'frequencia'),
                ('change_frequencia', 'frequencia'),
                ('view_frequencia', 'frequencia'),
                ('view_turma', 'turma'),
            ]
        },
        'diretor': {
            'description': 'Usuários com perfil de diretor',
            'permissions': [
                ('view_aluno', 'aluno'),
                ('add_aluno', 'aluno'),
                ('change_aluno', 'aluno'),
                ('view_professor', 'professor'),
                ('add_professor', 'professor'),
                ('change_professor', 'professor'),
                ('view_boletim', 'boletim'),
                ('change_boletim', 'boletim'),
                ('view_avaliacao', 'avaliacao'),
                ('change_avaliacao', 'avaliacao'),
                ('view_frequencia', 'frequencia'),
                ('change_frequencia', 'frequencia'),
                ('view_turma', 'turma'),
                ('change_turma', 'turma'),
                ('add_turma', 'turma'),
                ('view_disciplina', 'disciplina'),
                ('change_disciplina', 'disciplina'),
                ('add_disciplina', 'disciplina'),
            ]
        },
        'diretor_admin': {
            'description': 'Usuários com perfil de diretor administrativo',
            'permissions': [
                ('view_aluno', 'aluno'),
                ('add_aluno', 'aluno'),
                ('change_aluno', 'aluno'),
                ('delete_aluno', 'aluno'),
                ('view_professor', 'professor'),
                ('add_professor', 'professor'),
                ('change_professor', 'professor'),
                ('delete_professor', 'professor'),
                ('view_boletim', 'boletim'),
                ('change_boletim', 'boletim'),
                ('delete_boletim', 'boletim'),
                ('view_avaliacao', 'avaliacao'),
                ('change_avaliacao', 'avaliacao'),
                ('delete_avaliacao', 'avaliacao'),
                ('view_frequencia', 'frequencia'),
                ('change_frequencia', 'frequencia'),
                ('delete_frequencia', 'frequencia'),
                ('view_turma', 'turma'),
                ('change_turma', 'turma'),
                ('add_turma', 'turma'),
                ('delete_turma', 'turma'),
                ('view_disciplina', 'disciplina'),
                ('change_disciplina', 'disciplina'),
                ('add_disciplina', 'disciplina'),
                ('delete_disciplina', 'disciplina'),
            ]
        },
        'administrador': {
            'description': 'Usuários com perfil de administrador do sistema',
            'permissions': 'all'  # Todas as permissões
        }
    }

    for group_name, group_data in grupos.items():
        group, created = Group.objects.get_or_create(
            name=group_name,
            #defaults={'description': group_data['description']}
        )

        if group_data['permissions'] == 'all':
            group.permissions.set(Permission.objects.all())
        else:
            for codename, model in group_data['permissions']:
                try:
                    content_type = ContentType.objects.get(model=model)
                    permission = Permission.objects.get(
                        content_type=content_type,
                        codename=codename
                    )
                    group.permissions.add(permission)
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    continue


def create_example_users():
    """Cria usuários de exemplo para cada grupo"""
    users_data = [
        {
            'username': 'aluno',
            'password': 'aluno123',
            'email': 'aluno1@escola.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'groups': ['aluno']
        },
        {
            'username': 'prof',
            'password': 'prof123',
            'email': 'prof1@escola.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'groups': ['professor']
        },
        {
            'username': 'diretor1',
            'password': 'diretor123',
            'email': 'diretor1@escola.com',
            'first_name': 'Carlos',
            'last_name': 'Oliveira',
            'groups': ['diretor']
        },
        {
            'username': 'diradm',
            'password': 'diradm123',
            'email': 'diradm1@escola.com',
            'first_name': 'Ana',
            'last_name': 'Ferreira',
            'groups': ['diretor_admin']
        },
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@escola.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'groups': ['administrador'],
            'is_staff': True,
            'is_superuser': True
        }
    ]

    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_staff': user_data.get('is_staff', False),
                'is_superuser': user_data.get('is_superuser', False)
            }
        )

        if created:
            user.set_password(user_data['password'])
            user.save()
            for group_name in user_data['groups']:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)


def populate_calendario():
    """Popula a tabela Calendario com dados de exemplo"""
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    for mes in meses:
        dias_no_mes = 31 if mes in ['Janeiro', 'Março', 'Maio', 'Julho', 'Agosto', 'Outubro', 'Dezembro'] else 30
        if mes == 'Fevereiro':
            dias_no_mes = 28
        for dia in range(1, dias_no_mes + 1):
            status = None
            if random.random() < 0.2:
                status = random.choice(['feriado', 'recesso', 'evento'])
            Calendario.objects.get_or_create(
                mes=mes,
                dia=dia,
                defaults={'status': status}
            )


def populate_about_edu_center():
    """Popula a tabela site_admin_abouteducenter com dados de exemplo"""
    about_data = {
        'title': 'Sobre o Centro Educacional',
        'content': (
            'O Centro Educacional é dedicado a oferecer uma educação de qualidade, '
            'promovendo o desenvolvimento integral dos alunos. Nossa abordagem combina '
            'excelência acadêmica com valores éticos e sociais, preparando os estudantes '
            'para os desafios do futuro.'
        ),
        'is_active': True
    }
    about, created = AboutEducenter.objects.get_or_create(
        title=about_data['title'],
        defaults=about_data
    )
    return about


def populate_feature_items(about_section):
    """Popula a tabela site_admin_featureitem com dados de exemplo"""
    feature_items = [
        {
            'text': 'Programas educacionais inovadores focados em tecnologia.',
            'order': 1
        },
        {
            'text': 'Ambiente inclusivo que valoriza a diversidade.',
            'order': 2
        }
    ]
    for item in feature_items:
        FeatureItem.objects.get_or_create(
            about_section=about_section,
            order=item['order'],
            defaults={'text': item['text']}
        )


def populate_about_us():
    """Popula a tabela site_admin_aboutus com dados de exemplo"""
    about_us_data = {
        'mission': (
            'Nossa missão é transformar vidas por meio da educação, oferecendo oportunidades '
            'iguais e incentivando o crescimento pessoal e profissional de cada aluno.'
        ),
        'is_active': True
    }
    AboutUs.objects.get_or_create(
        mission=about_us_data['mission'],
        defaults=about_us_data
    )


def populate_feature_blocks():
    """Popula a tabela site_admin_featureblock com dados de exemplo"""
    feature_blocks = [
        {
            'icon': 'fas fa-book',
            'title': 'Educação de Qualidade',
            'description': 'Cursos estruturados para maximizar o aprendizado.',
            'is_active': True,
            'order': 1
        },
        {
            'icon': 'fas fa-users',
            'title': 'Comunidade Engajada',
            'description': 'Uma comunidade que apoia o crescimento mútuo.',
            'is_active': True,
            'order': 2
        },
        {
            'icon': 'fas fa-laptop',
            'title': 'Tecnologia Avançada',
            'description': 'Ferramentas modernas para um ensino dinâmico.',
            'is_active': True,
            'order': 3
        }
    ]
    for block in feature_blocks:
        FeatureBlock.objects.get_or_create(
            title=block['title'],
            defaults=block
        )


def populate_hero_content():
    """Popula a tabela site_admin_herocontent com dados de exemplo"""
    hero_data = {
        'title': 'Bem-vindo ao Futuro da Educação',
        'subtitle': (
            'Junte-se a nós para uma jornada de aprendizado transformadora, onde cada aluno '
            'é valorizado e preparado para o sucesso.'
        ),
        'button_text': 'Saiba Mais',
        'button_link': '/about'
    }
    HeroContent.objects.get_or_create(
        title=hero_data['title'],
        defaults=hero_data
    )


def populate_database(style=None):
    with transaction.atomic():
        # 1. Criar grupos e usuários
        create_user_groups()
        create_example_users()

        # 2. Popula calendário
        populate_calendario()

        # 3. Criar Diretorias de Ensino
        diretoria1, _ = DiretoriaEnsino.objects.get_or_create(
            nome="Diretoria de Ensino Regional Centro",
            defaults={
                'endereco': 'Av. Paulista, 1000 - Centro',
                'telefone': '(11) 1234-5678'
            }
        )
        diretoria2, _ = DiretoriaEnsino.objects.get_or_create(
            nome="Diretoria de Ensino Regional Leste",
            defaults={
                'endereco': 'Rua Vergueiro, 2000 - Liberdade',
                'telefone': '(11) 8765-4321'
            }
        )

        # 4. Criar Diretores
        diretor1 = Diretor.objects.create(
            nome_usuario="diretor1",
            senha="temp123",
            nome="Carlos Alberto Silva",
            cpf=generate_cpf(),
            data_nascimento=date(1975, 5, 15),
            sexo='Masculino',
            endereco='Rua das Flores, 123 - Jardim Paulista',
            telefone='(11) 98765-4321'
        )
        diretor2 = Diretor.objects.create(
            nome_usuario="diretor2",
            senha="temp123",
            nome="Ana Maria Santos",
            cpf=generate_cpf(),
            data_nascimento=date(1980, 8, 22),
            sexo='Feminino',
            endereco='Av. Brasil, 500 - Mooca',
            telefone='(11) 91234-5678'
        )

        # 5. Criar Escolas
        escola1, _ = Escola.objects.get_or_create(
            nome="EMEF Jardim das Flores",
            defaults={
                'endereco': 'Rua das Acácias, 123 - Jardim das Flores',
                'telefone': '(11) 2345-6789',
                'diretoria_ensino': diretoria1,
                'diretor': diretor1,
                'ativa': True
            }
        )
        escola2, _ = Escola.objects.get_or_create(
            nome="EMEF Vila Nova",
            defaults={
                'endereco': 'Av. Principal, 456 - Vila Nova',
                'telefone': '(11) 3456-7890',
                'diretoria_ensino': diretoria2,
                'diretor': diretor2,
                'ativa': True
            }
        )

        # 6. Criar Turmas
        turmas_data = [
            {"nome": "1º Ano A", "escola": escola1, "ano": 2025},
            {"nome": "2º Ano A", "escola": escola1, "ano": 2025},
            {"nome": "3º Ano A", "escola": escola1, "ano": 2025},
            {"nome": "4º Ano A", "escola": escola1, "ano": 2025},
            {"nome": "5º Ano A", "escola": escola1, "ano": 2025},
            {"nome": "1º Ano B", "escola": escola2, "ano": 2025},
            {"nome": "2º Ano B", "escola": escola2, "ano": 2025},
            {"nome": "3º Ano B", "escola": escola2, "ano": 2025},
        ]
        turmas = []
        for data in turmas_data:
            turma, _ = Turma.objects.get_or_create(**data)
            turmas.append(turma)

        # 7. Criar Alunos
        nomes_alunos = [
            "Ana Silva", "Carlos Oliveira", "Mariana Santos", "Pedro Costa",
            "Julia Pereira", "Lucas Fernandes", "Beatriz Almeida", "Rafael Souza",
            "Isabela Martins", "Gabriel Lima", "Laura Beatriz", "Matheus Ribeiro",
            "Sofia Mendes", "João Almeida", "Clara Ferreira", "Thiago Barbosa",
            "Manuela Costa", "Felipe Santos", "Larissa Oliveira", "Eduardo Silva",
            "Camila Pereira", "Gustavo Lima", "Helena Souza", "Vinicius Ribeiro",
            "Lívia Martins", "Daniel Fernandes", "Alice Mendes", "Bruno Costa",
            "Valentina Almeida", "Arthur Santos", "Letícia Oliveira", "Enzo Silva",
            "Luana Pereira", "Nicolas Lima", "Yasmin Souza", "Igor Ribeiro",
            "Bianca Martins", "Leonardo Fernandes", "Gabriela Mendes", "Diego Costa",
            "Fernanda Almeida", "Samuel Santos", "Vitória Oliveira", "Caio Silva",
            "Amanda Pereira", "Henrique Lima", "Júlia Souza", "Murilo Ribeiro",
            "Evelyn Martins", "Rodrigo Fernandes", "Natália Mendes", "Otávio Costa"
        ]
        alunos = []
        for nome in nomes_alunos:
            turma_principal = random.choice(turmas)
            aluno, _ = Aluno.objects.get_or_create(
                nome=nome,
                defaults={
                    'ra': generate_ra(),
                    'data_nascimento': random_date(date(2010, 1, 1), date(2015, 12, 31)),
                    'ativo': True,
                    'quilombola': random.choice([True, False])
                }
            )
            aluno.turmas.add(turma_principal)
            if random.random() < 0.3:
                turmas_disponiveis = [t for t in turmas if t != turma_principal]
                if turmas_disponiveis:
                    qtd_extras = random.randint(1, min(2, len(turmas_disponiveis)))
                    turmas_extras = random.sample(turmas_disponiveis, qtd_extras)
                    aluno.turmas.add(*turmas_extras)
            alunos.append(aluno)

        # 8. Criar Disciplinas
        disciplinas_data = [
            "Português", "Matemática", "História", "Geografia",
            "Ciências", "Educação Física", "Artes", "Inglês"
        ]
        disciplinas = []
        for nome in disciplinas_data:
            disciplina, _ = Disciplina.objects.get_or_create(nome=nome)
            disciplinas.append(disciplina)

        # 9. Criar Professores
        nomes_professores = [
            "Márcia Fernandes", "Roberto Almeida", "Patrícia Souza", "Ricardo Lima",
            "Fernanda Costa", "Gustavo Santos", "Luciana Oliveira", "Marcos Pereira"
        ]
        professores = []
        for i, nome in enumerate(nomes_professores):
            professor = Professor.objects.create(
                nome=nome,
                cpf=generate_cpf(),
                data_nascimento=random_date(date(1970, 1, 1), date(1990, 12, 31)),
                sexo=random.choice(['Masculino', 'Feminino']),
                endereco=f'Rua Professor {i + 1}, {random.randint(100, 999)} - Centro',
                telefone=f'(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
            )
            professor.disciplinas.set(random.sample(disciplinas, random.randint(2, 4)))
            professor.turmas.set(random.sample(turmas, random.randint(1, 3)))
            professores.append(professor)

        # 10. Criar Bimestres para 2025
        bimestres_data = [
            {
                'nome': '1º Bimestre',
                'ano_letivo': 2025,
                'data_inicio': date(2025, 2, 5),
                'data_fim': date(2025, 4, 10),
                'dias_letivo': 45,
            },
            {
                'nome': '2º Bimestre',
                'ano_letivo': 2025,
                'data_inicio': date(2025, 4, 11),
                'data_fim': date(2025, 6, 30),
                'dias_letivo': 50,
            },
            {
                'nome': '3º Bimestre',
                'ano_letivo': 2025,
                'data_inicio': date(2025, 7, 25),
                'data_fim': date(2025, 9, 30),
                'dias_letivo': 48,
            },
            {
                'nome': '4º Bimestre',
                'ano_letivo': 2025,
                'data_inicio': date(2025, 10, 1),
                'data_fim': date(2025, 12, 19),
                'dias_letivo': 52,
            },
        ]
        bimestres = []
        for data in bimestres_data:
            bimestre, _ = Bimestre.objects.get_or_create(
                nome=data['nome'],
                ano_letivo=data['ano_letivo'],
                defaults={
                    'data_inicio': data['data_inicio'],
                    'data_fim': data['data_fim'],
                    'dias_letivo': data['dias_letivo']
                }
            )
            bimestres.append(bimestre)

        # 11. Criar Períodos Letivos
        periodos_data = [
            {
                "nome": "Ano Letivo 2025",
                "tipo": "ANUAL",
                "ano": 2025,
                "data_inicio": date(2025, 2, 5),
                "data_fim": date(2025, 12, 19),
                "ativo": True
            },
            {
                "nome": "1º Semestre 2026",
                "tipo": "SEMESTRAL",
                "ano": 2026,
                "data_inicio": date(2026, 2, 5),
                "data_fim": date(2026, 7, 5),
                "ativo": False
            }
        ]
        periodos = []
        for data in periodos_data:
            periodo, created = PeriodoLetivo.objects.get_or_create(
                ano=data['ano'],
                defaults={
                    'nome': data['nome'],
                    'tipo': data['tipo'],
                    'data_inicio': data['data_inicio'],
                    'data_fim': data['data_fim'],
                    'ativo': data['ativo']
                }
            )
            if created and style:
                style.SUCCESS(f'Período Letivo criado: {periodo}')
            periodos.append(periodo)

        # 12. Criar Dias Letivos
        periodo_principal = periodos[0]
        current_date = periodo_principal.data_inicio
        while current_date <= periodo_principal.data_fim:
            if current_date.weekday() < 5:
                status = 'L'
                if current_date.month == 4 and current_date.day == 21:
                    status = 'FE'
                elif current_date.month == 5 and current_date.day == 1:
                    status = 'FE'
                elif current_date.month == 9 and current_date.day == 7:
                    status = 'FE'
                elif current_date.month == 10 and current_date.day == 12:
                    status = 'FE'
                elif current_date.month == 11 and current_date.day == 2:
                    status = 'FE'
                elif current_date.month == 11 and current_date.day == 15:
                    status = 'FE'
                elif current_date.month == 12 and current_date.day == 25:
                    status = 'FE'
                elif current_date.month == 7 and 15 <= current_date.day <= 31:
                    status = 'R'
                DiaLetivo.objects.get_or_create(
                    periodo_letivo=periodo_principal,
                    data=current_date,
                    defaults={'status': status}
                )
            current_date += timedelta(days=1)

        # 13. Criar Avaliações
        for aluno in alunos:
            for bimestre in bimestres:
                for disciplina in random.sample(disciplinas, 4):
                    try:
                        turma = aluno.turmas.first()
                        if turma is None:
                            continue
                    except AttributeError:
                        print(f"Erro: Aluno {aluno.nome} não tem turmas associadas.")
                        continue
                    Avaliacao.objects.get_or_create(
                        aluno=aluno,
                        disciplina=disciplina,
                        bimestre=bimestre,
                        turma=turma,
                        defaults={
                            'nota': round(random.uniform(5, 10), 1),
                            'data_fechamento': random_date(
                                bimestre.data_inicio,
                                bimestre.data_fim
                            )
                        }
                    )

        # 14. Criar Frequências
        dias_letivos = DiaLetivo.objects.filter(
            periodo_letivo=periodo_principal,
            status='L'
        ).order_by('data')
        for dia_letivo in dias_letivos:
            if random.random() < 0.8:
                for aluno in Aluno.objects.all():
                    try:
                        turma = aluno.turmas.first()
                        if turma is None:
                            continue
                    except AttributeError:
                        print(f"Erro: Aluno {aluno.nome} não tem turmas associadas.")
                        continue
                    for disciplina in random.sample(disciplinas, 4):
                        Frequencia.objects.get_or_create(
                            aluno=aluno,
                            turma=turma,
                            data=dia_letivo.data,
                            disciplina=disciplina,
                            defaults={
                                'status': random.choices(
                                    ['presente', 'ausente', 'justificado'],
                                    weights=[0.85, 0.1, 0.05]
                                )[0]
                            }
                        )

        # 15. Popula tabelas do site_admin
        about_section = populate_about_edu_center()
        populate_feature_items(about_section)
        populate_about_us()
        populate_feature_blocks()
        populate_hero_content()

        # 16. Configura o tema do admin_interface
        try:
            from admin_interface.models import Theme
            theme, created = Theme.objects.get_or_create(
                name='Tema Padrão',
                defaults={
                    'active': True,
                    'show_logo': False,
                }
            )
            if not created:
                theme.show_logo = False
                theme.save()

            if style:
                style.SUCCESS('✅ Tema do Admin configurado com sucesso!')
        except ImportError:
            if style:
                style.WARNING('⚠️ admin_interface não instalado, pulando configuração de tema')
        except Exception as e:
            if style:
                style.ERROR(f'❌ Erro ao configurar tema: {str(e)}')


if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diario_classe.settings')
    django.setup()
    populate_database()