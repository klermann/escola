# Importações padrão do Django
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import re
from django import forms

from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import models
from django.contrib import admin
from django import forms

# --- Validadores auxiliares (reaproveite os seus, se já existirem) ---
CEP_REGEX = RegexValidator(
    regex=r'^\d{5}-?\d{3}$',
    message="CEP deve estar no formato 99999-999 ou 99999999."
)
UF_CHOICES = [
    ('AC','AC'),('AL','AL'),('AP','AP'),('AM','AM'),('BA','BA'),('CE','CE'),('DF','DF'),
    ('ES','ES'),('GO','GO'),('MA','MA'),('MT','MT'),('MS','MS'),('MG','MG'),('PA','PA'),
    ('PB','PB'),('PR','PR'),('PE','PE'),('PI','PI'),('RJ','RJ'),('RN','RN'),('RS','RS'),
    ('RO','RO'),('RR','RR'),('SC','SC'),('SP','SP'),('SE','SE'),('TO','TO'),
]
EMAIL_OPCIONAL_HELP = "Preencha apenas se desejar registrar o e-mail."


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

# ============================================
# DADOS PESSOAIS (complemento do Aluno)
# ============================================
class AlunoPessoal(models.Model):
    SEXO_CHOICES = [('M','Masculino'), ('F','Feminino')]
    RACA_COR_CHOICES = [
        ('branca','Branca'), ('preta','Preta'), ('parda','Parda'),
        ('amarela','Amarela'), ('indigena','Indígena'), ('nao_informado','Prefiro não informar'),
    ]

    aluno = models.OneToOneField('Aluno', on_delete=models.CASCADE, related_name='pessoal')

    nome_social = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome social (se houver)")
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True)
    raca_cor = models.CharField(max_length=20, choices=RACA_COR_CHOICES, blank=True, null=True, verbose_name="Raça/Cor (autodeclarada)")
    nacionalidade = models.CharField(max_length=60, blank=True, null=True)
    naturalidade_cidade = models.CharField(max_length=80, blank=True, null=True)
    naturalidade_uf = models.CharField(max_length=2, choices=UF_CHOICES, blank=True, null=True)
    cpf = models.CharField(
        max_length=14, blank=True, null=True, validators=[CPF_REGEX],
        verbose_name="Número do CPF"
    )
    rg_numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número do RG")
    rg_orgao_emissor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Órgão emissor do RG")
    certidao_nascimento = models.TextField(blank=True, null=True, help_text="Número, livro, folha, cartório, etc.")

    class Meta:
        verbose_name = "Dados Pessoais"
        verbose_name_plural = "Dados Pessoais"

    def __str__(self):
        return f"Pessoais de {self.aluno.nome}"

# ============================================
# RESPONSÁVEIS
# ============================================
class AlunoResponsaveis(models.Model):
    aluno = models.OneToOneField('Aluno', on_delete=models.CASCADE, related_name='responsaveis')

    mae_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome completo da mãe")
    pai_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome completo do pai")
    responsavel_legal_nome = models.CharField(max_length=100, blank=True, null=True)
    telefone_principal = models.CharField(max_length=20, blank=True, null=True, validators=[TELEFONE_REGEX])
    telefone_reserva = models.CharField(max_length=20, blank=True, null=True, validators=[TELEFONE_REGEX])
    email_responsavel = models.EmailField(blank=True, null=True, help_text=EMAIL_OPCIONAL_HELP)
    guarda_judicial = models.BooleanField(default=False, verbose_name="Guarda judicial?")

    class Meta:
        verbose_name = "Responsáveis"
        verbose_name_plural = "Responsáveis"

    def __str__(self):
        return f"Responsáveis de {self.aluno.nome}"

# ============================================
# CONTATOS / ENDEREÇO
# ============================================
class AlunoContato(models.Model):
    aluno = models.OneToOneField('Aluno', on_delete=models.CASCADE, related_name='contato')

    logradouro = models.CharField(max_length=150, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=60, blank=True, null=True)
    bairro = models.CharField(max_length=60, blank=True, null=True)
    cidade = models.CharField(max_length=80, blank=True, null=True)
    uf = models.CharField(max_length=2, choices=UF_CHOICES, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True, validators=[CEP_REGEX])

    telefone_residencial = models.CharField(max_length=20, blank=True, null=True, validators=[TELEFONE_REGEX])
    celular_aluno = models.CharField(max_length=20, blank=True, null=True, validators=[TELEFONE_REGEX])
    email_aluno = models.EmailField(blank=True, null=True, help_text=EMAIL_OPCIONAL_HELP)

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"

    def __str__(self):
        return f"Contato de {self.aluno.nome}"

