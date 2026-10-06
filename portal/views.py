import os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import auth, firestore
from django.core.files.storage import FileSystemStorage
import json
from django.http import JsonResponse
from google import genai
from google.genai import types
import time
from django.conf import settings
import uuid
import mercadopago
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import datetime
import csv
# ==========================================
# CONFIGURACIÓN GENERAL Y PRECIO DEL PLAN
# ==========================================
PRECIO_PLAN = 2990.0  # <--- PRECIO OFICIAL EN CLP DEL PLAN PREMIUM

FIREBASE_KEY_PATH = os.path.join(settings.BASE_DIR, 'firebase_key.json')
FIREBASE_WEB_API_KEY = ""

if os.path.exists(FIREBASE_KEY_PATH):
    try:
        with open(FIREBASE_KEY_PATH, 'r', encoding='utf-8') as f:
            fb_data = json.load(f)
            FIREBASE_WEB_API_KEY = fb_data.get('FIREBASE_WEB_API_KEY', '')
    except Exception as e:
        print(f"⚠️ Error al cargar firebase_key.json: {e}")

KEY_FILE_PATH = os.path.join(settings.BASE_DIR, 'gemini_key.json')
GEMINI_API_KEY = ""

if os.path.exists(KEY_FILE_PATH):
    try:
        with open(KEY_FILE_PATH, 'r', encoding='utf-8') as f:
            key_data = json.load(f)
            GEMINI_API_KEY = key_data.get('GEMINI_API_KEY', '')
    except Exception as e:
        print(f"⚠️ Error al leer gemini_key.json: {e}")

MP_KEY_PATH = os.path.join(settings.BASE_DIR, 'mercadopago_key.json')
MERCADOPAGO_ACCESS_TOKEN = ""

if os.path.exists(MP_KEY_PATH):
    try:
        with open(MP_KEY_PATH, 'r', encoding='utf-8') as f:
            mp_data = json.load(f)
            MERCADOPAGO_ACCESS_TOKEN = mp_data.get('MERCADOPAGO_ACCESS_TOKEN', '')
    except Exception as e:
        print(f"⚠️ Error al leer mercadopago_key.json: {e}")


# ==========================================
# CHATBOT PROBOT IA
# ==========================================

