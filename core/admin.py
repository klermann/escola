# core/admin.py
from django.contrib import admin, messages
from datetime import datetime, date, timedelta

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Diretor, Escola, Professor, Turma, Aluno, Disciplina, Bimestre, Avaliacao, Frequencia, \
    PeriodoLetivo, DiaLetivo, DiretoriaEnsino
from django.urls import reverse, path
from django.utils.dateparse import parse_date
import logging
from django import forms
from django.db.models import Max
from django.db.models import Q
from calendar import monthrange
from collections import defaultdict
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from django.db.models import Case, When, Value, IntegerField, CharField, Max
# core/admin.py

from django.contrib import admin
from .models import (
    Aluno, AlunoPessoal, AlunoResponsaveis, AlunoContato,
    AlunoEscolar, AlunoComplementar
)
from .forms import (
    AlunoPessoalForm, AlunoResponsaveisForm, AlunoContatoForm,
    AlunoEscolarForm, AlunoComplementarForm
)

logger = logging.getLogger(__name__)

PRESENTES = ['P', 'presente']
AUSENTES  = ['A', 'ausente']
JUSTIFICADAS = ['J', 'justificada']

class FrequenciaForm(forms.ModelForm):
    class Meta:
        model = Frequencia
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.aluno:
            # Filtra alunos que estão em pelo menos uma turma em comum com a turma selecionada
            if self.instance.turma:
                self.fields['aluno'].queryset = Aluno.objects.filter(
                    turmas=self.instance.turma
                ).distinct()
        elif 'initial' in kwargs and 'turma' in kwargs['initial']:
            turma = kwargs['initial']['turma']
            self.fields['aluno'].queryset = Aluno.objects.filter(
                turmas=turma
            ).distinct()
        else:
            self.fields['aluno'].queryset = Aluno.objects.filter(ativo=True)

# -------- Inlines OneToOne ----------
class AlunoPessoalInline(admin.StackedInline):
    model = AlunoPessoal
    form = AlunoPessoalForm
    can_delete = False
    max_num = 1
    extra = 1
    verbose_name_plural = "Dados pessoais"

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

class AlunoResponsaveisInline(admin.StackedInline):
    model = AlunoResponsaveis
    form = AlunoResponsaveisForm
    can_delete = False
    max_num = 1
    extra = 0
    verbose_name_plural = "Responsáveis"

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

class AlunoContatoInline(admin.StackedInline):
    model = AlunoContato
    form = AlunoContatoForm
    can_delete = False
    max_num = 1
    extra = 0
    verbose_name_plural = "Contatos"

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

class AlunoEscolarInline(admin.StackedInline):
    model = AlunoEscolar
    form = AlunoEscolarForm
    can_delete = False
    max_num = 1
    extra = 0
    verbose_name_plural = "Dados escolares"

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

class AlunoComplementarInline(admin.StackedInline):
    model = AlunoComplementar
    form = AlunoComplementarForm
    can_delete = False
    max_num = 1
    extra = 0
    verbose_name_plural = "Dados complementares"

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if obj is None else 0

# -------- Admin do Aluno ----------
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ra', 'data_nascimento_formatada', 'ativo', 'quilombola', 'turmas_list')
    search_fields = ('nome', 'ra')
    list_filter = ('ativo', 'quilombola', 'turmas')
    list_per_page = 20
    date_hierarchy = 'data_nascimento'
    ordering = ('nome',)
    filter_horizontal = ('turmas',)
    change_form_template = 'admin/core/aluno/change_form_tabs.html'

    # 1ª tela: dados mínimos do Aluno (nome/ra/data/ativo/quilombola/turmas)
    fieldsets = (
        ('Identificação do Aluno', {
            'fields': ('nome', 'ra', 'data_nascimento', 'ativo', 'quilombola', 'turmas')
        }),
    )

    inlines = [
        AlunoPessoalInline,
        AlunoResponsaveisInline,
        AlunoContatoInline,
        AlunoEscolarInline,
        AlunoComplementarInline
    ]

    def turmas_list(self, obj):
        return ", ".join([t.nome for t in obj.turmas.all()])
    turmas_list.short_description = 'Turmas'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Adicione um novo aluno ou clique em um para modificar'
        return super().changelist_view(request, extra_context=extra_context)

    # Pós-salvar: cria automaticamente blocos OneToOne vazios para aparecerem como "abas"
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Garante que os inlines existam após inserir o aluno
        AlunoPessoal.objects.get_or_create(aluno=obj)
        AlunoResponsaveis.objects.get_or_create(aluno=obj)
        AlunoContato.objects.get_or_create(aluno=obj)
        AlunoEscolar.objects.get_or_create(aluno=obj, defaults={'numero_matricula': f"M-{obj.id:06d}", 'ano_serie_atual': ''})
        AlunoComplementar.objects.get_or_create(aluno=obj)