# ============================================
# DADOS ESCOLARES
# ============================================
class AlunoEscolar(models.Model):
    TURNO_CHOICES = [('manhã', 'Manhã'), ('tarde','Tarde'), ('noite','Noite'), ('integral','Integral')]
    ETAPA_CHOICES = [
        ('EI','Educação Infantil'),
        ('EF','Ensino Fundamental'),
        ('EM','Ensino Médio'),
    ]
    SITUACAO_CHOICES = [
        ('ativa','Ativa'), ('transferido','Transferido'), ('trancado','Trancado'),
        ('egresso','Egresso'), ('cancelado','Cancelado'),
    ]

    aluno = models.OneToOneField('Aluno', on_delete=models.CASCADE, related_name='escolar')

    numero_matricula = models.CharField(max_length=30, unique=True, verbose_name="Número de matrícula")
    ano_serie_atual = models.CharField(max_length=20, verbose_name="Ano/Série atual")
    turma_atual = models.ForeignKey('Turma', on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos_atual')
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, blank=True, null=True)
    unidade_escolar = models.ForeignKey('Escola', on_delete=models.SET_NULL, null=True, blank=True)
    etapa_ensino = models.CharField(max_length=2, choices=ETAPA_CHOICES, blank=True, null=True)

    historico_escolar = models.TextField(blank=True, null=True, help_text="Escolas anteriores, anos cursados, aprovação/reprovação.")
    situacao_matricula = models.CharField(max_length=15, choices=SITUACAO_CHOICES, default='ativa')
    data_ingresso = models.DateField(blank=True, null=True)
    data_saida = models.DateField(blank=True, null=True)
    numero_chamada = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Dados Escolares"
        verbose_name_plural = "Dados Escolares"

    def __str__(self):
        return f"Escolares de {self.aluno.nome}"

# ============================================
# DADOS COMPLEMENTARES
# ============================================
class AlunoComplementar(models.Model):
    aluno = models.OneToOneField('Aluno', on_delete=models.CASCADE, related_name='complementar')

    programa_bolsa_familia = models.BooleanField(default=False, verbose_name="Participa do Bolsa Família?")
    programa_peti = models.BooleanField(default=False, verbose_name="Participa do PETI?")
    acesso_internet_casa = models.BooleanField(default=True, verbose_name="Tem acesso à internet em casa?")
    dispositivo_para_estudos = models.CharField(
        max_length=40, blank=True, null=True,
        help_text="Computador, celular, tablet, etc."
    )
    transporte_escolar = models.BooleanField(default=False, verbose_name="Usa transporte escolar?")
    religiao = models.CharField(max_length=60, blank=True, null=True, verbose_name="Religião (opcional)")
    autoriza_uso_imagem = models.BooleanField(default=False, verbose_name="Autoriza uso de imagem?")

    class Meta:
        verbose_name = "Dados Complementares"
        verbose_name_plural = "Dados Complementares"

    def __str__(self):
        return f"Complementares de {self.aluno.nome}"

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
        verbose_name = "Dept. de Educação"
        verbose_name_plural = "Dept. de Educação"

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
# --- após class Usuario(models.Model) ---

class Diretor(Usuario):
    inicio_no_cargo = models.DateField(null=True, blank=True, verbose_name="Início no cargo")
    efetivo = models.BooleanField(default=False, verbose_name="Efetivo")

    class Meta:
        verbose_name = "Diretor"
        verbose_name_plural = "Diretores"
        ordering = ['nome']

    def __str__(self):
        return f"Diretor: {self.nome}"

class DiretorFormacao(models.Model):
    diretor = models.ForeignKey(Diretor, on_delete=models.CASCADE, related_name="formacoes")
    titulo = models.CharField(max_length=120, verbose_name="Formação")
    instituicao = models.CharField(max_length=120, blank=True, null=True)
    ano = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.titulo

