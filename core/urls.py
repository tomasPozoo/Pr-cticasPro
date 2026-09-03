from django.urls import path
from . import views

urlpatterns = [
    # Página principal (al entrar a http://127.0.0.1:8000/)
    path('', views.index, name='index'),

    # Autenticación y Registro
    path('login-usuario/', views.login_usuario, name='login_usuario'),
    path('login-empresa/', views.login_empresa, name='login_empresa'),
    path('registro-usuario/', views.registro_usuario, name='registro_usuario'),
    path('registro-empresa/', views.registro_empresa, name='registro_empresa'),

    # Plataforma Interna
    path('dashboard-estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),
    path('suscripcion/', views.suscripcion, name='suscripcion'),
    path('dashboard-empresa/', views.dashboard_empresa, name='dashboard_empresa'),
    path('perfil-estudiante/', views.perfil_estudiante, name='perfil_estudiante'),
]