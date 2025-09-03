from django.contrib import admin
from django.urls import path, include
from core.views import index_view, consulta_boletim, about_view, aluno_view, CustomLoginView, ajax_login
from django.contrib.auth import views as auth_views
from core.views import index_view, dias_letivos_api
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET
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
    path('ajax-login/', ajax_login, name='ajax_login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('sobre', about_view, name='sobre'),
    path('aluno', aluno_view, name='aluno'),
    path('', index_view, name='index'),
    path('consulta-boletim/', consulta_boletim, name='consulta_boletim'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),

    # URLs PWA
    path('manifest.json', ManifestView.as_view(), name='manifest'),
    path('offline/', TemplateView.as_view(template_name='pwa/offline.html'), name='offline'),
    path('sw.js', service_worker, name='service_worker'),
    path('', include('pwa.urls'))
]


# from django.contrib import admin




# from django.urls import path, include
# from core.views import index_view, consulta_boletim, about_view, aluno_view, CustomLoginView, ajax_login
# from django.contrib.auth import views as auth_views
# from core.views import index_view, dias_letivos_api
# urlpatterns = [
#     path('ajax-login/', ajax_login, name='ajax_login'),
#     path('login/', CustomLoginView.as_view(), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('sobre', about_view, name='sobre'),
#     path('aluno', aluno_view, name='aluno'),
#     path('', index_view, name='index'),
#     path('aluno/', consulta_boletim, name='aluno'),
#     path('login/', auth_views.LoginView.as_view(), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
#     path('admin/', admin.site.urls),
#     path('', include('core.urls')),
# ]