#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(Frequencia)
class FrequenciaAdmin(admin.ModelAdmin):
    form = FrequenciaForm
    list_display = ('aluno', 'data', 'status_display', 'disciplina', 'frequencia_link', 'turma')
    list_filter = ('turma', 'disciplina', 'status', 'data')
    search_fields = ('aluno__nome', 'turma__nome', 'disciplina__nome')
    date_hierarchy = 'data'

    fieldsets = (
        (None, {
            'fields': ('aluno', 'turma', 'data', 'disciplina', 'status')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        custom_urls = [
            path('<int:turma_id>/frequencia/', self.admin_site.admin_view(self.frequencia_form_view),
                 name='frequencia_form'),
        ]
        return custom_urls + urls

    def frequencia_form_view(self, request, turma_id):
        turma = get_object_or_404(Turma, id=turma_id)
        alunos = turma.alunos.filter(ativo=True).order_by('nome')

        # 1. Tenta obter a data da URL
        data_selecionada = request.GET.get('data')

        # 2. Se não houver na URL, tenta obter do POST (em caso de redirecionamento)
        if not data_selecionada and request.method == 'POST':
            data_selecionada = request.POST.get('data')

        # 3. Se ainda não tiver data, usa a mais recente do banco ou data atual
        if not data_selecionada:
            data_do_banco = Frequencia.objects.filter(turma=turma).aggregate(Max('data'))['data__max']
            data_selecionada = str(data_do_banco) if data_do_banco else str(date.today())

        # Valida e formata a data
        try:
            parsed_date = parse_date(data_selecionada)
            if not parsed_date:
                raise ValueError("Data inválida")
            data_selecionada = parsed_date.strftime('%Y-%m-%d')
        except (ValueError, TypeError) as e:
            logger.warning(f"Data inválida recebida: {data_selecionada}. Usando data atual. Erro: {str(e)}")
            data_selecionada = date.today().strftime('%Y-%m-%d')

        if request.method == 'POST':
            self._processar_frequencias(request, alunos, turma, data_selecionada)
            # Redireciona mantendo a data na URL
            return redirect(f"{reverse('admin:frequencia_form', args=[turma.id])}?data={data_selecionada}")

        # Recupera frequências para a data selecionada
        frequencias = Frequencia.objects.filter(
            turma=turma,
            data=data_selecionada
        ).select_related('aluno')

        frequencias_dict = {
            str(freq.aluno_id): freq.status
            for freq in frequencias
        }

        context = {
            **self.admin_site.each_context(request),
            'turma': turma,
            'alunos': alunos,
            'data_selecionada': data_selecionada,
            'frequencias_dict': frequencias_dict,
            'opcoes_status': Frequencia.PRESENCA_CHOICES,
            'title': f'Registro de Frequência - {turma.nome} - {turma.escola.nome}',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }

        return TemplateResponse(
            request,
            'admin/core/frequencia/frequencia_form.html',
            context
        )

    def _processar_frequencias(self, request, alunos, turma, data):
        success_count = 0
        error_messages = []
        logger.error(f"Data recebida para processamento: ({date.today().year})")
        today = date.today()
        # Valida a data antes de processar
        try:
            parsed_date = parse_date(data)
            if not parsed_date:
                raise ValueError("Data inválida")
            if parsed_date.year != today.year:
                raise ValueError(f"Data deve ser do ano atual ({today.year})")
        except (ValueError, TypeError) as e:
            logger.error(f"Data inválida recebida para processamento: {data}. Erro: {str(e)}")
            messages.error(request, f"Data deve ser do ano atual ({today.year})")
            return

        # Log para depuração
        logger.debug(f"Processando frequências para turma {turma.id} na data {data}")

        for aluno in alunos:
            if not aluno.turmas.filter(id=turma.id).exists():
                error_messages.append(f"Aluno {aluno.nome} não está matriculado na turma {turma.nome}")
                continue
            status_key = f"status_{aluno.id}"
            status = request.POST.get(status_key)

            # Log dos dados recebidos
            logger.debug(f"Aluno {aluno.id} - chave: {status_key}, valor: {status}")

            if status:  # Só processa se houver um status definido
                try:
                    # Validação do status
                    if status not in dict(Frequencia.PRESENCA_CHOICES):
                        error_messages.append(
                            f"Status inválido para {aluno.nome}. Valor recebido: {status}"
                        )
                        continue

                    # Disciplina é opcional (pode vir do POST ou ser None)
                    disciplina_id = request.POST.get('disciplina_id')

                    # Dados padrão para criação/atualização
                    defaults = {'status': status}
                    if disciplina_id:
                        defaults['disciplina_id'] = disciplina_id

                    # Atualiza ou cria o registro
                    Frequencia.objects.update_or_create(
                        aluno=aluno,
                        turma=turma,
                        data=data,
                        defaults=defaults
                    )
                    success_count += 1
                    logger.debug(f"Frequência salva para aluno {aluno.id}")

                except Exception as e:
                    error_msg = f"Erro ao salvar frequência para {aluno.nome}"
                    error_messages.append(error_msg)
                    logger.error(f"{error_msg}: {str(e)}", exc_info=True)

        # Feedback para o usuário
        if success_count > 0:
            messages.success(
                request,
                f"Frequências salvas com sucesso! ({success_count} registros)"
            )
        if error_messages:
            messages.error(
                request,
                "Erros encontrados:<br>" + "<br>".join(error_messages),
                extra_tags='safe'
            )

        # Log do resultado final
        logger.info(
            f"Processamento de frequências concluído. "
            f"Sucessos: {success_count}, Erros: {len(error_messages)}"
        )

    def status_display(self, obj):
        return obj.get_status_display()

    status_display.short_description = 'Status'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs

    def save_model(self, request, obj, form, change):
        if obj.aluno and not obj.turma:
            # Pega a primeira turma do aluno ou levanta erro se não houver
            turma = obj.aluno.turmas.first()
            if not turma:
                raise ValidationError("O aluno não está matriculado em nenhuma turma")
            obj.turma = turma
        super().save_model(request, obj, form, change)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['data'] = date.today()
        return initial

    def frequencia_link(self, obj):
        url = reverse('admin:frequencia_form', args=[obj.id])
        return format_html('<a class="button" href="{}">Registrar Frequência</a>', url)

    frequencia_link.short_description = 'Frequência'

    def changelist_view(self, request, extra_context=None):
        context = {
            **self.admin_site.each_context(request),
            'title': 'Selecione uma Turma para Registrar Frequência',
            'turmas': Turma.objects.all().order_by('nome'),
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }

        if extra_context:
            context.update(extra_context)

        return TemplateResponse(
            request,
            'admin/core/frequencia/turma_list.html',
            context
        )


#############################################################################
#############################################################################
#############################################################################
#############################################################################


class NumeroAlunosFilter(SimpleListFilter):
    title = 'Número de Alunos'  # Título que aparece no admin
    parameter_name = 'num_alunos'  # Parâmetro usado na URL

    def lookups(self, request, model_admin):
        """
        Retorna as opções de filtro que serão exibidas.
        """
        return (
            ('0', 'Sem alunos'),
            ('1-10', '1 a 10 alunos'),
            ('11-20', '11 a 20 alunos'),
            ('21+', 'Mais de 20 alunos'),
        )

    def queryset(self, request, queryset):
        """
        Filtra o queryset baseado no valor selecionado.
        """
        value = self.value()
        if not value:
            return queryset

        # Annotate each turma with the count of alunos
        queryset = queryset.annotate(num_alunos=Count('alunos'))

        if value == '0':
            return queryset.filter(num_alunos=0)
        elif value == '1-10':
            return queryset.filter(num_alunos__gte=1, num_alunos__lte=10)
        elif value == '11-20':
            return queryset.filter(num_alunos__gte=11, num_alunos__lte=20)
        elif value == '21+':
            return queryset.filter(num_alunos__gte=21)

        return queryset

class TurmaNomeFilter(SimpleListFilter):
    # Título que aparecerá na interface admin
    title = 'Filtrar por Turma'

    # Parâmetro que será usado na URL
    parameter_name = 'turma_nome'

    def lookups(self, request, model_admin):
        """
        Retorna a lista de opções que aparecerão no filtro.
        Cada tupla contém (valor_na_url, label_visivel)
        """
        # Obtém todas as turmas ordenadas por nome
        turmas = Turma.objects.all().order_by('nome')
        return [(turma.id, turma.nome) for turma in turmas]

    def queryset(self, request, queryset):
        """
        Filtra o queryset baseado no valor selecionado no filtro
        """
        if self.value():
            return queryset.filter(id=self.value())
        return queryset

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_filter = (
        'ano',
        'escola',
        'professores',
        NumeroAlunosFilter,
    )
    list_display = ('__str__', 'avaliacao_link', 'alunos_link')
    search_fields = ('nome', 'escola__nome')

    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        custom_urls = [
            path('<int:turma_id>/avaliacao/', self.admin_site.admin_view(self.avaliacao_form_view),
                 name='%s_%s_avaliacao' % (app_label, self.model._meta.model_name)),
            path('<int:turma_id>/alunos/', self.admin_site.admin_view(self.manage_alunos_view),
                 name='%s_%s_alunos' % (app_label, self.model._meta.model_name)),
        ]
        return custom_urls + urls

    def alunos_link(self, obj):
        url = reverse('admin:core_turma_alunos', args=[obj.id])
        return format_html('<a class="button" href="{}">Inserir alunos</a>', url)

    alunos_link.short_description = 'Alunos'

    def manage_alunos_view(self, request, turma_id):
        turma = get_object_or_404(Turma, id=turma_id)

        if request.method == 'POST':
            if 'ra' in request.POST:  # Adicionar aluno
                ra = request.POST.get('ra')
                try:
                    aluno = Aluno.objects.get(ra=ra)
                    turma.alunos.add(aluno)  # Usando o relacionamento ManyToMany
                    messages.success(request, f'Aluno {aluno.nome} adicionado à turma com sucesso!')
                except Aluno.DoesNotExist:
                    messages.error(request, f'Aluno com RA {ra} não encontrado.')

            elif 'aluno_id' in request.POST:  # Remover aluno
                aluno_id = request.POST.get('aluno_id')
                try:
                    aluno = Aluno.objects.get(id=aluno_id)
                    turma.alunos.remove(aluno)  # Usando o relacionamento ManyToMany
                    messages.success(request, f'Aluno {aluno.nome} removido da turma com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao remover aluno: {str(e)}')

            return redirect('admin:core_turma_alunos', turma_id=turma.id)

        alunos = turma.alunos.all().order_by('nome')
        context = {
            **self.admin_site.each_context(request),
            'turma': turma,
            'alunos': alunos,
            'opts': self.model._meta,
        }

        return TemplateResponse(
            request,
            'admin/core/turma/manage_alunos.html',
            context
        )

    def add_aluno_view(self, request, turma_id):
        turma = get_object_or_404(Turma, id=turma_id)

        if request.method == 'POST':
            ra = request.POST.get('ra')
            try:
                aluno = Aluno.objects.get(ra=ra)
                turma.alunos.add(aluno)  # Usa o relacionamento ManyToMany
                messages.success(request, f'Aluno {aluno.nome} adicionado à turma com sucesso!')
                return redirect('admin:core_turma_alunos', turma_id=turma.id)
            except Aluno.DoesNotExist:
                messages.error(request, f'Aluno com RA {ra} não encontrado.')
            except Exception as e:
                messages.error(request, f'Erro ao adicionar aluno: {str(e)}')

        context = {
            **self.admin_site.each_context(request),
            'turma': turma,
            'title': f'Adicionar Aluno - {turma.nome}',
            'opts': self.model._meta,
        }

        return TemplateResponse(
            request,
            'admin/core/turma/add_aluno.html',
            context
        )

    def remove_aluno_view(self, request, turma_id, aluno_id):
        turma = get_object_or_404(Turma, id=turma_id)
        aluno = get_object_or_404(Aluno, id=aluno_id)

        if request.method == 'POST':
            try:
                turma.alunos.remove(aluno)  # Usa o relacionamento ManyToMany
                messages.success(request, f'Aluno {aluno.nome} removido da turma com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao remover aluno: {str(e)}')

        return redirect('admin:core_turma_alunos', turma_id=turma.id)

    def avaliacao_form_view(self, request, turma_id):
        try:
            turma = get_object_or_404(Turma, id=turma_id)
        except Turma.DoesNotExist:
            messages.error(request, f"Turma com ID {turma_id} não encontrada.")
            return redirect('admin:core_turma_changelist')

        # Alterado para usar o relacionamento ManyToMany
        alunos = turma.alunos.all()
        disciplinas = Disciplina.objects.all()
        bimestres = Bimestre.objects.all()

        if not bimestres.exists():
            messages.error(request, "Nenhum bimestre cadastrado. Cadastre um bimestre antes de avaliar.")
            return redirect('admin:core_turma_changelist')

        if not alunos.exists():
            messages.error(request, "Nenhum aluno encontrado para esta turma.")
            return redirect('admin:core_turma_changelist')

        if not disciplinas.exists():
            messages.error(request, "Nenhuma disciplina cadastrada.")
            return redirect('admin:core_turma_changelist')

        # Get the selected bimestre
        bimestre = self._get_bimestre(request, bimestres)

        # Get the selected data_fechamento from GET or POST
        data_fechamento = request.GET.get('data_fechamento') or request.POST.get('data_fechamento')

        # Fetch grades based on turma, bimestre, and data_fechamento
        notas_dict = self._get_notas_dict(turma, bimestre, data_fechamento)

        # Handle POST request (saving grades)
        if request.method == "POST":
            self._processar_notas(request, alunos, disciplinas, bimestre, turma)
            return redirect(
                f"{reverse('admin:core_turma_avaliacao', args=[turma.id])}?bimestre={bimestre.id}&data_fechamento={data_fechamento}")

        # Handle GET request (displaying the form)
        context = self._prepare_context(request, turma, alunos, disciplinas, bimestres, bimestre, notas_dict,
                                        data_fechamento)
        return render(request, 'admin/core/turma/avaliacao_form.html', context)

    def _get_bimestre(self, request, bimestres):
        bimestre_id = request.POST.get('bimestre') or request.GET.get('bimestre')
        if bimestre_id:
            return get_object_or_404(Bimestre, id=bimestre_id)
        return bimestres.first()

    def avaliacao_link(self, obj):
        url = reverse('admin:core_turma_avaliacao', args=[obj.id])
        return format_html('<a href="{}">Gerenciar Avaliações</a>', url)

    avaliacao_link.short_description = 'Avaliações'

    def _get_notas_dict(self, turma, bimestre, data_fechamento=None):
        logger.debug(f"Buscando notas para turma {turma.id}, bimestre {bimestre.id}, data_fechamento {data_fechamento}")
        # Start with base query filtering by turma and bimestre
        query = Avaliacao.objects.filter(turma=turma, bimestre=bimestre)

        # If data_fechamento is provided, add it to the filter
        if data_fechamento:
            query = query.filter(data_fechamento=data_fechamento)

        avaliacoes = query
        logger.debug(f"[get_notas_dict] Avaliacoes encontradas: {list(avaliacoes)}")
        notas_dict = {}
        for av in avaliacoes:
            aluno_id = str(av.aluno.id)
            disciplina_id = str(av.disciplina.id)
            if aluno_id not in notas_dict:
                notas_dict[aluno_id] = {}
            notas_dict[aluno_id][disciplina_id] = str(av.nota) if av.nota is not None else ''
        return notas_dict

    def _processar_notas(self, request, alunos, disciplinas, bimestre, turma):
        success_count = 0
        error_messages = []
        data_fechamento = request.POST.get('data_fechamento', '').strip()

        for aluno in alunos:
            for disciplina in disciplinas:
                nota_key = f"nota_{aluno.id}_{disciplina.id}"
                nota = request.POST.get(nota_key, '').strip()

                if nota:
                    try:
                        nota = float(nota.replace(',', '.'))
                        if not (0 <= nota <= 10):
                            error_messages.append(
                                f"Nota inválida para {aluno.nome} em {disciplina.nome}. "
                                f"Deve estar entre 0 e 10."
                            )
                            continue

                        Avaliacao.objects.update_or_create(
                            aluno=aluno,
                            disciplina=disciplina,
                            bimestre=bimestre,
                            turma=turma,
                            defaults={
                                'nota': nota,
                                'data_fechamento': data_fechamento if data_fechamento else None
                            }
                        )
                        success_count += 1

                    except ValueError:
                        error_messages.append(
                            f"Nota inválida para {aluno.nome} em {disciplina.nome}. "
                            f"Deve ser um número."
                        )

        if success_count > 0:
            messages.success(request,
                             f"Notas salvas com sucesso! ({success_count} atualizações)"
                             )
        if error_messages:
            messages.error(request,
                           "Erros encontrados:<br>" + "<br>".join(error_messages),
                           extra_tags='safe'
                           )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Lista de Turmas'
        return super().changelist_view(request, extra_context=extra_context)

    def _prepare_context(self, request, turma, alunos, disciplinas, bimestres, bimestre, notas_dict, data_fechamento):
        context = self.admin_site.each_context(request)
        # Format data_fechamento for display
        formatted_data_fechamento = None
        if not data_fechamento:
            avaliacao = Avaliacao.objects.filter(turma=turma, bimestre=bimestre).first()
            data_fechamento = avaliacao.data_fechamento.strftime(
                '%Y-%m-%d') if avaliacao and avaliacao.data_fechamento else '2025-04-16'

        # Convert data_fechamento to DD/MM/YYYY format
        if data_fechamento:
            try:
                date_obj = datetime.strptime(data_fechamento, '%Y-%m-%d')
                formatted_data_fechamento = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                formatted_data_fechamento = data_fechamento  # Fallback to raw value

        return context


#############################################################################
#############################################################################
#############################################################################
############################################################################# 
@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'link_avaliacoes')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:turma_id>/avaliacao/', self.admin_site.admin_view(self.avaliacao_form_view),
                 name='core_avaliacao_form'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        escolas = Escola.objects.all().order_by('nome')
        turmas = Turma.objects.all().select_related('escola')

        # Filtros: escola, turma, ano
        escola_id = request.GET.get('escola')
        turma_id = request.GET.get('turma')
        ano = request.GET.get('ano')

        if escola_id and escola_id.isdigit():
            turmas = turmas.filter(escola_id=escola_id)
        if turma_id and turma_id.isdigit():
            turmas = turmas.filter(id=turma_id)
        if ano and ano.isdigit():
            turmas = turmas.filter(ano=ano)

        # Se quiser ordenar por ano/turma, etc.
        turmas = turmas.order_by('ano', 'nome')

        # Prepara lista de turmas para o select (opcional)
        turmas_filter = Turma.objects.all().order_by('nome')

        extra_context.update({
            'title': 'Clique em um card para ver as avaliações',
            'escolas': escolas,
            'turmas': turmas,
            'turmas_filter': turmas_filter,  # Para o filtro Turma
            'ano_selecionado': ano,
            'escola_selecionada': escola_id,
            'turma_selecionada': turma_id,
            'anos_disponiveis': Turma.objects.values_list('ano', flat=True).distinct().order_by('ano'),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def avaliacao_form_view(self, request, turma_id):
        try:
            turma = get_object_or_404(Turma, id=turma_id)
            alunos = turma.alunos.all()
        except Turma.DoesNotExist:
            messages.error(request, f"Turma com ID {turma_id} não encontrada.")
            return redirect('admin:core_avaliacao_changelist')

        alunos = turma.alunos.all()
        disciplinas = Disciplina.objects.all()
        bimestres = Bimestre.objects.all()

        if not bimestres.exists():
            messages.error(request, "Nenhum bimestre cadastrado. Cadastre um bimestre antes de avaliar.")
            return redirect('admin:core_avaliacao_changelist')

        if not alunos.exists():
            messages.error(request, "Nenhum aluno encontrado para esta turma.")
            return redirect('admin:core_avaliacao_changelist')

        if not disciplinas.exists():
            messages.error(request, "Nenhuma disciplina cadastrada.")
            return redirect('admin:core_avaliacao_changelist')

        # Get the selected bimestre
        bimestre = self._get_bimestre(request, bimestres)

        # Get the selected data_fechamento from GET or POST
        data_fechamento = request.GET.get('data_fechamento') or request.POST.get('data_fechamento')

        # Fetch grades based on turma, bimestre, and data_fechamento
        notas_dict = self._get_notas_dict(turma, bimestre, data_fechamento)

        # Handle POST request (saving grades)
        if request.method == "POST":
            self._processar_notas(request, alunos, disciplinas, bimestre, turma)
            return redirect(
                f"{reverse('admin:core_avaliacao_form', args=[turma.id])}?bimestre={bimestre.id}&data_fechamento={data_fechamento}")

        # Handle GET request (displaying the form)
        context = self._prepare_context(request, turma, alunos, disciplinas, bimestres, bimestre, notas_dict,
                                        data_fechamento)
        return render(request, 'admin/core/avaliacao/avaliacao_form.html', context)

    def _get_bimestre(self, request, bimestres):
        bimestre_id = request.POST.get('bimestre') or request.GET.get('bimestre')
        if bimestre_id:
            return get_object_or_404(Bimestre, id=bimestre_id)
        return bimestres.first()

    def _get_notas_dict(self, turma, bimestre, data_fechamento=None):
        logger.debug(f"[get_notas_dict] Turma ID: {turma.id}, Nome: {turma.nome}")
        logger.debug(f"[get_notas_dict] Bimestre ID: {bimestre.id}, Nome: {bimestre.nome}")
        logger.debug(f"[get_notas_dict] Data Fechamento: {data_fechamento}")
        # Start with base query filtering by turma and bimestre
        query = Avaliacao.objects.filter(turma=turma, bimestre=bimestre)

        # If data_fechamento is provided, add it to the filter
        if data_fechamento:
            query = query.filter(data_fechamento=data_fechamento)

        avaliacoes = query
        logger.debug(f"[get_notas_dict] Avaliacoes encontradas: {list(avaliacoes)}")
        notas_dict = {}
        for av in avaliacoes:
            aluno_id = str(av.aluno.id)
            disciplina_id = str(av.disciplina.id)
            if aluno_id not in notas_dict:
                notas_dict[aluno_id] = {}
            notas_dict[aluno_id][disciplina_id] = str(av.nota) if av.nota is not None else ''
            logger.debug(
                f"[get_notas_dict] Added: aluno {aluno_id}, disciplina {disciplina_id}, nota {notas_dict[aluno_id][disciplina_id]}")
        logger.debug(f"[get_notas_dict] Final notas_dict: {notas_dict}")
        return notas_dict

    def _processar_notas(self, request, alunos, disciplinas, bimestre, turma):
        success_count = 0
        error_count = 0
        data_fechamento = request.POST.get('data_fechamento', '').strip()

        for aluno in alunos:
            for disciplina in disciplinas:
                nota_key = f"nota_{aluno.id}_{disciplina.id}"
                nota = request.POST.get(nota_key, '').strip()

                if nota:
                    try:
                        nota = float(nota.replace(',', '.'))
                        if not (0 <= nota <= 10):
                            messages.error(request,
                                           f"Nota inválida para {aluno.nome} em {disciplina.nome}. "
                                           f"Deve estar entre 0 e 10."
                                           )
                            error_count += 1
                            continue

                        Avaliacao.objects.update_or_create(
                            aluno=aluno,
                            disciplina=disciplina,
                            bimestre=bimestre,
                            turma=turma,
                            defaults={
                                'nota': nota,
                                'data_fechamento': data_fechamento if data_fechamento else None
                            }
                        )
                        success_count += 1

                    except ValueError:
                        messages.error(request,
                                       f"Nota inválida para {aluno.nome} em {disciplina.nome}. "
                                       f"Deve ser um número."
                                       )
                        error_count += 1

        if success_count > 0:
            messages.success(request,
                             f"Notas salvas com sucesso! ({success_count} atualizações)"
                             )
        if error_count > 0:
            messages.warning(request,
                             f"{error_count} notas não puderam ser salvas devido a erros."
                             )

    def _prepare_context(self, request, turma, alunos, disciplinas, bimestres, bimestre, notas_dict, data_fechamento):
        context = self.admin_site.each_context(request)
        # Format data_fechamento for display
        formatted_data_fechamento = None
        if not data_fechamento:
            avaliacao = Avaliacao.objects.filter(turma=turma, bimestre=bimestre).first()
            data_fechamento = avaliacao.data_fechamento.strftime(
                '%Y-%m-%d') if avaliacao and avaliacao.data_fechamento else '2025-04-16'

        # Convert data_fechamento to DD/MM/YYYY format
        if data_fechamento:
            try:
                date_obj = datetime.strptime(data_fechamento, '%Y-%m-%d')
                formatted_data_fechamento = date_obj.strftime('%d/%m/%Y')
            except ValueError:
                formatted_data_fechamento = data_fechamento  # Fallback to raw value

        context.update({
            'turma': turma,
            'alunos': alunos,
            'disciplinas': disciplinas,
            'bimestres': bimestres,
            'bimestre_selecionado': bimestre,
            'notas_dict': notas_dict,
            'title': f'Avaliação - {turma.nome}',
            'data_fechamento': data_fechamento,
            'formatted_data_fechamento': formatted_data_fechamento,
        })
        return context

    def link_avaliacoes(self, obj):
        url = reverse('admin:core_avaliacao_changelist')
        return format_html('<a href="{}">Gerenciar Avaliações</a>', url)

    link_avaliacoes.short_description = 'Ações'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class DiaLetivoForm(forms.ModelForm):
    class Meta:
        model = DiaLetivo
        fields = '__all__'


#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(PeriodoLetivo)
class PeriodoLetivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'ano', 'data_inicio', 'data_fim', 'ativo', 'calendario_link')
    # list_filter = ('tipo', 'ano', 'ativo')
    # search_fields = ('nome',)
    date_hierarchy = 'data_inicio'
    list_display_links = ('nome', 'tipo')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:periodo_id>/calendario/', self.admin_site.admin_view(self.calendario_view),
                 name='core_periodoletivo_calendario'),
        ]
        return custom_urls + urls

    def calendario_escolar_view(self, request):
        """View completa do calendário escolar"""
        # 1. Obter o período letivo ativo
        try:
            periodo_letivo = PeriodoLetivo.objects.get(ativo=True)
        except PeriodoLetivo.DoesNotExist:
            return render(request, 'admin/core/calendario_escolar.html', {
                'error': 'Nenhum período letivo ativo encontrado'
            })

        # 2. Obter todos os dias letivos do período
        dias_letivos = DiaLetivo.objects.filter(periodo_letivo=periodo_letivo).order_by('data')

        # 3. Preparar cabeçalho com dias 1-31
        dias_cabecalho = [str(dia) for dia in range(1, 32)]

        # 4. Organizar dias por mês
        calendario = defaultdict(list)
        meses_ordenados = [
            'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL',
            'MAIO', 'JUNHO', 'JULHO', 'AGOSTO',
            'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
        ]

        # 5. Contar dias letivos por mês
        dias_letivos_por_mes = defaultdict(int)
        total_dias_letivos = 0

        for mes_num, mes_nome in enumerate(meses_ordenados, start=1):
            # Dias do mês
            _, ultimo_dia = monthrange(periodo_letivo.ano, mes_num)

            # Preencher dias do mês
            dias_mes = []
            for dia in range(1, ultimo_dia + 1):
                data_atual = date(periodo_letivo.ano, mes_num, dia)

                # Verificar se é dia letivo
                dia_letivo = next((d for d in dias_letivos if d.data == data_atual), None)

                if dia_letivo:
                    dias_mes.append({
                        'dia': dia,
                        'status': dia_letivo.status,
                        'data': data_atual
                    })
                    if dia_letivo.status == 'L':  # Dia Letivo normal
                        dias_letivos_por_mes[mes_nome] += 1
                        total_dias_letivos += 1
                else:
                    # Dias não cadastrados (finais de semana)
                    if data_atual.weekday() >= 5:  # Sábado ou Domingo
                        dias_mes.append({
                            'dia': dia,
                            'status': 'S' if data_atual.weekday() == 5 else 'D',
                            'data': data_atual
                        })
                    else:
                        dias_mes.append({
                            'dia': dia,
                            'status': '',
                            'data': data_atual
                        })

            calendario[mes_nome] = dias_mes

        # 6. Obter informações dos bimestres
        bimestres = Bimestre.objects.filter(ano_letivo=periodo.ano).order_by('nome')

        # 7. Preparar dados para a tabela de resumo
        resumo_bimestres = []
        for bimestre in bimestres:
            dias_bimestre = DiaLetivo.objects.filter(
                periodo_letivo=periodo,
                data__gte=bimestre.data_inicio,
                data__lte=bimestre.data_fim,
                status='L'
            ).count()
            resumo_bimestres.append({
                'nome': bimestre.nome,
                'inicio': bimestre.data_inicio.strftime('%d/%m') if bimestre.data_inicio else '',
                'fim': bimestre.data_fim.strftime('%d/%m') if bimestre.data_fim else '',
                'dias': dias_bimestre
            })

        bimestre_total = sum(bimestre['dias'] for bimestre in resumo_bimestres)
        if bimestre_total != total_dias_letivos:
            logger.warning(
                f"[calendario_view] Mismatch: Sum of bimestre days ({bimestre_total}) does not match total school days ({total_dias_letivos})")
            # Optionally, adjust total_dias_letivos to match bimestre_total
            total_dias_letivos = bimestre_total

        context = {
            **self.admin_site.each_context(request),
            'dias_cabecalho': dias_cabecalho,
            'calendario': calendario,
            'dias_letivos_por_mes': dias_letivos_por_mes,
            'total_dias_letivos': total_dias_letivos,
            'resumo_bimestres': resumo_bimestres,
            'periodo_letivo': periodo_letivo,
            'title': 'Calendário Escolar',
            'opts': self.model._meta,
        }

        return render(request, 'admin/core/calendario_escolar.html', context)

    def calculate_easter_sunday(self, year):
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    def get_holidays_for_year(self, year):
        # Calcular Domingo de Páscoa e feriados relacionados
        easter_sunday = self.calculate_easter_sunday(year)
        good_friday = easter_sunday - timedelta(days=2)
        carnival_monday = easter_sunday - timedelta(days=48)  # 48 dias antes da Páscoa (segunda-feira)
        carnival_tuesday = easter_sunday - timedelta(days=47)  # 47 dias antes da Páscoa (terça-feira)
        corpus_christi = easter_sunday + timedelta(days=60)

        # Feriados fixos
        holidays = [
            date(year, 1, 1),  # Ano Novo
            date(year, 4, 21),  # Tiradentes
            date(year, 5, 1),  # Dia do Trabalho
            date(year, 9, 7),  # Independência do Brasil
            date(year, 10, 12),  # Nossa Senhora Aparecida
            date(year, 11, 2),  # Finados
            date(year, 11, 15),  # Proclamação da República
            date(year, 12, 25),  # Natal
        ]

        # Feriados variáveis
        holidays.extend([
            carnival_monday,
            carnival_tuesday,
            good_friday,
            corpus_christi,
        ])

        return holidays

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Crie um calendário novo ou visualize e edite um calendário!'
        return super().changelist_view(request, extra_context=extra_context)

    def calendario_view(self, request, periodo_id):
        logger.debug(f"[calendario_view] Iniciando para periodo_id={periodo_id}")

        periodo = get_object_or_404(PeriodoLetivo, id=periodo_id)
        # Armazenar o ano na sessão
        request.session['ano_calendario'] = periodo.ano
        meses = [
            ('JANEIRO', 1), ('FEVEREIRO', 2), ('MARÇO', 3), ('ABRIL', 4),
            ('MAIO', 5), ('JUNHO', 6), ('JULHO', 7), ('AGOSTO', 8),
            ('SETEMBRO', 9), ('OUTUBRO', 10), ('NOVEMBRO', 11), ('DEZEMBRO', 12)
        ]

        # Obter feriados para o ano
        holidays = self.get_holidays_for_year(periodo.ano)
        dias_cabecalho = [str(dia) for dia in range(1, 32)]

        # Calcular dias letivos por mês (apenas status 'L')
        dias_letivos_por_mes = {mes_nome: 0 for mes_nome, _ in meses}
        total_dias_letivos = 0

        # Gerar o calendário para o ano
        calendario = {}
        for mes_nome, mes_num in meses:
            dias_do_mes = []
            for dia in range(1, monthrange(periodo.ano, mes_num)[1] + 1):
                data_atual = date(periodo.ano, mes_num, dia)
                dia_letivo = DiaLetivo.objects.filter(
                    periodo_letivo=periodo,
                    data=data_atual
                ).first()

                if data_atual in holidays:
                    status = 'FE'
                elif dia_letivo:
                    status = dia_letivo.status
                    if status == 'L':  # Só conta se for status 'L'
                        dias_letivos_por_mes[mes_nome] += 1
                        total_dias_letivos += 1
                else:
                    # Dias não cadastrados (não são considerados letivos)
                    status = 'S' if data_atual.weekday() == 5 else 'D' if data_atual.weekday() == 6 else ''

                dias_do_mes.append({'dia': dia, 'status': status})

            calendario[mes_nome] = dias_do_mes

        # Obter informações dos bimestres para a tabela de resumo
        bimestres = Bimestre.objects.filter(ano_letivo=periodo.ano).order_by('nome')
        resumo_bimestres = []
        for bimestre in bimestres:
            dias_bimestre = DiaLetivo.objects.filter(
                periodo_letivo=periodo,
                data__gte=bimestre.data_inicio,
                data__lte=bimestre.data_fim,
                status='L'  # Conta apenas dias com status 'L'
            ).count()

            resumo_bimestres.append({
                'nome': bimestre.nome,
                'inicio': bimestre.data_inicio.strftime('%d/%m') if bimestre.data_inicio else '',
                'fim': bimestre.data_fim.strftime('%d/%m') if bimestre.data_fim else '',
                'dias': dias_bimestre
            })

        # Calcular a soma dos dias dos bimestres
        soma_bimestre_dias = sum(bimestre['dias'] for bimestre in resumo_bimestres)

        # Verificar consistência
        if soma_bimestre_dias != total_dias_letivos:
            logger.warning(
                f"Divergência na contagem: "
                f"Total dias letivos={total_dias_letivos}, "
                f"Soma bimestres={soma_bimestre_dias}"
            )
            # Manter a contagem baseada nos dias letivos reais
            total_dias_letivos = soma_bimestre_dias

        context = {
            **self.admin_site.each_context(request),
            'periodo': periodo,
            'calendario': dict(calendario),
            'dias_letivos_por_mes': dias_letivos_por_mes,
            'total_dias_letivos': total_dias_letivos,
            'meses': meses,
            'dias_cabecalho': dias_cabecalho,
            'resumo_bimestres': resumo_bimestres,
            'soma_bimestre_dias': soma_bimestre_dias,
            'title': f'Calendário Escolar - {periodo.nome} ({periodo.ano})',
            'opts': self.model._meta,
        }

        return TemplateResponse(request, 'admin/core/periodo_letivo/calendario.html', context)

    def calendario_link(self, obj):
        url = reverse('admin:core_periodoletivo_calendario', args=[obj.id])
        return format_html('<a class="button" href="{}">Gerenciar Calendário</a>', url)

    calendario_link.short_description = 'Calendário'


#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome',)

    # search_fields = ('nome',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        disciplinas = Disciplina.objects.all()
        extra_context['title'] = 'Clique em uma disciplina para modificar'
        extra_context['disciplinas'] = disciplinas
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
        ]
        return custom_urls + urls


