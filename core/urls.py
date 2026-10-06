from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from portal import views
from django.conf.urls.static import static
from portal.views import (
    index,
    login_view,
    register_view,
    dashboard_view,
    logout_view,
    home_estudiante,
    perfil_estudiante,
    ofertas_list,
    oferta_detail,
    postular_oferta,
    mis_postulaciones,
    probot_ia,
    home_empresa,
    perfil_empresa,
    crear_oferta,
    mis_ofertas,
    ver_postulantes,
    cambiar_estado_postulacion,
    ver_perfil_estudiante,
    quienes_somos,
    home_admin,
    eliminar_usuario,
    eliminar_oferta,
    verificar_filtro_region,
    procesar_pago_premium,
    checkout_premium,
    confirmar_pago_premium,
    pago_exitoso,
    pago_fallido,
    pago_pendiente,
    mercadopago_webhook,
    dashboard_suscripciones,
    exportar_reporte_csv,


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
    
    # IA
    path('probot-ia/', probot_ia, name='probot_ia'),
    
    # Rutas Empresa
    path('empresa/', home_empresa, name='home_empresa'),
    path('empresa/perfil/', perfil_empresa, name='perfil_empresa'),
    path('empresa/oferta/nueva/', crear_oferta, name='crear_oferta'),
    path('empresa/ofertas/', mis_ofertas, name='mis_ofertas'),
    path('empresa/ofertas/<str:oferta_id>/postulantes/', ver_postulantes, name='ver_postulantes'),
    path('empresa/postulaciones/<str:postulacion_id>/cambiar-estado/', cambiar_estado_postulacion, name='cambiar_estado_postulacion'),
    path('empresa/estudiante/<str:estudiante_id>/perfil/', ver_perfil_estudiante, name='ver_perfil_estudiante'),

    path('quienes-somos/', quienes_somos, name='quienes_somos'),
    
    # Rutas Admin Panel
    path('admin-panel/', home_admin, name='home_admin'),
    path('admin-panel/eliminar-usuario/<str:usuario_id>/', eliminar_usuario, name='eliminar_usuario'),
    path('admin-panel/eliminar-oferta/<str:oferta_id>/', eliminar_oferta, name='eliminar_oferta'),

    # Rutas API de Pago y Filtro Regional Premium
    path('api/verificar-region/', verificar_filtro_region, name='verificar_filtro_region'),
    path('api/procesar-pago-premium/', procesar_pago_premium, name='procesar_pago_premium'),

    # Suscripción Checkout y Webhooks
    path('suscripcion/checkout/', checkout_premium, name='checkout_premium'),
    path('suscripcion/confirmar/', confirmar_pago_premium, name='confirmar_pago_premium'),
    path('suscripcion/exito/', pago_exitoso, name='pago_exitoso'),
    path('suscripcion/fallo/', pago_fallido, name='pago_fallido'),
    path('suscripcion/pendiente/', pago_pendiente, name='pago_pendiente'),
    path('api/mercadopago-webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
    path('admin/suscripciones/', dashboard_suscripciones, name='dashboard_suscripciones'),

    path('admin/exportar/<str:tipo_reporte>/', views.exportar_reporte_csv, name='exportar_reporte_csv'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)