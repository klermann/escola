# Importações padrão do Django
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import re

# Importações locais (relativas)
from .constants import (
    MAX_LENGTH_NOME,
    MAX_LENGTH_ENDERECO,
    MAX_LENGTH_TELEFONE,
    TELEFONE_REGEX,
    MAX_LENGTH_NOME_USUARIO,
    MAX_LENGTH_SENHA,
    MAX_LENGTH_CPF,
    CPF_REGEX
)

#############################################################################
#############################################################################
#############################################################################
############################################################################# 
class DiretoriaEnsino(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    nome = models.CharField(
        max_length=MAX_LENGTH_NOME,
        verbose_name="Nome do Núcleo educacional"
    )
    endereco = models.CharField(
        max_length=MAX_LENGTH_ENDERECO,
        verbose_name="Endereço",
        blank=True,
        null=True
    )
    telefone = models.CharField(
        max_length=MAX_LENGTH_TELEFONE,
        validators=[TELEFONE_REGEX],
        verbose_name="Telefone",
        blank=True,
        null=True
    )
    criado_em = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Diretoria de Ensino"
        verbose_name_plural = "Diretorias de Ensino"

#############################################################################
#############################################################################
#############################################################################
############################################################################# 
class Usuario(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    nome_usuario = models.CharField(###Lançado para cima o nome de usuário
        max_length=MAX_LENGTH_NOME_USUARIO,
        unique=True,
        verbose_name="Nome de usuário"
    )
    senha = models.CharField(
        max_length=MAX_LENGTH_SENHA,
        verbose_name="Senha",
        help_text="Em produção, use django.contrib.auth para gerenciar senhas."
    )
    nome = models.CharField(max_length=MAX_LENGTH_NOME, verbose_name="Nome completo")
    cpf = models.CharField(
        max_length=MAX_LENGTH_CPF,
        unique=True,
        validators=[CPF_REGEX],
        verbose_name="CPF",
        default='000.000.000-00' 
    )
    data_nascimento = models.DateField(verbose_name="Data de nascimento")
    sexo = models.CharField( ##### inclusão de sexo (M/F)
        max_length=10,
        choices=[('Masculino', 'Masculino'), ('Feminino', 'Feminino')],
        verbose_name="Sexo",
        null=True,
        blank=True
    )
    endereco = models.CharField(
        max_length=MAX_LENGTH_ENDERECO,
        verbose_name="Endereço"
    )
    telefone = models.CharField(
        max_length=MAX_LENGTH_TELEFONE,
        validators=[TELEFONE_REGEX],
        verbose_name="Telefone"
    )

    def __str__(self):
        return self.nome

#############################################################################
#############################################################################
#############################################################################
#############################################################################
class Diretor(Usuario):
    """
    Modelo que representa um Diretor escolar.
    Herda de Usuario e possui um relacionamento OneToOne com Escola.
    """
    
    def __str__(self):
        return f"Diretor: {self.get_full_name()}" if hasattr(self, 'get_full_name') else f"Diretor: {self.nome}"

    class Meta:
        verbose_name = "Diretor"
        verbose_name_plural = "Diretores"
        ordering = ['nome']


#############################################################################
#############################################################################
#############################################################################
#############################################################################
class Calendario(models.Model):
    mes = models.CharField(max_length=20)
    dia = models.IntegerField()
    status = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        unique_together = ('mes', 'dia')

class Escola(models.Model):
    nome = models.CharField(max_length=150, verbose_name="Nome")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    diretoria_ensino = models.ForeignKey(
        DiretoriaEnsino, 
        on_delete=models.PROTECT,
        verbose_name="Diretoria Regional de Ensino"
    )
    diretor = models.ForeignKey(
        Diretor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Diretor Responsável"
    )
    
    def __str__(self):
        return self.nome


#############################################################################
#############################################################################
#############################################################################
#############################################################################
class Turma(models.Model):
    nome = models.CharField(max_length=100)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='turmas')
    ano = models.PositiveIntegerField(verbose_name='Ano', help_text='Ano letivo da turma')

    def __str__(self):
        return f"{self.nome} - {self.escola.nome} ({self.ano})"    
    
#############################################################################
#############################################################################
#############################################################################
#############################################################################
def validate_ra(value):
    if not re.match(r'^0000\d{9}[0-9X]$', value):
        raise ValidationError('RA deve estar no formato 0000 + 9 dígitos + 1 dígito/X')

class Aluno(models.Model):
    nome = models.CharField(max_length=100)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')
    ativo = models.BooleanField(default=True)
    ra = models.CharField(
        max_length=14, 
        unique=True,
        validators=[validate_ra],
        help_text="Formato: 0000 + 9 dígitos + 1 dígito/X"
    )
    data_nascimento = models.DateField(verbose_name='Data de Nascimento', null=True, blank=True)
    quilombola = models.BooleanField(default=False, verbose_name='Quilombola')  # Novo campo
    
    @admin.display(description='Data Nasc.', ordering='data_nascimento')
    def data_nascimento_formatada(self):
        return self.data_nascimento.strftime('%d/%m/%Y') if self.data_nascimento else ''

    def clean(self):
        if self.data_nascimento and self.data_nascimento.year < 2005:
            raise ValidationError({'data_nascimento': 'Data deve ser posterior a 2005'})
        
        if self.ra and not re.match(r'^0000\d{9}[0-9X]$', self.ra):
            raise ValidationError({
                'ra': 'RA deve estar no formato 0000 seguido de 9 dígitos e 1 dígito/X (ex: 0000110487524X)'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def __str__(self):
        return self.nome

class Disciplina(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Bimestre(models.Model):
    nome = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    data_inicio = models.DateField(verbose_name='Data de Início', null=True, blank=True)  # Adicionado null=True
    data_fim = models.DateField(verbose_name='Data de Fim', null=True, blank=True)  # Adicionado null=True
    dias_letivo = models.IntegerField()
    
    def __str__(self):
        return f"{self.nome} - {self.dias_letivo} dias | ano- {self.ano_letivo}"

    def clean(self):
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError('A data de fim não pode ser anterior à data de início.')
        
        overlapping = Bimestre.objects.filter(
            ano_letivo=self.ano_letivo,
            data_inicio__lte=self.data_fim,
            data_fim__gte=self.data_inicio
        ).exclude(id=self.id)
        if overlapping.exists():
            raise ValidationError("Este bimestre sobrepõe-se a outro bimestre no mesmo ano letivo.")

class Avaliacao(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='avaliacoes')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    bimestre = models.ForeignKey(Bimestre, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    nota = models.FloatField()
    data_fechamento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliação"

    def __str__(self):
        return f"{self.aluno.nome} - Disciplina {self.disciplina.nome} - {self.bimestre.nome}: {self.nota}"
    
    def save(self, *args, **kwargs):
        # Ensure the turma matches the aluno's turma
        if self.aluno.turma != self.turma:
            self.turma = self.aluno.turma
        super().save(*args, **kwargs)
        
class Frequencia(models.Model):
    PRESENCA_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('justificado', 'Justificado'),
        ('nao_letivo', 'Dia Não Letivo'),
    ]
    
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='frequencias')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='frequencias')
    data = models.DateField(verbose_name='Data')
    status = models.CharField(max_length=20, choices=PRESENCA_CHOICES)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('aluno', 'data', 'disciplina')  # Um aluno só pode ter um registro por dia por disciplina
        verbose_name = 'Frequência'
        verbose_name_plural = 'Frequências'
    
    def __str__(self):
        return f"{self.aluno.nome} - {self.data} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Garante que a turma do registro de frequência seja a mesma do aluno
        if self.aluno.turma != self.turma:
            self.turma = self.aluno.turma
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.aluno.nome} - {self.data} - {self.get_status_display()}"

class PeriodoLetivo(models.Model):
    TIPO_PERIODO = [
        ('ANUAL', 'Anual'),
        ('SEMESTRAL', 'Semestral'),
        ('TRIMESTRAL', 'Trimestral'),
        ('BIMESTRAL', 'Bimestral'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=10, choices=TIPO_PERIODO, verbose_name="Tipo")
    ano = models.IntegerField(
        validators=[
            MinValueValidator(1900, message="O ano deve ser maior ou igual a 1900."),
            MaxValueValidator(2100, message="O ano deve ser menor ou igual a 2100.")
        ],
        verbose_name="Ano"
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Fim")
    ativo = models.BooleanField(default=False, verbose_name="Ativo")
    
    class Meta:
        verbose_name = 'Período Letivo'
        verbose_name_plural = 'Períodos Letivos'  
        ordering = ['-ano', 'data_inicio']
        indexes = [
            models.Index(fields=['tipo', 'ano', 'ativo']),
            models.Index(fields=['ano', 'data_inicio']),
        ]
        constraints = [
            # Garante que o campo 'ano' seja único
            models.UniqueConstraint(fields=['ano'], name='unique_periodo_letivo_por_ano')
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.ano})"
    
    def clean(self):
        # Validar que a data de fim não seja anterior à data de início
        if self.data_fim < self.data_inicio:
            raise ValidationError(_('A data de fim não pode ser anterior à data de início.'))

        # Validar que as datas pertencem ao ano informado
        if self.data_inicio.year != self.ano or self.data_fim.year != self.ano:
            raise ValidationError(_('As datas de início e fim devem pertencer ao ano informado.'))

        # Garantir que apenas um PeriodoLetivo esteja ativo por vez
        if self.ativo:
            conflitos = PeriodoLetivo.objects.filter(
                ativo=True
            ).exclude(pk=self.pk)

            if conflitos.exists():
                conflito = conflitos.first()
                raise ValidationError(
                    _(f"Já existe um período letivo ativo: {conflito.nome} ({conflito.ano}). "
                      "Apenas um período letivo pode estar ativo por vez.")
                )

    def save(self, *args, **kwargs):
        # Executar validações do método clean antes de salvar
        self.clean()
        
        # Garantir que apenas um PeriodoLetivo esteja ativo
        if self.ativo:
            PeriodoLetivo.objects.filter(ativo=True).exclude(id=self.id).update(ativo=False)
        
        super().save(*args, **kwargs)
            
class DiaLetivo(models.Model):
    STATUS_CHOICES = [
        ('L', 'Dia Letivo'),
        ('F', 'Feriado Docente'),
        ('FE', 'Feriado'),
        ('R', 'Recesso'),
        ('PL', 'Planejamento'),
        ('AC', 'Atividades Cultural/Letivo'),
        ('SA', 'Suspensão de Atividades'),
        ('S', 'Sábado'),
        ('D', 'Domingo'),
        ('RPL', 'Replanejamento'),
    ]

    periodo_letivo = models.ForeignKey(PeriodoLetivo, on_delete=models.CASCADE, related_name='dias_letivos')
    data = models.DateField()
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='L')

    class Meta:
        unique_together = ('periodo_letivo', 'data')
        verbose_name = 'Dia Letivo'
        verbose_name_plural = 'Dias Letivos'

    def __str__(self):
        return f"{self.data.strftime('%d/%m/%Y')} - {self.get_status_display()}"
    

class Professor(models.Model):
    # Opções para carga horária
    CARGA_HORARIA_CHOICES = [
        ("20", "20 horas"),
        ("25", "25 horas"),
        ("30", "30 horas"),
        ("35", "35 horas"),
        ("40", "40 horas"),
    ]

    # Campos básicos
    nome = models.CharField(max_length=100)
    cpf = models.CharField(
        max_length=MAX_LENGTH_CPF,
        unique=True,
        validators=[CPF_REGEX],
        verbose_name="CPF"
    )
    data_nascimento = models.DateField()
    sexo = models.CharField(
        max_length=10,
        choices=[('Masculino', 'Masculino'), ('Feminino', 'Feminino')]
    )
    endereco = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20)

    # Relacionamentos ManyToMany
    disciplinas = models.ManyToManyField(
        'Disciplina',
        blank=True,
        related_name="professores_disciplina",
        help_text="Selecione as disciplinas que o professor leciona.",
        verbose_name="Disciplinas",
    )
    turmas = models.ManyToManyField(
        'Turma',
        blank=True,
        related_name="professores",
        verbose_name="Turmas",
        help_text="Selecione as turmas que este professor leciona.",
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"

class Aviso(models.Model):
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    data_publicacao = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
class Boletim(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    # ... outros campos
    
