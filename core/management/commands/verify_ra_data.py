from django.core.management.base import BaseCommand
from core.models import Aluno

class Command(BaseCommand):
    help = 'Verifica os RAs e datas de nascimento dos alunos'

    def handle(self, *args, **options):
        alunos_sem_ra = Aluno.objects.filter(ra__isnull=True)
        alunos_sem_data = Aluno.objects.filter(data_nascimento__isnull=True)
        
        self.stdout.write(f"Alunos sem RA: {alunos_sem_ra.count()}")
        self.stdout.write(f"Alunos sem data de nascimento: {alunos_sem_data.count()}")
        
        for aluno in Aluno.objects.all():
            self.stdout.write(f"{aluno.nome}: RA {aluno.ra} | Nasc. {aluno.data_nascimento}")