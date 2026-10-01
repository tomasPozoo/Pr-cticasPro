from django.contrib import admin
from django.urls import path
from portal.views import logout_view
from portal.views import (
    index, login_view, register_view, dashboard_view,
    home_estudiante, perfil_estudiante, ofertas_list, oferta_detail, mis_postulaciones,
    home_empresa, perfil_empresa, crear_oferta, mis_ofertas, ver_postulantes
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('registro/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    # Rutas Estudiante
    path('estudiante/', home_estudiante, name='home_estudiante'),
    path('estudiante/perfil/', perfil_estudiante, name='perfil_estudiante'),
    path('ofertas/', ofertas_list, name='ofertas_list'),
    path('ofertas/<int:oferta_id>/', oferta_detail, name='oferta_detail'),
    path('estudiante/postulaciones/', mis_postulaciones, name='mis_postulaciones'),

    # Rutas Empresa
    path('empresa/', home_empresa, name='home_empresa'),
    path('empresa/perfil/', perfil_empresa, name='perfil_empresa'),
    path('empresa/oferta/nueva/', crear_oferta, name='crear_oferta'),
    path('empresa/ofertas/', mis_ofertas, name='mis_ofertas'),
    path('empresa/ofertas/<int:oferta_id>/postulantes/', ver_postulantes, name='ver_postulantes'),
]