#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(Bimestre)
class BimestreAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ano_letivo', 'data_inicio', 'data_fim', 'dias_letivo')
    list_filter = ('ano_letivo',)
    ordering = ('-ano_letivo', 'nome')

    def changelist_view(self, request, extra_context=None):
        bimestres = Bimestre.objects.all().order_by('-ano_letivo', 'nome')
        extra_context = extra_context or {}
        extra_context['title'] = 'Adicione um novo Bimestre ou clique em um para modificar'

        # Criar estrutura de dados que o template espera
        bimestres_by_year = {}
        for bimestre in bimestres:
            year = bimestre.ano_letivo
            if year not in bimestres_by_year:
                bimestres_by_year[year] = {
                    'bimestres': [],
                    'total_dias_letivos': 0
                }
            bimestres_by_year[year]['bimestres'].append(bimestre)
            bimestres_by_year[year]['total_dias_letivos'] += bimestre.dias_letivo

        # Ordenar os anos
        bimestres_by_year = dict(sorted(bimestres_by_year.items(), reverse=True))

        extra_context = extra_context or {}
        extra_context.update({
            'bimestres_by_year': bimestres_by_year,
            'bimestres_count': bimestres.count(),
        })

        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        return urls


#############################################################################
#############################################################################
#############################################################################
#############################################################################
from django.contrib import admin, messages
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.db.models import Count, Max, Case, When, Value, IntegerField, CharField, Q

