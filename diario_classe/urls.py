from django.contrib import admin
from django.urls import path, include
from core.views import index_view, consulta_boletim, about_view, aluno_view, CustomLoginView, ajax_login
from django.contrib.auth import views as auth_views
from core.views import index_view, dias_letivos_api
urlpatterns = [
    path('ajax-login/', ajax_login, name='ajax_login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('sobre', about_view, name='sobre'),
    path('aluno', aluno_view, name='aluno'),
    path('', index_view, name='index'),
    path('aluno/', consulta_boletim, name='aluno'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('core.urls')),
]
