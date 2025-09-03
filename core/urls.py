from django.contrib import admin
from django.urls import path, include
from . import views
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET
from django.http import HttpResponse
from django.shortcuts import render

class ManifestView(TemplateView):
    template_name = 'pwa/manifest.json'
    content_type = 'application/manifest+json'

@require_GET
def service_worker(request):
    response = render(request, 'pwa/sw.js', content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response
urlpatterns = [
    path('admin/', admin.site.urls),
    path('calendario/atualizar/', views.atualizar_calendario, name='atualizar_calendario'),
    path('api/dias-letivos/', views.dias_letivos_api, name='dias_letivos_api'),
    path('consulta-boletim/', views.consulta_boletim, name='consulta_boletim'),
    path('turma/<int:turma_id>/avaliacao/', views.avaliacao_form, name='avaliacao_form'),
    path('turma/<int:turma_id>/add_alunos/', views.add_alunos_turma, name='add_alunos_turma'),
    path('turma/<int:turma_id>/remove_aluno/<int:aluno_id>/', views.remove_aluno_turma, name='remove_aluno_turma'),
    path('api/frequencias/', views.api_frequencias, name='api_frequencias'),
    path('api/frequencias-alunos/', views.api_frequencias_alunos, name='api_frequencias_alunos'),
    path('', views.turma_list, name='turma_list'),  # Mova para o final

    path('manifest.json', ManifestView.as_view(), name='manifest'),
    path('offline/', TemplateView.as_view(template_name='pwa/offline.html'), name='offline'),
    path('sw.js', service_worker, name='service_worker'),
]