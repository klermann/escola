from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import MultipleObjectsReturned
import json
from django.core.exceptions import ValidationError
import logging
from django.db.models import Sum
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import Calendario
from django.db import transaction
from core.models import DiaLetivo, PeriodoLetivo
from django.contrib.auth.decorators import login_required, permission_required
from .models import Aviso, Boletim
from django.db.models import Q
import re
from typing import Dict, List, Optional, Any
from django.shortcuts import resolve_url
import warnings
from urllib.parse import urlparse, urlunparse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import (
    AuthenticationForm,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import resolve_url
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.deprecation import RemovedInDjango50Warning
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from .models import Aluno, Avaliacao, Frequencia, Disciplina, Bimestre, Turma
from site_admin.models import HeroContent, FeatureBlock
from datetime import datetime, date

logger = logging.getLogger(__name__)

csrf_protect
@login_required
def api_frequencias_alunos(request):
    data = request.GET.get('data')
    turma_id = request.GET.get('turma_id')

    try:
        # Converte a string da data para objeto date
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()

        # Busca todas as frequências para esta data e turma
        frequencias = Frequencia.objects.filter(
            data=data_obj,
            turma_id=turma_id
        ).values('aluno_id', 'status')

        return JsonResponse(list(frequencias), safe=False)

    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=400
        )

csrf_protect
@login_required
def api_frequencias(request):
    turma_id = request.GET.get('turma_id')
    frequencias = Frequencia.objects.filter(turma_id=turma_id).values('data', 'status')
    return JsonResponse(list(frequencias), safe=False)

@csrf_protect
@login_required
def dias_letivos_api(request):
    try:
        # Obter o período letivo ativo
        periodo_letivo = PeriodoLetivo.objects.get(ativo=True)

        # Obter todos os dias letivos do período
        dias_letivos = DiaLetivo.objects.filter(periodo_letivo=periodo_letivo).values('data', 'status')

        # Converter datas para string no formato YYYY-MM-DD
        dias_letivos_list = [
            {'data': dia['data'].strftime('%Y-%m-%d'), 'status': dia['status']}
            for dia in dias_letivos
        ]

        return JsonResponse({
            'success': True,
            'dias_letivos': dias_letivos_list
        })
    except PeriodoLetivo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Nenhum período letivo ativo encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def index_view(request):
    # Busca todos os conteúdos do Hero
    hero_contents = HeroContent.objects.all()

    # Garante que exista pelo menos um conteúdo (opcional, dependendo do design)
    if not hero_contents.exists():
        HeroContent.objects.create(
            title="Seu futuro brilhante é nossa missão",
            subtitle="Lorem ipsum dolor sit amet...",
            button_text="Inscreva-se agora",
            button_link="#"
        )
        hero_contents = HeroContent.objects.all()

    feature_blocks = FeatureBlock.objects.filter(is_active=True).order_by('order')

    print("DEBUG - Hero Content Exists:", hero_contents.exists())
    print("DEBUG - Hero Contents:", list(hero_contents))
    print("DEBUG - Feature Blocks Count:", feature_blocks.count())
    print("DEBUG - Feature Blocks:", list(feature_blocks))

    context = {
        'hero_contents': hero_contents,
        'feature_blocks': feature_blocks,
    }

    return render(request, 'frontend/index.html', context)

def about_view(request):
    return render(request, "frontend/about.html")

def aluno_view(request):
    return render(request, "frontend/aluno.html")

def validate_ra(ra: str) -> None:
    """Valida o formato do RA do aluno.

    Args:
        ra: Número de RA a ser validado

    Raises:
        ValidationError: Se o RA não estiver no formato correto
    """
    if not re.match(r'^0000\d{9}[0-9X]$', ra):
        raise ValidationError('RA inválido. Formato esperado: 0000 + 9 dígitos + 1 dígito/X')


