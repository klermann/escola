import os
import django
import sys
from django.db import transaction
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

# Configuração para funcionar como script independente
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meu_projeto.settings')
    django.setup()
except:
    pass  # Já configurado se executado como comando Django

from core.models import (
    Escola, Turma, Aluno, Disciplina, Bimestre, 
    Avaliacao, Frequencia, PeriodoLetivo, DiaLetivo, Calendario,
    DiretoriaEnsino, Diretor, Professor
)

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de exemplo para o sistema escolar'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a população do banco de dados...'))
        populate_database(self.style)
        self.stdout.write(self.style.SUCCESS('Banco de dados populado com sucesso!'))

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
    
    # Calcula primeiro dígito verificador
    soma = sum((10 - i) * num for i, num in enumerate(cpf))
    d1 = 11 - (soma % 11)
    if d1 >= 10:
        d1 = 0
    cpf.append(d1)
    
    # Calcula segundo dígito verificador
    soma = sum((11 - i) * num for i, num in enumerate(cpf))
    d2 = 11 - (soma % 11)
    if d2 >= 10:
        d2 = 0
    cpf.append(d2)
    
    return f"{''.join(map(str, cpf[:3]))}.{''.join(map(str, cpf[3:6]))}.{''.join(map(str, cpf[6:9]))}-{cpf[9]}{cpf[10]}"

def populate_calendario():
    """Popula a tabela Calendario com dados de exemplo"""
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    for mes in meses:
        dias_no_mes = 31 if mes in ['Janeiro', 'Março', 'Maio', 'Julho', 'Agosto', 'Outubro', 'Dezembro'] else 30
        if mes == 'Fevereiro':
            dias_no_mes = 28  # Considerando ano não bissexto para exemplo
            
        for dia in range(1, dias_no_mes + 1):
            # Define status aleatório para alguns dias
            status = None
            if random.random() < 0.2:  # 20% de chance de ter status especial
                status = random.choice(['feriado', 'recesso', 'evento'])
                
            Calendario.objects.get_or_create(
                mes=mes,
                dia=dia,
                defaults={'status': status}
            )

def populate_database(style=None):
    with transaction.atomic():
        # 0. Popula calendário
        populate_calendario()
        
        # 1. Criar Diretorias de Ensino
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
        
        # 2. Criar Diretores
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
        
        # 3. Criar Escolas
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

        # 4. Criar Turmas
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

        # 5. Criar Alunos
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
            aluno, _ = Aluno.objects.get_or_create(
                nome=nome,
                turma=random.choice(turmas),
                defaults={
                    'ra': generate_ra(),
                    'data_nascimento': random_date(date(2010, 1, 1), date(2015, 12, 31)),
                    'ativo': True,
                    'quilombola': random.choice([True, False])
                }
            )
            alunos.append(aluno)

        # 6. Criar Disciplinas
        disciplinas_data = [
            "Português", "Matemática", "História", "Geografia",
            "Ciências", "Educação Física", "Artes", "Inglês"
        ]

        disciplinas = []
        for nome in disciplinas_data:
            disciplina, _ = Disciplina.objects.get_or_create(nome=nome)
            disciplinas.append(disciplina)

        # 7. Criar Professores
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
                endereco=f'Rua Professor {i+1}, {random.randint(100, 999)} - Centro',
                telefone=f'(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'
            )
            
            # Atribui disciplinas aleatórias (2-4 disciplinas por professor)
            professor.disciplinas.set(random.sample(disciplinas, random.randint(2, 4)))
            
            # Atribui turmas aleatórias (1-3 turmas por professor)
            professor.turmas.set(random.sample(turmas, random.randint(1, 3)))
            
            professores.append(professor)

        # 8. Criar Bimestres para 2025
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

        # 9. Criar Períodos Letivos
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

        # 10. Criar Dias Letivos
        periodo_principal = periodos[0]
        current_date = periodo_principal.data_inicio
        
        while current_date <= periodo_principal.data_fim:
            if current_date.weekday() < 5:  # Segunda a sexta
                status = 'L'  # Dia Letivo normal
                
                # Feriados nacionais
                if current_date.month == 4 and current_date.day == 21:  # Tiradentes
                    status = 'FE'
                elif current_date.month == 5 and current_date.day == 1:  # Dia do Trabalho
                    status = 'FE'
                elif current_date.month == 9 and current_date.day == 7:  # Independência
                    status = 'FE'
                elif current_date.month == 10 and current_date.day == 12:  # Nossa Senhora Aparecida
                    status = 'FE'
                elif current_date.month == 11 and current_date.day == 2:  # Finados
                    status = 'FE'
                elif current_date.month == 11 and current_date.day == 15:  # Proclamação da República
                    status = 'FE'
                elif current_date.month == 12 and current_date.day == 25:  # Natal
                    status = 'FE'
                
                # Recesso escolar
                elif current_date.month == 7 and 15 <= current_date.day <= 31:  # Férias de julho
                    status = 'R'
                
                DiaLetivo.objects.get_or_create(
                    periodo_letivo=periodo_principal,
                    data=current_date,
                    defaults={'status': status}
                )
            
            current_date += timedelta(days=1)

        # 11. Criar Avaliações
        for aluno in alunos:
            for bimestre in bimestres:
                for disciplina in random.sample(disciplinas, 4):  # 4 disciplinas por bimestre
                    Avaliacao.objects.get_or_create(
                        aluno=aluno,
                        disciplina=disciplina,
                        bimestre=bimestre,
                        turma=aluno.turma,
                        defaults={
                            'nota': round(random.uniform(5, 10), 1),
                            'data_fechamento': random_date(
                                bimestre.data_inicio,
                                bimestre.data_fim
                            )
                        }
                    )

        # 12. Criar Frequências
        dias_letivos = DiaLetivo.objects.filter(
            periodo_letivo=periodo_principal,
            status='L'
        ).order_by('data')
        
        for dia_letivo in dias_letivos:
            if random.random() < 0.8:  # 80% de chance de criar registros para este dia
                for turma in turmas:
                    for aluno in Aluno.objects.filter(turma=turma):
                        Frequencia.objects.get_or_create(
                            aluno=aluno,
                            turma=turma,
                            data=dia_letivo.data,
                            defaults={
                                'status': random.choices(
                                    ['presente', 'ausente', 'justificado'],
                                    weights=[0.85, 0.1, 0.05]
                                )[0],
                                'disciplina': random.choice(disciplinas)
                            }
                        )

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diario_classe_digital.settings')
    django.setup()
    populate_database()