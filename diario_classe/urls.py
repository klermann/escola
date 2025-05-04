from django.contrib import admin
from django.urls import path, include
from core.views import index_view, consulta_boletim, about_view, aluno_view
from django.contrib.auth import views as auth_views
from core.views import index_view, dias_letivos_api
urlpatterns = [
    path('admin/', admin.site.urls),
    path('about', about_view, name='about'),
    path('aluno', aluno_view, name='aluno'),
    path('', index_view, name='index'),
    path('consulta-boletim/', consulta_boletim, name='consulta_boletim'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('core.urls')),
]