def get_bimestre_data(aluno: Aluno, disciplina: Disciplina, bimestre: Bimestre) -> Dict[str, Optional[Any]]:
    """Obtém os dados de um bimestre específico para uma disciplina.

    Args:
        aluno: Instância do aluno
        disciplina: Disciplina a ser consultada
        bimestre: Bimestre a ser consultado

    Returns:
        Dicionário com nota, faltas e situação do aluno
    """
    try:
        avaliacao = Avaliacao.objects.filter(
            aluno=aluno,
            disciplina=disciplina,
            bimestre=bimestre
        ).first()

        frequencias = Frequencia.objects.filter(
            aluno=aluno,
            disciplina=disciplina,
            data__gte=bimestre.data_inicio,
            data__lte=bimestre.data_fim
        )

        total_faltas = frequencias.filter(status='ausente').count()

        # Cálculo da situação (mireq)
        situacao = None
        if avaliacao and avaliacao.nota is not None:
            situacao = "Aprovado" if avaliacao.nota >= 6 else "Reprovado"

        return {
            'nota': avaliacao.nota if avaliacao else None,
            'faltas': total_faltas,
            'mireq': situacao
        }
    except Exception:
        return {
            'nota': None,
            'faltas': None,
            'mireq': None
        }


def get_disciplinas_data(aluno: Aluno) -> Dict[str, Dict[str, Any]]:
    """Obtém os dados de todas as disciplinas para um aluno.

    Args:
        aluno: Instância do aluno

    Returns:
        Dicionário com dados de todas as disciplinas e bimestres
    """
    disciplinas_data = {}
    todas_disciplinas = Disciplina.objects.all()
    bimestres = Bimestre.objects.filter(
        Q(nome="1º Bimestre") | Q(nome="2º Bimestre") |
        Q(nome="3º Bimestre") | Q(nome="4º Bimestre")
    ).order_by('nome')

    for disciplina in todas_disciplinas:
        bimestres_data = []

        for bimestre in bimestres:
            bimestre_data = get_bimestre_data(aluno, disciplina, bimestre)
            bimestres_data.append(bimestre_data)

        disciplinas_data[disciplina.nome] = {
            'nome': disciplina.nome,
            'bimestres': bimestres_data
        }

    return disciplinas_data


def consulta_boletim(request):
    """View para consulta de boletim escolar por RA."""
    boletim = None

    if request.method == 'POST':
        ra_aluno = request.POST.get('ra_aluno', '').strip()

        # Validação do RA
        try:
            validate_ra(ra_aluno)
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'frontend/templates/frontend/consulta_boletim.html', {'boletim': None})

        # Busca o aluno
        try:
            aluno = Aluno.objects.select_related('turma').get(ra=ra_aluno)
        except Aluno.DoesNotExist:
            messages.error(request, 'Aluno não encontrado com o RA informado.')
            return render(request, 'frontend/consulta_boletim.html', {'boletim': None})

        # Disciplinas fixas que devem aparecer no boletim
        DISCIPLINAS_BOLETIM = [
            'Português', 'Matemática', 'História', 'Geografia',
            'Ciências', 'Artes', 'Educação Física'
        ]

        # Obtém os dados das disciplinas
        disciplinas_data = {}
        bimestres = Bimestre.objects.filter(
            Q(nome="1º Bimestre") | Q(nome="2º Bimestre") |
            Q(nome="3º Bimestre") | Q(nome="4º Bimestre")
        ).order_by('nome')

        for disciplina_nome in DISCIPLINAS_BOLETIM:
            try:
                disciplina = Disciplina.objects.get(nome=disciplina_nome)
                bimestres_data = []

                for bimestre in bimestres:
                    # Busca avaliação
                    avaliacao = Avaliacao.objects.filter(
                        aluno=aluno,
                        disciplina=disciplina,
                        bimestre=bimestre
                    ).first()

                    # Calcula faltas
                    frequencias = Frequencia.objects.filter(
                        aluno=aluno,
                        disciplina=disciplina,
                        data__gte=bimestre.data_inicio,
                        data__lte=bimestre.data_fim
                    )
                    total_faltas = frequencias.filter(status='ausente').count()

                    # Calcula situação
                    situacao = None
                    if avaliacao and avaliacao.nota is not None:
                        situacao = "Aprovado" if avaliacao.nota >= 6 else "Reprovado"

                    bimestres_data.append({
                        'nota': avaliacao.nota if avaliacao else None,
                        'faltas': total_faltas,
                        'mireq': situacao
                    })

                disciplinas_data[disciplina_nome] = {
                    'nome': disciplina_nome,
                    'bimestres': bimestres_data
                }
            except Disciplina.DoesNotExist:
                # Se a disciplina não existir, cria com valores vazios
                disciplinas_data[disciplina_nome] = {
                    'nome': disciplina_nome,
                    'bimestres': [{'nota': None, 'faltas': None, 'mireq': None} for _ in range(4)]
                }

        # Prepara a estrutura do boletim
        boletim = {
            'aluno': aluno,
            'turma': aluno.turma.nome if aluno.turma else '',
            'disciplinas': disciplinas_data
        }

    return render(request, 'frontend/consulta_boletim.html', {'boletim': boletim})

