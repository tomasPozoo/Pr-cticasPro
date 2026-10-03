from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from portal.views import (
    index, login_view, register_view, dashboard_view, logout_view,
    home_estudiante, perfil_estudiante, ofertas_list, oferta_detail, mis_postulaciones,
    postular_oferta, ver_postulantes, cambiar_estado_postulacion, ver_perfil_estudiante,
    home_empresa, perfil_empresa, crear_oferta, mis_ofertas,
    home_admin, eliminar_usuario, eliminar_oferta
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
    path('ofertas/<str:oferta_id>/', oferta_detail, name='oferta_detail'),
    path('ofertas/<str:oferta_id>/postular/', postular_oferta, name='postular_oferta'),
    path('estudiante/postulaciones/', mis_postulaciones, name='mis_postulaciones'),

    # Rutas Empresa
    path('empresa/', home_empresa, name='home_empresa'),
    path('empresa/perfil/', perfil_empresa, name='perfil_empresa'),
    path('empresa/oferta/nueva/', crear_oferta, name='crear_oferta'),
    path('empresa/ofertas/', mis_ofertas, name='mis_ofertas'),
    path('empresa/ofertas/<str:oferta_id>/postulantes/', ver_postulantes, name='ver_postulantes'),
    path('empresa/postulaciones/<str:postulacion_id>/cambiar-estado/', cambiar_estado_postulacion, name='cambiar_estado_postulacion'),
    path('empresa/estudiante/<str:estudiante_id>/perfil/', ver_perfil_estudiante, name='ver_perfil_estudiante'),

    # Rutas Admin Panel
    path('admin-panel/', home_admin, name='home_admin'),
    path('admin-panel/eliminar-usuario/<str:usuario_id>/', eliminar_usuario, name='eliminar_usuario'),
    path('admin-panel/eliminar-oferta/<str:oferta_id>/', eliminar_oferta, name='eliminar_oferta'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)