def probot_ia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_usuario = data.get('mensaje', '').strip()

            if not mensaje_usuario:
                return JsonResponse({'respuesta': 'Por favor escribe una pregunta.'})

            client = genai.Client(api_key=GEMINI_API_KEY)

            instrucciones = (
                "Eres ProBot IA, el asistente virtual oficial del portal PrácticasPro. "
                "Tu objetivo es ayudar a estudiantes a encontrar su primera práctica profesional, "
                "revisar o mejorar su CV, dar tips para entrevistas de trabajo y resolver dudas. "
                "Responde en español de forma profesional, cercana y breve (máximo 2 párrafos)."
            )

            respuesta_texto = None
            max_intentos = 4
            tiempos_espera = [1.5, 2.5, 3.5]

            for intento in range(max_intentos):
                try:
                    chat = client.chats.create(
                        model='gemini-3.8-flash',
                        config=types.GenerateContentConfig(
                            system_instruction=instrucciones
                        )
                    )
                    response = chat.send_message(mensaje_usuario)

                    if response and response.text:
                        respuesta_texto = response.text
                        print(f"🚀 ¡ProBot IA respondió exitosamente en el intento {intento + 1}!")
                        break

                except Exception as err:
                    err_str = str(err)
                    print(f"⚠️️ Intento {intento + 1}/{max_intentos} en gemini-3.8-flash: {err_str}")

                    if "503" in err_str and intento < max_intentos - 1:
                        time.sleep(tiempos_espera[intento])
                    else:
                        break

            if respuesta_texto:
                return JsonResponse({'respuesta': respuesta_texto})
            else:
                return JsonResponse({
                    'respuesta': '🤖 Los servidores de la IA experimentan una alta demanda en este instante. Por favor reintenta tu pregunta en unos segundos.'
                })

        except Exception as e:
            print("❌ ERROR CRÍTICO EN PROBOT IA:", str(e))
            return JsonResponse({'respuesta': f"🤖 Ocurrió un error: {str(e)}"}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ==========================================
# VISTAS GENERALES
# ==========================================

def quienes_somos(request):
    """Página informativa sobre PrácticasPro, términos y privacidad."""
    return render(request, 'quienes_somos.html')

def index(request):
    return render(request, 'index.html')

def dashboard_view(request):
    rol = request.session.get('user_rol')
    if rol == 'estudiante':
        return redirect('home_estudiante')
    elif rol == 'empresa':
        return redirect('home_empresa')
    
    return redirect('login')


# ==========================================
# AUTENTICACIÓN Y REGISTRO
# ==========================================

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        nombre = request.POST.get('nombre')
        rol = request.POST.get('rol')

        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=nombre
            )

            db = firestore.client()
            db.collection('usuarios').document(user.uid).set({
                'nombre': nombre,
                'email': email,
                'rol': rol,
                'es_premium': False,
                'region': 'Región Metropolitana',
                'creado_en': firestore.SERVER_TIMESTAMP
            })

            messages.success(request, 'Cuenta creada exitosamente. Inicia sesión.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url, json=payload)
        data = response.json()

        if "error" in data:
            messages.error(request, "Correo o contraseña incorrectos.")
        else:
            uid = data['localId']

            db = firestore.client()
            doc = db.collection('usuarios').document(uid).get()

            if doc.exists:
                user_data = doc.to_dict()
                rol = user_data.get('rol')

                request.session['user_id'] = uid
                request.session['user_email'] = email
                request.session['user_name'] = user_data.get('nombre')
                request.session['user_rol'] = rol
                request.session['es_premium'] = user_data.get('es_premium', False)
                request.session['region'] = user_data.get('region', 'Región Metropolitana')

                if rol == 'estudiante':
                    return redirect('home_estudiante')
                elif rol == 'empresa':
                    return redirect('home_empresa')
                elif rol == 'admin':
                    return redirect('home_admin')
                else:
                    return redirect('index') 
            else:
                messages.error(request, "El usuario no tiene un perfil registrado.")

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')


# ==========================================
# VISTAS DE ESTUDIANTE
# ==========================================

def home_estudiante(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')

    user_id = request.session.get('user_id')
    db = firestore.client()

    user_doc = db.collection('usuarios').document(user_id).get()
    estudiante_data = user_doc.to_dict() if user_doc.exists else {}

    postulaciones_ref = db.collection('postulaciones').where('estudiante_id', '==', user_id).get()
    total_postulaciones = len(postulaciones_ref)

    ofertas_ref = db.collection('ofertas').stream()
    ofertas = [{'id': doc.id, **doc.to_dict()} for doc in ofertas_ref]

    context = {
        'estudiante': estudiante_data,
        'total_postulaciones': total_postulaciones,
        'total_ofertas': len(ofertas),
        'ofertas': ofertas[:6],
    }
    return render(request, 'home_estudiante.html', context)

def perfil_estudiante(request):
    user_id = request.session.get('user_id')
    user_rol = request.session.get('user_rol')

    if not user_id or user_rol != 'estudiante':
        messages.error(request, "Acceso no autorizado.")
        return redirect('login')

    db = firestore.client()
    user_ref = db.collection('usuarios').document(user_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        carrera = request.POST.get('carrera')
        telefono = request.POST.get('telefono')
        bio = request.POST.get('bio')

        doc_actual = user_ref.get()
        data_actual = doc_actual.to_dict() if doc_actual.exists else {}
        foto_url = data_actual.get('foto_url', '')

        if 'foto' in request.FILES:
            foto_file = request.FILES['foto']
            fs = FileSystemStorage()
            
            extension = foto_file.name.split('.')[-1]
            nombre_archivo = f"perfiles/{user_id}.{extension}"

            if fs.exists(nombre_archivo):
                fs.delete(nombre_archivo)

            filename = fs.save(nombre_archivo, foto_file)
            foto_url = fs.url(filename)

        user_ref.update({
            'nombre': nombre,
            'carrera': carrera,
            'telefono': telefono,
            'bio': bio,
            'foto_url': foto_url
        })

        messages.success(request, "¡Perfil y foto actualizados con éxito!")
        return redirect('perfil_estudiante')

    doc = user_ref.get()
    estudiante_data = doc.to_dict() if doc.exists else {}

    return render(request, 'perfil_estudiante.html', {'estudiante': estudiante_data})

def ofertas_list(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')
        
    db = firestore.client()
    ofertas_ref = db.collection('ofertas').where('estado', '==', 'activa').stream()
    
    lista_ofertas = []
    for doc in ofertas_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        lista_ofertas.append(data)
        
    return render(request, 'ofertas_list.html', {'ofertas': lista_ofertas})

def oferta_detail(request, oferta_id):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')
        
    db = firestore.client()
    doc_ref = db.collection('ofertas').document(oferta_id).get()
    
    if not doc_ref.exists:
        messages.error(request, "La oferta no existe.")
        return redirect('ofertas_list')
        
    oferta_data = doc_ref.to_dict()
    oferta_data['id'] = doc_ref.id
    
    return render(request, 'oferta_detail.html', {'oferta': oferta_data})

def postular_oferta(request, oferta_id):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')
        
    db = firestore.client()
    
    oferta_doc = db.collection('ofertas').document(oferta_id).get()
    if not oferta_doc.exists:
        messages.error(request, "La oferta no existe.")
        return redirect('ofertas_list')
        
    oferta_data = oferta_doc.to_dict()
    oferta_data['id'] = oferta_doc.id
    estudiante_id = request.session.get('user_id')

    if request.method == 'POST':
        mensaje = request.POST.get('mensaje', '')
        cv_url = None

        if 'cv_file' in request.FILES:
            archivo = request.FILES['cv_file']
            fs = FileSystemStorage()
            filename = fs.save(f"cvs/{estudiante_id}_{archivo.name}", archivo)
            cv_url = fs.url(filename)

        try:
            nueva_postulacion = {
                'oferta_id': oferta_id,
                'oferta_titulo': oferta_data.get('titulo', ''),
                'empresa_id': oferta_data.get('empresa_id', ''),
                'empresa_nombre': oferta_data.get('empresa_nombre', ''),
                'estudiante_id': estudiante_id,
                'estudiante_nombre': request.session.get('user_name', ''),
                'estudiante_email': request.session.get('user_email', ''),
                'mensaje': mensaje,
                'cv_url': cv_url,
                'estado': 'pendiente',
                'fecha_postulacion': firestore.SERVER_TIMESTAMP
            }

            db.collection('postulaciones').add(nueva_postulacion)

            messages.success(request, "¡Te has postulado con éxito!")
            return redirect('mis_postulaciones')

        except Exception as e:
            messages.error(request, f"Error al procesar la postulación: {str(e)}")

    return render(request, 'postular_oferta.html', {'oferta': oferta_data})

def mis_postulaciones(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')

    estudiante_id = request.session.get('user_id')
    db = firestore.client()

    try:
        postulaciones_ref = db.collection('postulaciones').where('estudiante_id', '==', estudiante_id).stream()
        
        lista_postulaciones = []
        for doc in postulaciones_ref:
            data = doc.to_dict()
            data['id'] = doc.id
            lista_postulaciones.append(data)

        context = {
            'postulaciones': lista_postulaciones
        }
        
        return render(request, 'mis_postulaciones.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al cargar tus postulaciones: {str(e)}")
        return redirect('home_estudiante')


# ==========================================
# VISTAS DE EMPRESA
# ==========================================

def home_empresa(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')
    return render(request, 'home_empresa.html', {'nombre': request.session.get('user_name')})

def perfil_empresa(request):
    return render(request, 'perfil_empresa.html')

def crear_oferta(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        requisitos = request.POST.get('requisitos')
        modalidad = request.POST.get('modalidad')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')

        try:
            db = firestore.client()
            
            oferta_data = {
                'empresa_id': request.session.get('user_id'),
                'empresa_nombre': request.session.get('user_name'),
                'titulo': titulo,
                'descripcion': descripcion,
                'requisitos': requisitos,
                'modalidad': modalidad,
                'latitud': latitud,
                'longitud': longitud,
                'estado': 'activa',
                'fecha_creacion': firestore.SERVER_TIMESTAMP
            }
            
            db.collection('ofertas').add(oferta_data)
            
            messages.success(request, "¡Oferta creada y publicada exitosamente!")
            return redirect('home_empresa')
            
        except Exception as e:
            messages.error(request, f"Error al publicar la oferta: {str(e)}")

    return render(request, 'crear_oferta.html')

def mis_ofertas(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')
        
    empresa_id = request.session.get('user_id')
    db = firestore.client()
    
    ofertas_ref = db.collection('ofertas').where('empresa_id', '==', empresa_id).stream()
    
    lista_ofertas = []
    for doc in ofertas_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        lista_ofertas.append(data)
        
    return render(request, 'mis_ofertas.html', {'ofertas': lista_ofertas})

def ver_postulantes(request, oferta_id):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    db = firestore.client()
    
    oferta_doc = db.collection('ofertas').document(oferta_id).get()
    oferta = oferta_doc.to_dict() if oferta_doc.exists else {}

    postulaciones_ref = db.collection('postulaciones').where('oferta_id', '==', oferta_id).stream()
    
    postulantes = []
    for doc in postulaciones_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        postulantes.append(data)

    context = {
        'oferta': oferta,
        'oferta_id': oferta_id,
        'postulantes': postulantes,
        'total_postulantes': len(postulantes)
    }

    return render(request, 'ver_postulantes.html', context)

def cambiar_estado_postulacion(request, postulacion_id):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')
        oferta_id = request.POST.get('oferta_id')
        mensaje_respuesta = request.POST.get('mensaje_respuesta', '').strip()

        try:
            db = firestore.client()
            postulacion_ref = db.collection('postulaciones').document(postulacion_id)

            postulacion_ref.update({
                'estado': nuevo_estado,
                'mensaje_empresa': mensaje_respuesta
            })

            messages.success(request, f"Estado actualizado a '{nuevo_estado}' con éxito.")

        except Exception as e:
            messages.error(request, f"Error al actualizar la postulación: {str(e)}")

        return redirect('ver_postulantes', oferta_id=oferta_id)

    return redirect('mis_ofertas')

def ver_perfil_estudiante(request, estudiante_id):
    if request.session.get('user_rol') != 'empresa':
        messages.error(request, "Acceso denegado. Solo las empresas pueden ver esta página.")
        return redirect('mis_ofertas')

    try:
        db = firestore.client()
        estudiante_doc = db.collection('usuarios').document(estudiante_id).get()

        if not estudiante_doc.exists:
            messages.error(request, "El perfil del estudiante no fue encontrado.")
            return redirect('mis_ofertas')

        estudiante_data = estudiante_doc.to_dict()
        return render(request, 'ver_perfil_estudiante.html', {'estudiante': estudiante_data})

    except Exception as e:
        messages.error(request, f"Error al cargar el perfil: {str(e)}")
        return redirect('mis_ofertas')


# ==========================================
# VISTAS DE ADMINISTRADOR
# ==========================================

def home_admin(request):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
    
    db = firestore.client()
    
    # 1. Usuarios y Métricas Desglosadas
    usuarios_ref = db.collection('usuarios').stream()
    lista_usuarios = []
    
    estudiantes_count = 0
    estudiantes_premium_count = 0
    estudiantes_free_count = 0
    empresas_count = 0
    premium_count = 0
    
    for doc in usuarios_ref:
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        
        es_premium = user_data.get('es_premium', False)
        user_data['es_premium'] = es_premium
        if es_premium:
            premium_count += 1
        
        rol = user_data.get('rol', '')
        if rol == 'estudiante':
            estudiantes_count += 1
            if es_premium:
                estudiantes_premium_count += 1
            else:
                estudiantes_free_count += 1
        elif rol == 'empresa':
            empresas_count += 1
            
        lista_usuarios.append(user_data)

    # Tasa de conversión Freemium -> Premium
    tasa_conversion = (estudiantes_premium_count / estudiantes_count * 100) if estudiantes_count > 0 else 0.0

    # 2. Ofertas de Práctica
    ofertas_ref = db.collection('ofertas').stream()
    lista_ofertas = [{**doc.to_dict(), 'id': doc.id} for doc in ofertas_ref]

    # 3. Postulaciones y Métricas de Impacto
    postulaciones_ref = db.collection('postulaciones').stream()
    lista_postulaciones = []
    estados_postulacion = {'pendiente': 0, 'aceptado': 0, 'rechazado': 0}

    for doc in postulaciones_ref:
        p_data = doc.to_dict()
        p_data['id'] = doc.id
        lista_postulaciones.append(p_data)
        
        est = str(p_data.get('estado', 'pendiente')).lower()
        if est in estados_postulacion:
            estados_postulacion[est] += 1
        else:
            estados_postulacion['pendiente'] += 1

    total_postulaciones = len(lista_postulaciones)
    promedio_postulaciones = round(total_postulaciones / len(lista_ofertas), 1) if lista_ofertas else 0.0

    # 4. Suscripciones y Finanzas
    suscripciones_ref = db.collection('suscripciones').stream()
    ingresos_totales = 0.0
    ultimas_suscripciones = []

    for doc in suscripciones_ref:
        sub_data = doc.to_dict()
        sub_data['id'] = doc.id
        monto_val = float(sub_data.get('monto') or sub_data.get('precio') or 0.0)
        sub_data['monto'] = monto_val
        sub_data['precio'] = monto_val
        
        estado = str(sub_data.get('estado', '')).lower()
        if estado in ['activa', 'completado', 'pagado', 'aprobado']:
            ingresos_totales += monto_val

        ultimas_suscripciones.append(sub_data)

    ultimas_suscripciones.sort(key=lambda x: str(x.get('fecha', '')), reverse=True)
    ultimas_suscripciones = ultimas_suscripciones[:5]

    # Datos JSON pre-formateados para Chart.js en la plantilla
    chart_data_usuarios = json.dumps([estudiantes_free_count, estudiantes_premium_count, empresas_count])
    chart_data_postulaciones = json.dumps([
        estados_postulacion['pendiente'], 
        estados_postulacion['aceptado'], 
        estados_postulacion['rechazado']
    ])

    context = {
        'nombre': request.session.get('user_name', 'Administrador'),
        'usuarios': lista_usuarios,
        'ofertas': lista_ofertas,
        'total_usuarios': len(lista_usuarios),
        'estudiantes_count': estudiantes_count,
        'estudiantes_premium_count': estudiantes_premium_count,
        'estudiantes_free_count': estudiantes_free_count,
        'empresas_count': empresas_count,
        'premium_count': premium_count,
        'tasa_conversion': round(tasa_conversion, 1),
        'total_ofertas': len(lista_ofertas),
        'total_postulaciones': total_postulaciones,
        'promedio_postulaciones': promedio_postulaciones,
        'ingresos_totales': f"{int(ingresos_totales):,}".replace(",", "."),
        'ultimas_suscripciones': ultimas_suscripciones,
        'chart_data_usuarios': chart_data_usuarios,
        'chart_data_postulaciones': chart_data_postulaciones,
    }
    return render(request, 'home_admin.html', context)

def eliminar_usuario(request, usuario_id):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
    
    try:
        auth.delete_user(usuario_id)
        db = firestore.client()
        db.collection('usuarios').document(usuario_id).delete()
        messages.success(request, "Usuario eliminado correctamente de la plataforma.")
    except Exception as e:
        messages.error(request, f"Error al eliminar usuario: {str(e)}")
        
    return redirect('home_admin')

def eliminar_oferta(request, oferta_id):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
        
    try:
        db = firestore.client()
        db.collection('ofertas').document(oferta_id).delete()
        messages.success(request, "Oferta de práctica eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la oferta: {str(e)}")
        
    return redirect('home_admin')


# ==========================================
# VISTAS DE PAGO Y PLAN PREMIUM (FREEMIUM)
# ==========================================

def verificar_filtro_region(request):
    """API AJAX para validar si el estudiante puede filtrar por la región seleccionada"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            region_seleccionada = data.get('region', '')
            user_id = request.session.get('user_id')

            if not user_id:
                return JsonResponse({'error': 'Sesión no válida'}, status=401)

            db = firestore.client()
            user_doc = db.collection('usuarios').document(user_id).get()
            
            es_premium = False
            region_base = 'Región Metropolitana'

            if user_doc.exists:
                u_data = user_doc.to_dict()
                es_premium = u_data.get('es_premium', False)
                region_base = u_data.get('region', 'Región Metropolitana')
                request.session['es_premium'] = es_premium
                request.session['region'] = region_base

            if region_seleccionada != region_base and not es_premium:
                return JsonResponse({
                    'permitido': False,
                    'requiere_premium': True,
                    'region_base': region_base,
                    'mensaje': f'Tu región registrada es "{region_base}". Para buscar prácticas en otras regiones necesitas el Plan Premium.'
                })

            return JsonResponse({'permitido': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def procesar_pago_premium(request):
    """Procesa la actualización del usuario a Premium en Firestore tras el pago"""
    if request.method == 'POST':
        user_id = request.session.get('user_id')

        if not user_id:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)

        try:
            db = firestore.client()
            
            db.collection('usuarios').document(user_id).update({
                'es_premium': True,
                'fecha_suscripcion': firestore.SERVER_TIMESTAMP
            })

            request.session['es_premium'] = True

            return JsonResponse({
                'success': True,
                'mensaje': '¡Felicidades! Tu cuenta ha sido actualizada a Premium con éxito.'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def confirmar_pago_premium(request):
    """Procesa el pago, activa es_premium en Firestore y redirige."""
    if request.method == 'POST':
        user_id = request.session.get('user_id')

        if not user_id:
            return redirect('login')

        try:
            db = firestore.client()

            db.collection('usuarios').document(user_id).update({
                'es_premium': True,
                'fecha_suscripcion': firestore.SERVER_TIMESTAMP,
            })

            request.session['es_premium'] = True

            messages.success(request, "🎉 ¡Pago recibido con éxito! Ya eres usuario Premium.")
            return redirect('home_estudiante')

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar la transacción: {str(e)}")
            return redirect('checkout_premium')

    return redirect('home_estudiante')


def pago_exitoso(request):
    user_id = request.GET.get('external_reference') or request.session.get('user_id')
    status = request.GET.get('status') or request.GET.get('collection_status')
    payment_id = request.GET.get('payment_id') or request.GET.get('collection_id')

    if user_id and status == 'approved':
        db = firestore.client()
        
        user_ref = db.collection('usuarios').document(user_id)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()

            # 1. Actualizar estado Premium
            user_ref.update({
                'es_premium': True
            })

            # 2. Registrar el pago en la colección 'suscripciones' usando PRECIO_PLAN
            db.collection('suscripciones').add({
                'usuario_id': user_id,
                'email_usuario': user_data.get('email', ''),
                'usuario_nombre': user_data.get('nombre', ''),
                'monto': PRECIO_PLAN,
                'precio': PRECIO_PLAN,
                'payment_id': str(payment_id),
                'estado': 'completado',
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # 3. Actualizar sesión activa
            request.session['user_id'] = user_id
            request.session['user_email'] = user_data.get('email')
            request.session['user_name'] = user_data.get('nombre')
            request.session['user_rol'] = user_data.get('rol', 'estudiante')
            request.session['es_premium'] = True

            messages.success(request, "¡Felicidades! Tu suscripción Premium ha sido activada.")
            return redirect('home_estudiante')

    messages.error(request, "No se pudo confirmar el estado de la suscripción.")
    return redirect('login')


def pago_fallido(request):
    messages.error(request, "❌ Ocurrió un problema con el pago o fue cancelado. Inténtalo nuevamente.")
    return redirect('home_estudiante')


def pago_pendiente(request):
    messages.warning(request, "⏳ Tu pago está en proceso de validación. Te notificaremos al confirmarse.")
    return redirect('home_estudiante')


@csrf_exempt
def mercadopago_webhook(request):
    """Webhook que recibe las notificaciones de Mercado Pago en segundo plano."""
    if request.method == 'POST':
        topic = request.GET.get('type') or request.GET.get('topic')
        payment_id = request.GET.get('data.id') or request.GET.get('id')

        if not payment_id:
            try:
                body = json.loads(request.body)
                payment_id = body.get('data', {}).get('id')
                topic = body.get('type')
            except Exception:
                pass

        if topic == 'payment' and payment_id:
            sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info.get('response', {})

            if payment_data.get('status') == 'approved':
                user_id = payment_data.get('external_reference')
                monto = float(payment_data.get('transaction_amount', PRECIO_PLAN))
                
                if user_id:
                    db = firestore.client()
                    user_ref = db.collection('usuarios').document(user_id)
                    user_doc = user_ref.get()
                    
                    user_data = user_doc.to_dict() if user_doc.exists else {}

                    # 1. Actualizar usuario a Premium
                    user_ref.update({
                        'es_premium': True,
                        'fecha_suscripcion': firestore.SERVER_TIMESTAMP,
                        'mp_payment_id': payment_id
                    })

                    # 2. Registrar la suscripción
                    db.collection('suscripciones').add({
                        'usuario_id': user_id,
                        'email_usuario': user_data.get('email', ''),
                        'usuario_nombre': user_data.get('nombre', ''),
                        'monto': monto,
                        'precio': monto,
                        'payment_id': str(payment_id),
                        'estado': 'completado',
                        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

        return HttpResponse(status=200)

    return HttpResponse(status=400)


def checkout_premium(request):
    """Genera la preferencia en Mercado Pago garantizando un dominio válido para webhooks."""
    user_id = request.session.get('user_id')
    user_email = request.session.get('user_email') or 'test_user_123456@testuser.com'

    if not user_id:
        return redirect('login')

    try:
        if not MERCADOPAGO_ACCESS_TOKEN:
            raise Exception("El Access Token de Mercado Pago no está configurado.")

        sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

        host = request.get_host()
        if '127.0.0.1' in host or 'localhost' in host:
            base_url = "https://reptilian-debug-disobey.ngrok-free.dev"
        else:
            base_url = f"https://{host}"

        preference_data = {
            "items": [
                {
                    "title": "Suscripción Premium PrácticasPro",
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": int(PRECIO_PLAN),
                }
            ],
            "payer": {
                "email": str(user_email),
            },
            "back_urls": {
                "success": f"{base_url}/suscripcion/exito/",
                "failure": f"{base_url}/suscripcion/fallo/",
                "pending": f"{base_url}/suscripcion/pendiente/",
            },
            "auto_return": "approved",
            "notification_url": f"{base_url}/api/mercadopago-webhook/",
            "external_reference": str(user_id),
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})

        redirect_url = preference.get("sandbox_init_point") or preference.get("init_point")

        if not redirect_url:
            raise Exception(f"Respuesta inválida de Mercado Pago: {preference}")

        return redirect(redirect_url)

    except Exception as e:
        print(f"❌ ERROR MERCADO PAGO: {e}")
        messages.error(request, f"Error al procesar el pago: {str(e)}")
        return redirect('home_estudiante')


def dashboard_suscripciones(request):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
    
    db = firestore.client()
    suscripciones_ref = db.collection('suscripciones').stream()
    
    lista_suscripciones = []
    total_suscripciones = 0
    activas_count = 0
    pendientes_count = 0
    canceladas_count = 0
    ingresos_estimados = 0
    
    for doc in suscripciones_ref:
        sub_data = doc.to_dict()
        sub_data['id'] = doc.id
        
        estado = sub_data.get('estado', '').lower()
        if estado in ['activa', 'completado', 'pagado', 'aprobado']:
            activas_count += 1
        elif estado == 'pendiente':
            pendientes_count += 1
        elif estado in ['cancelada', 'vencida']:
            canceladas_count += 1

        monto = float(sub_data.get('monto') or sub_data.get('precio') or 0.0)
        sub_data['monto'] = monto
        sub_data['precio'] = monto

        if estado in ['activa', 'completado', 'pagado', 'aprobado']:
            ingresos_estimados += monto
            
        lista_suscripciones.append(sub_data)
        total_suscripciones += 1

    context = {
        'nombre': request.session.get('user_name', 'Administrador'),
        'suscripciones': lista_suscripciones,
        'total_suscripciones': total_suscripciones,
        'activas_count': activas_count,
        'pendientes_count': pendientes_count,
        'canceladas_count': canceladas_count,
        'ingresos_estimados': ingresos_estimados,
    }
    
    return render(request, 'dashboard_suscripciones.html', context)


def exportar_reporte_csv(request, tipo_reporte):
    """Genera un archivo CSV descargable con el reporte seleccionado para el Administrador."""
    if request.session.get('user_rol') != 'admin':
        return redirect('login')

    db = firestore.client()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tipo_reporte}.csv"'
    
    # Escribir BOM para que Excel abra los caracteres en español sin problemas
    response.write('\ufeff')
    writer = csv.writer(response)

    if tipo_reporte == 'usuarios':
        writer.writerow(['ID Documento', 'Nombre', 'Email', 'Rol', 'Es Premium', 'Región'])
        for doc in db.collection('usuarios').stream():
            u = doc.to_dict()
            writer.writerow([doc.id, u.get('nombre'), u.get('email'), u.get('rol'), u.get('es_premium', False), u.get('region', '')])

    elif tipo_reporte == 'suscripciones':
        writer.writerow(['ID Pago', 'Usuario ID', 'Email', 'Monto (CLP)', 'Estado', 'Fecha'])
        for doc in db.collection('suscripciones').stream():
            s = doc.to_dict()
            writer.writerow([doc.id, s.get('usuario_id'), s.get('email_usuario'), s.get('monto'), s.get('estado'), s.get('fecha')])

    elif tipo_reporte == 'ofertas':
        writer.writerow(['ID Oferta', 'Empresa', 'Título Práctica', 'Modalidad', 'Estado'])
        for doc in db.collection('ofertas').stream():
            o = doc.to_dict()
            writer.writerow([doc.id, o.get('empresa_nombre'), o.get('titulo'), o.get('modalidad'), o.get('estado')])

    return response