def calendario_view(request):
    ano_letivo = 2026  # You can make this dynamic if needed
    bimestres = Bimestre.objects.filter(ano_letivo=ano_letivo).order_by('nome')
    total_dias_letivos = bimestres.aggregate(total=Sum('dias_letivo'))['total'] or 0

    # Assuming you already have the calendar data (calendario, dias_cabecalho, etc.)
    calendario = {}  # Your calendar data logic here
    dias_cabecalho = list(range(1, 32))  # Example: 1 to 31
    dias_letivos_por_mes = {}  # Your logic to calculate days per month

    context = {
        'bimestres': bimestres,
        'total_dias_letivos': total_dias_letivos,
        'calendario': calendario,
        'dias_cabecalho': dias_cabecalho,
        'dias_letivos_por_mes': dias_letivos_por_mes,
    }
    return render(request, 'admin/calendario.html', context)

@login_required
@require_POST
@csrf_protect
def atualizar_calendario(request):
    try:
        logger.debug(f"[atualizar_calendario] Requisição recebida: {request.body}")
        data = json.loads(request.body)
        logger.debug(f"[atualizar_calendario] Dados parseados: {data}")

        changes = data.get('changes', [])
        ano_calendario = data.get('ano', date.today().year)  # Permite receber o ano do frontend

        if not changes:
            logger.warning("[atualizar_calendario] Nenhuma alteração fornecida no payload.")
            return JsonResponse({'success': False, 'error': 'Nenhuma alteração fornecida.'}, status=400)

        with transaction.atomic():
            try:
                periodo_letivo = PeriodoLetivo.objects.get(ano=ano_calendario, ativo=True)
                logger.debug(f"[atualizar_calendario] Período letivo: {periodo_letivo}")
            except PeriodoLetivo.DoesNotExist:
                logger.error(
                    f"[atualizar_calendario] Nenhum período letivo ativo encontrado para o ano {ano_calendario}.")
                return JsonResponse(
                    {'success': False, 'error': f'Nenhum período letivo ativo encontrado para o ano {ano_calendario}.'},
                    status=400)
            except MultipleObjectsReturned:
                logger.error(
                    f"[atualizar_calendario] Múltiplos períodos letivos ativos encontrados para o ano {ano_calendario}.")
                return JsonResponse({'success': False,
                                     'error': f'Múltiplos períodos letivos ativos encontrados para o ano {ano_calendario}.'},
                                    status=400)

            mes_to_num = {
                'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'ABRIL': 4,
                'MAIO': 5, 'JUNHO': 6, 'JULHO': 7, 'AGOSTO': 8,
                'SETEMBRO': 9, 'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
            }

            for change in changes:
                try:
                    mes = change['mes']
                    dia = int(change['dia'])
                    novo_status = change['status']

                    data_atual = date(ano_calendario, mes_to_num[mes], dia)

                    DiaLetivo.objects.update_or_create(
                        periodo_letivo=periodo_letivo,
                        data=data_atual,
                        defaults={'status': novo_status}
                    )
                except (KeyError, ValueError) as e:
                    logger.error(f"[atualizar_calendario] Erro ao processar alteração {change}: {str(e)}")
                    return JsonResponse({'success': False, 'error': f'Dados inválidos na alteração: {change}'},
                                        status=400)

        # Recalcular totais
        dias_letivos_por_mes = {}
        for mes, num in mes_to_num.items():
            count = DiaLetivo.objects.filter(
                periodo_letivo=periodo_letivo,
                data__year=ano_calendario,
                data__month=num,
                status='L'
            ).count()
            dias_letivos_por_mes[mes] = count

        total_dias_letivos = sum(dias_letivos_por_mes.values())

        return JsonResponse({
            'success': True,
            'dias_letivos_por_mes': dias_letivos_por_mes,
            'total_dias_letivos': total_dias_letivos
        })

    except json.JSONDecodeError as e:
        logger.error(f"[atualizar_calendario] Erro ao parsear JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"[atualizar_calendario] Erro inesperado: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Erro interno do servidor'}, status=500)

def turma_list(request):
    try:
        turmas = Turma.objects.all().order_by('nome')  # Adiciona ordenação por nome
        logger.debug(f"[turma_list] Turmas recuperadas: {turmas.count()} turmas")
        return render(request, 'admin/core/turma/turma_list.html', {'turmas': turmas})
    except Exception as e:
        logger.error(f"[turma_list] Erro ao listar turmas: {str(e)}")
        return render(request, 'admin/core/turma/turma_list.html', {'turmas': [], 'error': 'Erro ao listar turmas.'})

def add_alunos_turma(request, turma_id):
    try:
        turma = get_object_or_404(Turma, id=turma_id)
        alunos = turma.alunos.all().order_by('nome')  # Ordena os alunos por nome

        if request.method == 'POST':
            ra = request.POST.get('ra')
            if not ra:
                logger.warning(f"[add_alunos_turma] RA não fornecido para turma {turma_id}")
                messages.error(request, 'Por favor, forneça o RA do aluno.')
                return redirect('add_alunos_turma', turma_id=turma.id)

            try:
                aluno = Aluno.objects.get(ra=ra)
                if aluno in turma.alunos.all():
                    logger.warning(f"[add_alunos_turma] Aluno {aluno.nome} (RA: {ra}) já está na turma {turma_id}")
                    messages.warning(request, f'Aluno {aluno.nome} já está nesta turma.')
                else:
                    turma.alunos.add(aluno)
                    logger.info(f"[add_alunos_turma] Aluno {aluno.nome} (RA: {ra}) adicionado à turma {turma_id}")
                    messages.success(request, f'Aluno {aluno.nome} adicionado com sucesso!')
            except Aluno.DoesNotExist:
                logger.error(f"[add_alunos_turma] Aluno com RA {ra} não encontrado para turma {turma_id}")
                messages.error(request, f'Aluno com RA {ra} não encontrado.')
            except Exception as e:
                logger.error(f"[add_alunos_turma] Erro ao adicionar aluno à turma {turma_id}: {str(e)}")
                messages.error(request, f'Erro ao adicionar aluno: {str(e)}')

            return redirect('add_alunos_turma', turma_id=turma.id)

        context = {
            'turma': turma,
            'alunos': alunos,
        }
        return render(request, 'admin/core/turma/add_alunos_turma.html', context)

    except Exception as e:
        logger.error(f"[add_alunos_turma] Erro inesperado ao processar turma {turma_id}: {str(e)}")
        messages.error(request, 'Erro inesperado ao processar a turma.')
        return render(request, 'admin/core/turma/add_alunos_turma.html', {'turma': None, 'alunos': []})

def remove_aluno_turma(request, turma_id, aluno_id):
    turma = get_object_or_404(Turma, id=turma_id)
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if request.method == 'POST':
        turma.alunos.remove(aluno)
        messages.success(request, f'Aluno {aluno.nome} removido com sucesso!')
        return redirect('add_alunos_turma', turma_id=turma.id)

    return redirect('add_alunos_turma', turma_id=turma.id)

def avaliacao_form(request, turma_id):
    # Your existing evaluation form logic here
    pass

def avaliacao_form(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    alunos = Aluno.objects.filter(turma=turma)
    disciplinas = Disciplina.objects.all()
    bimestres = Bimestre.objects.all()

    if not bimestres.exists():
        messages.error(request, "Nenhum bimestre cadastrado. Cadastre um bimestre antes de avaliar.")
        return redirect('turma_list')

    if request.method == "POST":
        bimestre_id = request.POST.get('bimestre')
        bimestre = get_object_or_404(Bimestre, id=bimestre_id)

        for aluno in alunos:
            for disciplina in disciplinas:
                nota_key = f"nota_{aluno.id}_{disciplina.id}"
                nota = request.POST.get(nota_key)
                if nota:
                    try:
                        nota = float(nota)
                        if not (0 <= nota <= 10):
                            messages.error(request, f"Nota inválida para {aluno.nome} em {disciplina.nome}. Deve estar entre 0 e 10.")
                            continue
                        Avaliacao.objects.update_or_create(
                            aluno=aluno,
                            disciplina=disciplina,
                            bimestre=bimestre,
                            turma=turma,
                            defaults={'nota': nota}
                        )
                    except ValueError:
                        messages.error(request, f"Nota inválida para {aluno.nome} em {disciplina.nome}. Deve ser um número.")
        messages.success(request, "Notas salvas com sucesso!")
        return redirect('turma_list')

    return render(request, 'core/avaliacao_form.html', {
        'turma': turma,
        'alunos': alunos,
        'disciplinas': disciplinas,
        'bimestres': bimestres,
    })

def avaliacao_form_view(self, request, turma_id):
    # ... código existente ...

    if request.method == "POST":
        self._processar_notas(request, alunos, disciplinas, bimestre, turma)
        # Mantém o bimestre selecionado após o POST
        return redirect(f"{reverse('admin:core_turma_avaliacao', args=[turma.id])}?bimestre={bimestre.id}")

@staff_member_required
def periodo_letivo_add(request):
    if request.method == 'POST':
        form = PeriodoLetivoForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

class RedirectURLMixin:
    next_page = None
    redirect_field_name = REDIRECT_FIELD_NAME
    success_url_allowed_hosts = set()

    def get_success_url(self):
        return self.get_redirect_url() or self.get_default_redirect_url()

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name)
        )
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ""

    def get_success_url_allowed_hosts(self):
        return {self.request.get_host(), *self.success_url_allowed_hosts}

    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        if self.next_page:
            return resolve_url(self.next_page)
        raise ImproperlyConfigured("No URL to redirect to. Provide a next_page.")