from datetime import date, timedelta

from .models import DiretoriaEnsino, Escola, Professor, Aluno, Frequencia, Turma

@admin.register(DiretoriaEnsino)
class DiretoriaEnsinoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'endereco', 'report_link')
    ordering = ('nome',)
    change_list_template = 'admin/core/diretoriaensino/change_list.html'

    # --- Conjuntos de status (ajuste conforme seus choices) ---
    PRESENTES = {'P', 'p', 'presente', 'Presente'}
    AUSENTES = {'A', 'a', 'ausente', 'Ausente'}
    JUSTIFICADAS = {'J', 'j', 'justificada', 'Justificada', 'AJ', 'aj'}  # se existir

    def _get_periodo(self, request):
        """Retorna (data_ini, data_fim) com fallback para últimos 30 dias."""
        data_ini = request.GET.get('data_ini')
        data_fim = request.GET.get('data_fim')
        if data_ini and data_fim:
            return data_ini, data_fim
        hoje = date.today()
        return (hoje - timedelta(days=30)).strftime('%Y-%m-%d'), hoje.strftime('%Y-%m-%d')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reports/', self.admin_site.admin_view(self.reports_view),
                 name='core_diretoriaensino_reports'),
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view)),
            path('schools-chart/', self.admin_site.admin_view(self.schools_chart_view),
                 name='core_diretoriaensino_schools_chart'),
            path('dashboard-detalhado/', self.admin_site.admin_view(self.dashboard_detalhado_view),
                 name='core_diretoriaensino_dashboard_detalhado'),
        ]
        return custom_urls + urls

    # ----------------- HELPERS -----------------
    def base_frequencias_filtradas(self, request):
        data_ini, data_fim = self._get_periodo(request)
        escola_id = request.GET.get('escola_id')
        turma_id = request.GET.get('turma_id')
        professor_id = request.GET.get('professor_id')

        qs = Frequencia.objects.filter(data__range=[data_ini, data_fim])

        if escola_id and escola_id != 'all':
            qs = qs.filter(turma__escola_id=escola_id)
        if turma_id:
            qs = qs.filter(turma_id=turma_id)
        if professor_id:
            qs = qs.filter(turma__professores__id=professor_id)

        return qs

    def schools_chart_view(self, request):
        data_ini = request.GET.get('data_ini')
        data_fim = request.GET.get('data_fim')
        escola_id = request.GET.get('escola_id')

        frequencias = Frequencia.objects.all()
        if data_ini and data_fim:
            frequencias = frequencias.filter(data__range=[data_ini, data_fim])
        if escola_id:
            frequencias = frequencias.filter(turma__escola__id=escola_id)

        labels, valores = [], []
        qs_escolas = Escola.objects.all()
        for escola in qs_escolas:
            if escola_id and str(escola.id) != str(escola_id):
                continue
            # total de presenças no período por escola (ajuste conforme sua métrica)
            total = frequencias.filter(turma__escola=escola, status='presente').count()
            labels.append(escola.nome)
            valores.append(total)

        data = {
            'labels': labels,
            'datasets': [{
                'label': 'Presenças no Período',
                'data': valores,
            }],
            'data': valores,  # opcional, para facilitar no front
        }
        return JsonResponse(data)

    def consolida_por_aluno_dia(self, qs):
        """
        Consolida um 'marcador' por (aluno, data):
        - 'A' se houve qualquer ausência no dia
        - senão 'P' se houve presença
        - senão 'NA'
        Também cria 'marcador2' opcional 'AJ' para ausência justificada.
        """
        agrupado = (
            qs.values('aluno_id', 'data')
              .annotate(
                  tem_ausencia=Max(
                      Case(When(status__in=self.AUSENTES, then=1),
                           default=0, output_field=IntegerField())
                  ),
                  tem_presenca=Max(
                      Case(When(status__in=self.PRESENTES, then=1),
                           default=0, output_field=IntegerField())
                  ),
                  tem_just=Max(
                      Case(When(status__in=self.JUSTIFICADAS, then=1),
                           default=0, output_field=IntegerField())
                  ),
              )
              .annotate(
                  marcador=Case(
                      When(tem_ausencia__gt=0, then=Value('A')),
                      When(tem_presenca__gt=0, then=Value('P')),
                      default=Value('NA'),
                      output_field=CharField()
                  ),
                  marcador2=Case(
                      When(tem_ausencia__gt=0, tem_just__gt=0, then=Value('AJ')),
                      default=Value(None),
                      output_field=CharField()
                  ),
              )
        )
        return agrupado

    # ----------------- VIEWS -----------------
    def schools_chart_view(self, request):
        """
        Dataset 0: Alunos por Escola  (sempre populado)
        Dataset 1: Presenças (aluno-dia) no período (opcional)
        """
        data_ini, data_fim = self._get_periodo(request)
        escola_id = request.GET.get('escola_id')

        # Escolas a considerar
        escolas_qs = Escola.objects.all().order_by('nome')
        if escola_id and escola_id != 'all':
            escolas_qs = escolas_qs.filter(id=escola_id)

        # --- Alunos por escola (distinct via M2M turmas) ---
        alunos_por_escola = (
            Aluno.objects
            .filter(turmas__escola__in=escolas_qs)
            .values('turmas__escola__id', 'turmas__escola__nome')
            .distinct()
            .values('turmas__escola__id', 'turmas__escola__nome')
            .annotate(qt=Count('id'))
        )
        # Mapeia id -> contagem de alunos
        alunos_map = {r['turmas__escola__id']: r['qt'] for r in alunos_por_escola}

        # --- Presenças por escola no período (aluno-dia, consolidado) ---
        qs_freq = Frequencia.objects.filter(data__range=[data_ini, data_fim])
        if escola_id and escola_id != 'all':
            qs_freq = qs_freq.filter(turma__escola_id=escola_id)

        # consolida por aluno-dia e mantém apenas 'P'
        agrupado = (
            qs_freq.values('aluno_id', 'data',
                           'turma__escola__id', 'turma__escola__nome')
            .annotate(
                tem_presenca=Max(
                    Case(When(status__in=self.PRESENTES, then=1),
                         default=0, output_field=IntegerField())
                )
            )
            .filter(tem_presenca__gt=0)
            .distinct()
            .values('turma__escola__id', 'turma__escola__nome')
            .annotate(qt=Count('turma__escola__id'))
        )
        presentes_map = {r['turma__escola__id']: r['qt'] for r in agrupado}

        # --- Monta labels e séries na mesma ordem das escolas ---
        labels = [e.nome for e in escolas_qs]
        serie_alunos = [alunos_map.get(e.id, 0) for e in escolas_qs]
        serie_presencas = [presentes_map.get(e.id, 0) for e in escolas_qs]

        return JsonResponse({
            'labels': labels,
            'datasets': [
                {'label': 'Alunos por Escola', 'data': serie_alunos},
                {'label': 'Presenças (aluno-dia) no período', 'data': serie_presencas},
            ],
            # compat com seu JS atual:
            'data': serie_alunos,
        })

    def dashboard_detalhado_view(self, request):
        qs = self.base_frequencias_filtradas(request)

        filtro_presente = Q(status__in=self.PRESENTES)
        filtro_ausente = Q(status__in=self.AUSENTES)

        total_presente = qs.filter(filtro_presente).count()
        total_ausente = qs.filter(filtro_ausente).count()

        professores_com_chamada = Professor.objects.filter(turmas__frequencia__in=qs).distinct()
        professores_sem_chamada = Professor.objects.exclude(id__in=professores_com_chamada.values('id'))

        data = {
            'professores_com_chamada': list(professores_com_chamada.values('id', 'nome')),
            'professores_sem_chamada': list(professores_sem_chamada.values('id', 'nome')),
            'total_presente': total_presente,
            'total_ausente': total_ausente,
        }
        return JsonResponse(data)

    def dashboard_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            'total_escolas': Escola.objects.count(),
            'total_alunos': Aluno.objects.count(),
            'total_professores': Professor.objects.count(),
            'title': 'Dashboard Administrativo',
        }
        return TemplateResponse(request, 'admin/core/dashboard.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Visão geral do município',
            'departamentos': DiretoriaEnsino.objects.all(),
            'total_escolas': Escola.objects.count(),
            'total_alunos': Aluno.objects.count(),
            'total_professores': Professor.objects.count(),
            'escolas': Escola.objects.all(),
            # defaults para o template até o fetch preencher
            'alunos_presentes': 0,
            'alunos_ausentes': 0,
            'professores_com_chamada': 0,
            # compat admin
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        })
        return super().changelist_view(request, extra_context=extra_context)

    def reports_view(self, request):
        schools = Escola.objects.all()
        students_by_school = [
            {
                'name': school.nome,
                'count': Aluno.objects.filter(turmas__escola=school).distinct().count()
            }
            for school in schools
        ]

        context = {
            **self.admin_site.each_context(request),
            'title': 'Relatórios da Diretoria de Ensino',
            'schools': schools,
            'students_by_school': students_by_school,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/core/diretoriaensino/reports.html', context)

    def report_link(self, obj):
        url = reverse('admin:core_diretoriaensino_reports')
        return format_html('<a class="button" href="{}">Ver Relatórios</a>', url)
    report_link.short_description = 'Relatórios'

#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(Diretor)
class DiretorAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone")

    # search_fields = ("nome", "cpf")
    # ordering = ("nome",)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Adicione um novo Diretor ou clique em um para modificar'
        return super().changelist_view(request, extra_context=extra_context)

    # Opcional: desative ações em massa se não forem necessárias
    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


#############################################################################
#############################################################################
#############################################################################
#############################################################################
class EscolaForm(forms.ModelForm):
    """Formulário personalizado para o modelo Escola."""

    class Meta:
        model = Escola
        fields = '__all__'
        labels = {
            'diretoria_ensino': 'Diretoria Regional de Ensino',
            'diretor': 'Diretor Responsável'
        }
        help_texts = {
            'cnpj': 'Formato: 00.000.000/0000-00',
            'cep': 'Formato: 00000-000'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_field_attributes()
        self.set_required_fields()

    def set_field_attributes(self):
        """Configura atributos comuns para os campos."""
        for field in self.fields:
            if isinstance(self.fields[field], forms.CharField):
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })

    def set_required_fields(self):
        """Define campos obrigatórios."""
        required_fields = ['nome', 'diretoria_ensino', 'cidade', 'estado']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

    def clean_cnpj(self):
        """Validação customizada para o CNPJ."""
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Implementar validação real do CNPJ aqui
            if len(cnpj) != 18:
                raise forms.ValidationError("CNPJ deve ter 14 dígitos")
        return cnpj


