from django.core.validators import RegexValidator

# Constantes
MAX_LENGTH_NOME = 100
MAX_LENGTH_NOME_USUARIO = 50
MAX_LENGTH_SENHA = 128
MAX_LENGTH_ENDERECO = 200
MAX_LENGTH_TELEFONE = 15
MAX_LENGTH_RA = 20
MAX_LENGTH_RG = 20
MAX_LENGTH_CPF = 14
MAX_LENGTH_DISCIPLINA = 50
MAX_LENGTH_NOME_TURMA = 50
MAX_LENGTH_CONTEUDO = 1000
MAX_LENGTH_MATRICULA = 20
MAX_LENGTH_SERIE = 30
MAX_LENGTH_ANO_LETIVO = 4
MAX_LENGTH_CARGA_HORARIA = 5
MAX_LENGTH_TURNO = 20
MAX_LENGTH_CURSO = 100
MAX_LENGTH_SEMESTRE = 10

# Validador para telefone
TELEFONE_REGEX = RegexValidator(
    regex=r"^\(?\d{2}\)?\s?\d{4,5}-?\d{4}$",
    message="O telefone deve estar no formato: '(XX) XXXXX-XXXX' ou 'XX XXXXX-XXXX'.",
)

# Validador para CPF
CPF_REGEX = RegexValidator(
    regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
    message="O CPF deve estar no formato: '123.456.789-00'.",
)
# Validador para RG
RG_REGEX = RegexValidator(
    regex=r"^\d{2}\.\d{3}\.\d{3}-\d{2}$",
    message="O RG deve estar no formato: '00.000.000-00'.",
)