class DiretorCurso(models.Model):
    diretor = models.ForeignKey(Diretor, on_delete=models.CASCADE, related_name="cursos")
    nome = models.CharField(max_length=120, verbose_name="Curso")
    instituicao = models.CharField(max_length=120, blank=True, null=True)
    carga_horaria = models.PositiveIntegerField(blank=True, null=True, verbose_name="Carga horária (h)")
    ano = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.nome


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

# perto dos validadores já existentes
CNPJ_REGEX = RegexValidator(
    regex=r'^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$',
    message="CNPJ deve estar no formato 00.000.000/0000-00 ou apenas dígitos."
)

class Escola(models.Model):
    nome = models.CharField(max_length=150, verbose_name="Nome")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    diretoria_ensino = models.ForeignKey(DiretoriaEnsino, on_delete=models.PROTECT, verbose_name="Diretoria Regional de Ensino")
    diretor = models.ForeignKey(Diretor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Diretor Responsável")

    # — novos —
    cnpj = models.CharField(max_length=18, blank=True, null=True, validators=[CNPJ_REGEX], verbose_name="CNPJ")
    cod_cie = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código CIE")
    apm_ativa = models.BooleanField(default=False, verbose_name="APM ativa?")
    ppp_arquivo = models.FileField(upload_to="ppp/", blank=True, null=True, verbose_name="Projeto Político-Pedagógico (PDF)")

    def __str__(self):
        return self.nome


class EscolaEstruturaFisica(models.Model):
    """One-to-One para manter a tela limpa e extensível."""
    escola = models.OneToOneField(Escola, on_delete=models.CASCADE, related_name="estrutura")

    qtd_salas = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Salas (quantidade)")
    tem_cozinha = models.BooleanField(default=False, verbose_name="Cozinha")
    tem_refeitorio = models.BooleanField(default=False, verbose_name="Refeitório")
    area_lazer_m2 = models.PositiveIntegerField(blank=True, null=True, verbose_name="Área de lazer (m²)")
    possui_alimentacao_escolar = models.BooleanField(default=False, verbose_name="Alimentação escolar")
    qtd_quadras = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Quadras poliesportivas")

    class Meta:
        verbose_name = "Estrutura física"
        verbose_name_plural = "Estrutura física"

    def __str__(self):
        return f"Estrutura de {self.escola.nome}"

class EscolaFuncionarios(models.Model):
    """Quadro básico de funcionários da escola."""
    escola = models.OneToOneField(Escola, on_delete=models.CASCADE, related_name="funcionarios")

    # OBS: o diretor já existe em Escola.diretor; aqui ficam os demais cargos e quantitativos.
    vice_diretor = models.CharField(max_length=120, blank=True, null=True, verbose_name="Vice-diretor(a)")
    coordenador = models.CharField(max_length=120, blank=True, null=True, verbose_name="Coordenador(a)")
    secretario = models.CharField(max_length=120, blank=True, null=True, verbose_name="Secretário(a)")

    qtd_professores = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Quantidade de professores")
    qtd_alunos = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Quantidade de alunos")

    qtd_cozinheiras = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Cozinheira(s)")
    qtd_auxiliares_limpeza = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Auxiliar(es) de limpeza")

    class Meta:
        verbose_name = "Funcionários"
        verbose_name_plural = "Funcionários"

    def __str__(self):
        return f"Funcionários de {self.escola.nome}"

#############################################################################
#############################################################################
#############################################################################
#############################################################################
class Turma(models.Model):
    TIPO_ENSINO_CHOICES = [
        ("EI", "Educação Infantil"),
        ("EF1", "Ensino Fundamental – Anos Iniciais"),
        ("EF2", "Ensino Fundamental – Anos Finais"),
        ("EM", "Ensino Médio"),
    ]

    nome = models.CharField(max_length=100)
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='turmas')
    ano = models.PositiveIntegerField(verbose_name='Ano')
    codigo = models.CharField(max_length=20, default="")
    tipo_ensino = models.CharField(
        max_length=4,
        choices=TIPO_ENSINO_CHOICES,
        default="EF1"
    )
    sala_identificacao = models.CharField(
        max_length=50,
        default="S/N",
        verbose_name="Sala (nº/identificação)"
    )
    aee = models.BooleanField(default=False, verbose_name="AEE")
    aee_observacoes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Obs. AEE"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["escola", "ano", "codigo"], name="uq_turma_escola_ano_codigo"),
        ]

    def __str__(self):
        return f"{self.nome} - {self.escola.nome} ({self.ano})"