class LoginView(RedirectURLMixin, FormView):
    """
    Display the login form and handle the login action.
    """

    form_class = AuthenticationForm
    authentication_form = None
    template_name = "registration/login.html"
    redirect_authenticated_user = False
    extra_context = None

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        if self.next_page:
            return resolve_url(self.next_page)
        else:
            return resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_form_class(self):
        return self.authentication_form or self.form_class

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        auth_login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_current_site(self.request)
        context.update(
            {
                self.redirect_field_name: self.get_redirect_url(),
                "site": current_site,
                "site_name": current_site.name,
                **(self.extra_context or {}),
            }
        )
        return context


class LogoutView(RedirectURLMixin, TemplateView):
    """
    Log out the user and display the 'You are logged out' message.
    """

    # RemovedInDjango50Warning: when the deprecation ends, remove "get" and
    # "head" from http_method_names.
    http_method_names = ["get", "head", "post", "options"]
    template_name = "registration/logged_out.html"
    extra_context = None

    # RemovedInDjango50Warning: when the deprecation ends, move
    # @method_decorator(csrf_protect) from post() to dispatch().
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == "get":
            warnings.warn(
                "Log out via GET requests is deprecated and will be removed in Django "
                "5.0. Use POST requests for logging out.",
                RemovedInDjango50Warning,
            )
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        """Logout may be done via POST."""
        auth_logout(request)
        redirect_to = self.get_success_url()
        if redirect_to != request.get_full_path():
            # Redirect to target page once the session has been cleared.
            return HttpResponseRedirect(redirect_to)
        return super().get(request, *args, **kwargs)

    # RemovedInDjango50Warning.
    get = post

    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        if self.next_page:
            return resolve_url(self.next_page)
        elif settings.LOGOUT_REDIRECT_URL:
            return resolve_url(settings.LOGOUT_REDIRECT_URL)
        else:
            return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_current_site(self.request)
        context.update(
            {
                "site": current_site,
                "site_name": current_site.name,
                "title": _("Logged out"),
                "subtitle": None,
                **(self.extra_context or {}),
            }
        )
        return context


def logout_then_login(request, login_url=None):
    """
    Log out the user if they are logged in. Then redirect to the login page.
    """
    login_url = resolve_url(login_url or settings.LOGIN_URL)
    return LogoutView.as_view(next_page=login_url)(request)


def redirect_to_login(next, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    resolved_url = resolve_url(login_url or settings.LOGIN_URL)

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe="/")

    return HttpResponseRedirect(urlunparse(login_url_parts))