#############################################################################
#############################################################################
#############################################################################
#############################################################################
@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ('nome',)  # Adjust based on your fields
    list_filter = ('ativa',)

    # search_fields = ('nome',)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        escolas = Escola.objects.all()

        ativa = request.GET.get('ativa')
        if ativa in ['1', '0']:
            escolas = escolas.filter(ativa=bool(int(ativa)))

        extra_context['title'] = 'Clique no editor do card para visualizar ou modificar'
        extra_context['escolas'] = escolas
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:escola_id>/delete/',
                self.admin_site.admin_view(self.delete_escola_view),
                name='core_escola_delete',
            ),
        ]
        return custom_urls + urls

    def delete_escola_view(self, request, escola_id):
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        escola = get_object_or_404(Escola, id=escola_id)

        if request.method == 'POST':
            try:
                escola.delete()
                messages.success(request, f'Escola "{escola.nome}" excluída com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao excluir escola: {str(e)}')
            return redirect('admin:core_escola_changelist')

        return redirect('admin:core_escola_changelist')


class ProfessorAdminForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = [
            'nome', 'cpf', 'data_nascimento', 'sexo',
            'endereco', 'telefone', 'disciplinas', 'turmas'
        ]
        widgets = {
            'disciplinas': forms.SelectMultiple(attrs={'class': 'select2'}),
            'turmas': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar a exibição dos campos ManyToMany
        self.fields['disciplinas'].help_text = "Selecione as disciplinas que o professor leciona."
        self.fields['turmas'].help_text = "Selecione as turmas associadas ao professor."
        self.fields['disciplinas'].queryset = Disciplina.objects.all().order_by('nome')
        self.fields['turmas'].queryset = Turma.objects.all().order_by('nome')


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    form = ProfessorAdminForm
    search_fields = ("nome", "cpf")
    ordering = ("nome",)
    change_list_template = 'admin/core/professor/change_list.html'
    list_filter = [
        'turmas',
        'turmas__escola',
        'disciplinas',
    ]

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',)
        }
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
            '/static/js/admin_select2.js',
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['escolas'] = Escola.objects.all()
        extra_context['turmas'] = Turma.objects.all()
        extra_context['disciplinas'] = Disciplina.objects.all()
        extra_context['title'] = "Adicione, edite ou exclua um professor"
        return super().changelist_view(request, extra_context)

    def get_disciplinas(self, obj):
        return ", ".join([disciplina.nome for disciplina in obj.disciplinas.all()])

    get_disciplinas.short_description = 'Disciplinas'

    def get_turmas(self, obj):
        return ", ".join([turma.nome for turma in obj.turmas.all()])

    get_turmas.short_description = 'Turmas'