class TurmaHorario(models.Model):
    DIAS = [
        (0, "Segunda"),
        (1, "Terça"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIAS)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()

    class Meta:
        verbose_name = "Funcionamento da Turma"
        verbose_name_plural = "Funcionamento da Turma"
        constraints = [
            models.CheckConstraint(
                check=models.Q(horario_inicio__lt=models.F("horario_fim")),
                name="chk_turma_horario_intervalo_valido"
            ),
            models.UniqueConstraint(fields=["turma", "dia_semana"], name="uq_turma_dia_unico"),
        ]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.horario_inicio}-{self.horario_fim}"


#############################################################################
#############################################################################
#############################################################################
#############################################################################
def validate_ra(value):
    if not re.match(r'^0000\d{9}[0-9X]$', value):
        raise ValidationError('RA deve estar no formato 0000 + 9 dígitos + 1 dígito/X')


class Aluno(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    ra = models.CharField(
        max_length=14,
        unique=True,
        validators=[validate_ra],
        help_text="Formato: 0000 + 9 dígitos + 1 dígito/X"
    )
    data_nascimento = models.DateField(verbose_name='Data de Nascimento', null=True, blank=True)
    quilombola = models.BooleanField(default=False, verbose_name='Quilombola')  # Novo campo

    # Relacionamentos ManyToMany (igual ao Professor)
    turmas = models.ManyToManyField(
        'Turma',
        blank=True,
        related_name="alunos",
        verbose_name="Turmas",
        help_text="Selecione as turmas deste aluno.",
    )

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
    AREA_CONHECIMENTO_CHOICES = [
        ("LINGUAGENS", "Linguagens"),
        ("MATEMÁTICA", "Matemática"),
        ("CIÊNCIAS HUMANAS", "Ciências Humanas"),
        ("CIÊNCIA DA NATUREZA", "Ciência da Natureza"),
    ]

    nome = models.CharField(max_length=50, unique=True)
    area_conhecimento = models.CharField(
        max_length=30,
        choices=AREA_CONHECIMENTO_CHOICES,
        verbose_name="Área do conhecimento",
        default="LINGUAGENS"  # <-- valor inicial válido
    )
    carga_horaria = models.PositiveIntegerField(
        verbose_name="Carga horária (horas)",
        default=0  # <-- inteiro simples
    )

    def __str__(self):
        return f"{self.nome} ({self.area_conhecimento})"


class Bimestre(models.Model):
    nome = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()
    data_inicio = models.DateField(verbose_name='Data de Início', null=True, blank=True)  # Adicionado null=True
    data_fim = models.DateField(verbose_name='Data de Fim', null=True, blank=True)  # Adicionado null=True
    dias_letivo = models.IntegerField()

    def __str__(self):
        return f"{self.nome} - {self.dias_letivo} dias | ano- {self.ano_letivo}"

    def clean(self):
        # Verifica se ambas as datas estão preenchidas antes de comparar
        if self.data_inicio and self.data_fim:
            if self.data_fim < self.data_inicio:
                raise ValidationError('A data de fim não pode ser anterior à data de início.')

            # Só verifica sobreposição se ambas as datas estiverem preenchidas
            overlapping = Bimestre.objects.filter(
                ano_letivo=self.ano_letivo,
                data_inicio__isnull=False,  # Garante que data_inicio não é None
                data_fim__isnull=False,  # Garante que data_fim não é None
                data_inicio__lte=self.data_fim,
                data_fim__gte=self.data_inicio
            ).exclude(id=self.id if self.id else None)  # Exclui o próprio registro se estiver sendo editado

            if overlapping.exists():
                raise ValidationError("Este bimestre sobrepõe-se a outro bimestre no mesmo ano letivo.")

        # Validação adicional para garantir que campos obrigatórios estejam preenchidos
        if not self.nome:
            raise ValidationError({'nome': 'O nome do bimestre é obrigatório'})

        if not self.ano_letivo:
            raise ValidationError({'ano_letivo': 'O ano letivo é obrigatório'})

        if not self.dias_letivo:
            raise ValidationError({'dias_letivo': 'O número de dias letivos é obrigatório'})


class BimestreForm(forms.ModelForm):
        class Meta:
            model = Bimestre
            fields = ['nome', 'ano_letivo', 'data_inicio', 'data_fim', 'dias_letivo']
            widgets = {
                'nome': forms.TextInput(attrs={
                    'placeholder': 'Ex: 1º Bimestre, Primeiro Bimestre...',
                    'class': 'form-control',
                    'required': 'required'
                }),
                'ano_letivo': forms.NumberInput(attrs={
                    'placeholder': 'Ex: 2023, 2024...',
                    'class': 'form-control',
                    'required': 'required',
                    'min': '2000',
                    'max': '2100'
                }),
                'data_inicio': forms.DateInput(attrs={
                    'placeholder': 'DD/MM/AAAA',
                    'class': 'form-control',
                    'type': 'date',
                    'required': 'required'
                }),
                'data_fim': forms.DateInput(attrs={
                    'placeholder': 'DD/MM/AAAA',
                    'class': 'form-control',
                    'type': 'date',
                    'required': 'required'
                }),
                'dias_letivo': forms.NumberInput(attrs={
                    'placeholder': 'Ex: 45, 50...',
                    'class': 'form-control',
                    'min': '1',
                    'required': 'required'
                })
            }

        def clean(self):
            cleaned_data = super().clean()
            data_inicio = cleaned_data.get('data_inicio')
            data_fim = cleaned_data.get('data_fim')

            if data_inicio and data_fim and data_fim < data_inicio:
                self.add_error('data_fim', 'A data de fim não pode ser anterior à data de início.')

            return cleaned_data

        def clean_nome(self):
            nome = self.cleaned_data['nome']
            if not any(char.isdigit() for char in nome):
                raise forms.ValidationError("O nome deve conter o número do bimestre (Ex: 1º Bimestre)")
            return nome

        def clean_ano_letivo(self):
            ano = self.cleaned_data['ano_letivo']
            if ano < 2000 or ano > 2100:
                raise forms.ValidationError("Ano letivo deve estar entre 2000 e 2100")
            return ano

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
        if not self.turma_id or not self.aluno.turmas.filter(id=self.turma_id).exists():
            raise ValidationError("O aluno não está matriculado nesta turma")
        super().save(*args, **kwargs)

class Frequencia(models.Model):
    PRESENCA_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('justificado', 'Justificado'),
        ('nao_letivo', 'Dia Não Letivo'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, db_index=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, db_index=True)

    data = models.DateField(verbose_name='Data')
    registro = models.PositiveSmallIntegerField(
        verbose_name="Registro/Aula do dia",
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Número da aula dentro do dia (1ª, 2ª, 3ª...)."
    )
    status = models.CharField(max_length=20, choices=PRESENCA_CHOICES)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['aluno', 'data', 'disciplina', 'registro'],
                name='unique_frequencia_aluno_dia_disciplina_registro'
            )
        ]
        verbose_name = 'Frequência'
        verbose_name_plural = 'Frequências'

    def __str__(self):
        return f"{self.aluno.nome} - {self.data} - Aula {self.registro} - {self.get_status_display()}"

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


class ProfessorFormacao(models.Model):
    formacao = models.CharField(max_length=150, verbose_name="Formação")
    professor = models.ForeignKey(
        'Professor',
        on_delete=models.CASCADE,
        related_name='formacoes'
    )

    class Meta:
        verbose_name = 'Formação'
        verbose_name_plural = 'Formações'

    def __str__(self):
        return self.formacao



class ProfessorCurso(models.Model):
    professor = models.ForeignKey(
        "Professor",
        on_delete=models.CASCADE,
        related_name="cursos"
    )
    nome = models.CharField(max_length=150, verbose_name="Curso de Aperfeiçoamento")

    def __str__(self):
        return f"{self.nome} ({self.professor.nome})"

    class Meta:
        verbose_name = "Curso de Aperfeiçoamento"
        verbose_name_plural = "Cursos de Aperfeiçoamento"


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

