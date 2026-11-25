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
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import unicodedata
import base64
from io import BytesIO
from PIL import Image
# ==========================================



def _procesar_imagen_base64(archivo_imagen) -> str:
    """Redimensiona y comprime una imagen a JPEG Base64 (~25 KB) para guardarla en Firestore."""
    img = Image.open(archivo_imagen)
    if img.mode in ("RGBA", "P", "LA"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA"):
            fondo.paste(img, mask=img.split()[-1])
        else:
            fondo.paste(img)
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((300, 300))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=82)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"
# CONFIGURACIÓN GENERAL Y PRECIO DEL PLAN
# ==========================================
PRECIO_PLAN = 2990.0  # <--- PRECIO OFICIAL EN CLP DEL PLAN PREMIUM

FIREBASE_WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')


# ==========================================
# CHATBOT PROBOT IA
# ==========================================
def _normalizar_texto(texto: str) -> str:
    """Convierte a minúsculas y elimina tildes para coincidencia exacta de palabras clave."""
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def _respuesta_fallback_probot(mensaje_usuario: str) -> str:
    """Diccionario completo de respaldo por palabras clave adaptado a PrácticasPro (Chile)."""
    msg = _normalizar_texto(mensaje_usuario)

    # 1. Saludos y presentación
    saludos = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hey', 'que tal', 'saludos', 'holi', 'alo']
    if any(msg == s or msg.startswith(s + ' ') or msg.startswith(s + ',') for s in saludos):
        return (
            "¡Hola! 👋 Soy **ProBot IA**, el asistente virtual de **PrácticasPro**.\n\n"
            "¿En qué te puedo ayudar hoy? Puedes preguntarme sobre cómo postular a prácticas profesionales, "
            "cómo mejorar tu CV, tips para entrevistas, cartas de presentación, remuneración o el seguro escolar en Chile."
        )

    # 2. Qué puedes hacer / Ayuda
    if any(p in msg for p in ['ayuda', 'que haces', 'como funcionas', 'opciones', 'menu', 'que puedes hacer']):
        return (
            "Estoy aquí para impulsarte en la búsqueda de tu primera práctica profesional en Chile. Puedo orientarte en:\n"
            "• **Postulaciones:** Cómo buscar y postular en PrácticasPro.\n"
            "• **Currículum y Carta:** Cómo destacar tus ramos, proyectos y habilidades sin experiencia previa.\n"
            "• **Entrevistas y Legal:** Consejos para entrevistas, asignaciones de movilización/colación y seguro escolar."
        )

    # 3. Diccionario temático para estudiantes en Chile
    base_conocimiento = [
        (
            ['cv', 'curriculum', 'curriculo', 'hoja de vida', 'resumen'],
            "Para un buen CV de práctica en Chile (idealmente de 1 página), destaca tu **carrera, institución y semestre**, "
            "seguido de tus **proyectos académicos, ayudantías, voluntariados y manejo de herramientas** (Excel, Python, etc.). "
            "¡Tip! Usa nuestra herramienta **Asistente CV IA** en tu panel para optimizarlo automáticamente."
        ),
        (
            ['carta', 'presentacion', 'motivos', 'motivacion'],
            "Una buena carta de presentación debe ser breve (3 párrafos): quién eres y qué carrera estudias, "
            "qué habilidades o proyectos puedes aportar al equipo, y tu disponibilidad horaria (práctica profesional o técnico-profesional). "
            "Puedes generar una personalizada en la sección **Asistente CV IA** de tu cuenta."
        ),
        (
            ['postular', 'postulacion', 'oferta', 'ofertas', 'buscar practica', 'encontrar practica', 'como funciona'],
            "Para postular en **PrácticasPro**: 1) Completa tu perfil y sube tu CV actualizado en PDF; "
            "2) Filtra las ofertas según tu carrera, comuna o modalidad (presencial, híbrida o remota); "
            "3) Haz clic en **Postular** y haz seguimiento desde tu panel de estudiante."
        ),
        (
            ['entrevista', 'reclutador', 'preguntas', 'nervios', 'seleccion'],
            "En una entrevista de práctica buscan **actitud, ganas de aprender y responsabilidad** más que años de experiencia. "
            "Investiga a la empresa antes de entrar, prepara un ejemplo de un trabajo en equipo o proyecto universitario que hayas resuelto, "
            "y ten listas 1 o 2 preguntas sobre las tareas del área."
        ),
        (
            ['sueldo', 'pago', 'remuneracion', 'pagan', 'gratis', 'bono', 'movilizacion', 'colacion', 'plata', 'dinero'],
            "En Chile, según el Código del Trabajo (Art. 8°), las prácticas profesionales **no constituyen contrato de trabajo**, "
            "por lo que no tienen sueldo mínimo obligatorio. Sin embargo, la mayoría de las empresas en PrácticasPro ofrecen "
            "una **asignación compensatoria** para cubrir gastos de colación y movilización."
        ),
        (
            ['seguro', 'escolar', 'accidente', 'certificado', 'alumno regular', 'inscripcion'],
            "Para iniciar tu práctica en Chile es obligatorio contar con el **Seguro Escolar** (Ley 16.744), que te cubre en el trayecto "
            "y dentro de la empresa. Debes solicitar la **carta o certificado de práctica** en la dirección de carrera o portal de tu universidad/CFT/IP antes de empezar."
        ),
        (
            ['sin experiencia', 'no tengo experiencia', 'primera vez', 'nunca he trabajado'],
            "¡No te preocupes! Las empresas que publican prácticas saben que estás comenzando. "
            "Reemplaza la experiencia laboral por **proyectos de título, trabajos de ramos complejos, ayudantías, certificaciones online** "
            "y habilidades blandas como trabajo en equipo y proactividad."
        ),
        (
            ['duracion', 'horas', 'meses', 'tiempo', 'cuanto dura'],
            "La duración de la práctica depende de la malla curricular de tu institución (generalmente entre **360 y 720 horas**, "
            "equivalentes a 2 a 6 meses). Asegúrate de revisar las horas exigidas por tu jefe de carrera antes de confirmar la fecha de término."
        ),
        (
            ['remoto', 'teletrabajo', 'hibrido', 'presencial', 'online', 'casa'],
            "En PrácticasPro contamos con ofertas **presenciales, híbridas y 100% remotas**. "
            "Usa los filtros del buscador principal para seleccionar la modalidad que mejor se adapte a tus horarios de estudio."
        ),
        (
            ['gracias', 'muchas gracias', 'vale', 'te pasaste', 'genial', 'super', 'bkn', 'bacan'],
            "¡De nada! Mucho éxito en tu búsqueda y postulaciones. Si necesitas revisar tu perfil o preparar tu carta, aquí estoy para ayudarte. 🚀"
        ),
    ]

    for palabras_clave, respuesta in base_conocimiento:
        if any(palabra in msg for palabra in palabras_clave):
            return respuesta

    # 4. Respuesta por defecto si no coincide con ninguna palabra clave
    return (
        "¡Hola! Soy **ProBot IA** de PrácticasPro. En este momento tengo alta demanda en mi motor avanzado, "
        "pero puedo ayudarte de inmediato si me preguntas sobre: **cómo mejorar tu CV, cartas de presentación, "
        "entrevistas, cómo postular, remuneración/movilización o el seguro escolar en Chile**. ¿Sobre cuál de estos temas te gustaría saber?"
    )


def _generar_fallback_cv_ia(tipo: str, carrera: str, puesto_objetivo: str, habilidades: str, experiencia: str) -> str:
    """Genera una carta o revisión de CV estructurada usando los datos del estudiante si Gemini falla."""
    carrera_txt = carrera if carrera else "mi carrera profesional"
    puesto_txt = puesto_objetivo if puesto_objetivo else "Práctica Profesional"
    hab_txt = habilidades if habilidades else "trabajo en equipo, aprendizaje rápido y herramientas digitales"
    exp_txt = experiencia if experiencia else "proyectos académicos desarrollados durante mi formación"

    if tipo == 'carta':
        return (
            f"Estimado/a [Nombre del Reclutador/a o Equipo de Selección] de [Nombre de la Empresa]:\n\n"
            f"Junto con saludar, me dirijo a ustedes para postular al cargo de **{puesto_txt}**. "
            f"Actualmente soy estudiante de **{carrera_txt}** y busco una oportunidad donde pueda aplicar mis conocimientos "
            f"académicos y seguir desarrollándome profesionalmente en un entorno dinámico.\n\n"
            f"Durante mi formación he fortalecido competencias clave en **{hab_txt}**, además de participar en **{exp_txt}**, "
            f"instancias que me han permitido desarrollar capacidad analítica, compromiso y orientación al logro de objetivos.\n\n"
            f"Agradezco de antemano su tiempo y consideración. Quedo a su entera disposición para coordinar una entrevista y "
            f"conversar sobre cómo puedo aportar valor al equipo.\n\n"
            f"Atentamente,\n"
            f"[Tu Nombre Completo]\n"
            f"[Tu Teléfono / Correo Electrónico]"
        )

    return (
        f"### 1. Fortalezas del Perfil\n"
        f"Como estudiante de **{carrera_txt}** apuntando a **{puesto_txt}**, tu principal ventaja es la combinación de formación "
        f"actualizada y conocimientos en **{hab_txt}**. Destacar tu experiencia en **{exp_txt}** demuestra iniciativa y aplicación práctica.\n\n"
        f"### 2. Palabras Clave Recomendadas para tu CV\n"
        f"• **Competencias Técnicas:** {hab_txt}\n"
        f"• **Habilidades Transversales:** Trabajo colaborativo, resolución de problemas, adaptabilidad, cumplimiento de plazos.\n"
        f"• **Enfoque:** {puesto_txt}, Mejora continua, Gestión de proyectos.\n\n"
        f"### 3. Sugerencias de Redacción\n"
        f"1. **Cuantifica tus logros:** En lugar de describir tareas genéricas en tus proyectos, indica qué problema resolviste y qué herramienta usaste.\n"
        f"2. **Encabezado claro:** Incluye tu disponibilidad horaria y las horas requeridas de práctica según tu institución.\n"
        f"3. **Formato limpio:** Mantén tu CV en una sola página en formato PDF y adapta tu perfil profesional al área de **{puesto_txt}**."
    )


def _consultar_gemini_con_respaldo(prompt, instrucciones):
    """Consulta Gemini rotando modelos (principal + ligero vigente) y claves API con timeout estricto."""
    claves = [k for k in [os.environ.get('GEMINI_API_KEY_2'), GEMINI_API_KEY] if k]
    
    # Si gemini-3.8-flash está congestionado (503/504), salta a gemini-3.5-flash-lite
    modelos = ['gemini-3.5-flash-lite', 'gemini-3.8-flash']
    
    opciones_http = types.HttpOptions(timeout=18000)

    for modelo in modelos:
        for idx, clave in enumerate(claves, start=1):
            client = genai.Client(api_key=clave, http_options=opciones_http)
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=instrucciones
                    )
                )
                if response and response.text:
                    print(f"🚀 IA respondió con {modelo} (Clave #{idx})")
                    return response.text
            except Exception as err:
                print(f"⚠ Fallo con {modelo} (Clave #{idx}): {str(err)}")
                continue

    print("❌ Todos los intentos con Gemini fallaron. Activando respaldo local.")
    return None

def probot_ia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_usuario = data.get('mensaje', '').strip()

            if not mensaje_usuario:
                return JsonResponse({'respuesta': 'Por favor escribe una pregunta para poder ayudarte.'})

            instrucciones = (
                "Eres ProBot IA, el asistente virtual oficial del portal PrácticasPro en Chile. "
                "Tu objetivo es ayudar a estudiantes a encontrar su primera práctica profesional, "
                "revisar o mejorar su CV, dar tips para entrevistas de trabajo y resolver dudas sobre prácticas en Chile. "
                "Responde en español de forma profesional, cercana y breve (máximo 2 párrafos)."
            )

            respuesta_texto = _consultar_gemini_con_respaldo(mensaje_usuario, instrucciones)

            # Si Gemini responde, devolvemos su respuesta; si no, usamos el diccionario de palabras clave
            if not respuesta_texto:
                respuesta_texto = _respuesta_fallback_probot(mensaje_usuario)

            return JsonResponse({'respuesta': respuesta_texto})

        except Exception as e:
            print("❌ ERROR CRÍTICO EN PROBOT IA:", str(e))
            return JsonResponse({
                'respuesta': '¡Hola! Soy ProBot IA. En este momento estoy procesando muchas consultas, pero dime: ¿necesitas ayuda con tu CV, carta de presentación o tips para tu entrevista?'
            }, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def asistente_cv_ia(request):
    """Generador de Cartas de Presentación y Revisor de CV con ProBot IA."""
    if request.session.get('user_rol') != 'estudiante':
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'Sesión expirada. Recarga la página e inicia sesión.'}, status=401)
        return redirect('login')

    user_id = request.session.get('user_id')
    db = firestore.client()
    user_doc = db.collection('usuarios').document(user_id).get()
    estudiante_data = user_doc.to_dict() if user_doc.exists else {}

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo = data.get('tipo', 'carta')
            carrera = data.get('carrera', estudiante_data.get('carrera', '')).strip()
            habilidades = data.get('habilidades', '').strip()
            experiencia = data.get('experiencia', '').strip()
            puesto_objetivo = data.get('puesto_objetivo', '').strip()

            if not habilidades and not experiencia:
                return JsonResponse({'success': False, 'error': 'Por favor ingresa tus habilidades o un resumen de tu experiencia/proyectos.'})

            if tipo == 'carta':
                prompt = (
                    f"Genera una Carta de Presentación profesional, concisa y persuasiva para una postulación de práctica profesional en Chile.\n"
                    f"- Carrera: {carrera}\n"
                    f"- Cargo / Área Objetivo: {puesto_objetivo if puesto_objetivo else 'Práctica Profesional'}\n"
                    f"- Habilidades Clave / Tecnologías: {habilidades}\n"
                    f"- Proyectos / Experiencia Relevante: {experiencia}\n\n"
                    f"Instrucciones:\n"
                    f"1. Estructura la carta en 3 párrafos formales (Saludo/Introducción, Valor Agregado/Proyectos, Cierre/Llamado a la acción).\n"
                    f"2. Utiliza un tono profesional y motivador.\n"
                    f"3. Agrega corchetes [ ] en variables opcionales como [Nombre de la Empresa] si aplica."
                )
            else:
                prompt = (
                    f"Actúa como un reclutador senior y realiza una revisión constructiva de perfil para un estudiante que busca práctica profesional.\n"
                    f"- Carrera: {carrera}\n"
                    f"- Puesto Deseado: {puesto_objetivo if puesto_objetivo else 'Práctica Profesional'}\n"
                    f"- Habilidades / Herramientas: {habilidades}\n"
                    f"- Proyectos / Experiencia redactada: {experiencia}\n\n"
                    f"Instrucciones de Respuesta:\n"
                    f"1. **Fortalezas del Perfil**: Breve análisis de lo más destacado.\n"
                    f"2. **Palabras Clave Recomendadas**: Términos técnicos o de industria que debe incluir en su CV.\n"
                    f"3. **Sugerencias de Redacción**: 3 recomendaciones puntuales para hacer su CV más atractivo para los reclutadores."
                )

            instrucciones = (
                "Eres ProBot CV Coach, el asistente inteligente de empleabilidad de PrácticasPro en Chile. "
                "Respondes de forma estructurada, profesional y clara."
            )

            respuesta_texto = _consultar_gemini_con_respaldo(prompt, instrucciones)

            # Si Gemini falla por completo, generamos el resultado con los datos del formulario
            if not respuesta_texto:
                respuesta_texto = _generar_fallback_cv_ia(
                    tipo=tipo,
                    carrera=carrera,
                    puesto_objetivo=puesto_objetivo,
                    habilidades=habilidades,
                    experiencia=experiencia
                )

            return JsonResponse({'success': True, 'resultado': respuesta_texto})

        except Exception as e:
            print("❌ ERROR EN ASISTENTE CV IA:", str(e))
            return JsonResponse({'success': False, 'error': f"Ocurrió un error: {str(e)}"}, status=500)

    context = {
        'estudiante': estudiante_data,
        'carreras': CARRERAS_LISTA
    }
    return render(request, 'cv_ia.html', context)
# ==========================================
# CHATBOT PROBOT IA
# ==========================================


# ==========================================
# VISTAS GENERALES
# ==========================================

def quienes_somos(request):
    """Página informativa sobre PrácticasPro, términos y privacidad."""
    return render(request, 'quienes_somos.html')

def index(request):
    try:
        db = firestore.client()

        # 1. Ofertas activas
        ofertas_ref = db.collection('ofertas').where('estado', '==', 'activa').stream()
        lista_ofertas = [{**doc.to_dict(), 'id': doc.id} for doc in ofertas_ref]
        total_ofertas = len(lista_ofertas)

        # 2. Empresas registradas
        empresas_ref = db.collection('usuarios').where('rol', '==', 'empresa').stream()
        total_empresas = len(list(empresas_ref))

        # 3. Estudiantes registrados
        estudiantes_ref = db.collection('usuarios').where('rol', '==', 'estudiante').stream()
        total_estudiantes = len(list(estudiantes_ref))

    except Exception as e:
        print(f"⚠️ Error al obtener métricas para index: {e}")
        lista_ofertas = []
        total_ofertas = 0
        total_empresas = 0
        total_estudiantes = 0

    context = {
        'total_ofertas': total_ofertas,
        'total_empresas': total_empresas,
        'total_estudiantes': total_estudiantes,
        'ofertas_destacadas': lista_ofertas[:6]
    }
    return render(request, 'index.html', context)
def dashboard_view(request):
    rol = request.session.get('user_rol')
    if rol == 'estudiante':
        return redirect('home_estudiante')
    elif rol == 'empresa':
        return redirect('home_empresa')
    elif rol == 'admin':
        return redirect('home_admin')
    
    return redirect('login')


# ==========================================
# AUTENTICACIÓN Y REGISTRO
# ==========================================
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password')
        nombre = request.POST.get('nombre').strip()
        rol = request.POST.get('rol')

        # 1. Validación de dominio SÓLO para estudiantes
        if rol == 'estudiante':
            if not (email.endswith('@duocuc.cl') or email.endswith('@alumnos.duoc.cl')):
                messages.error(request, 'Los estudiantes deben registrarse con su correo institucional (@duocuc.cl o @alumnos.duoc.cl).')
                return render(request, 'register.html')

        try:
            # 2. Crear usuario en Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=nombre
            )

            # 3. Guardar en Firestore
            db = firestore.client()
            db.collection('usuarios').document(user.uid).set({
                'nombre': nombre,
                'email': email,
                'rol': rol,
                'es_premium': False,
                'region': 'Región Metropolitana',
                'creado_en': firestore.SERVER_TIMESTAMP
            })

            # 4. Iniciar sesión temporalmente vía API REST para obtener el idToken y enviar el correo de verificación
            login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
            login_res = requests.post(login_url, json={"email": email, "password": password, "returnSecureToken": True})
            
            if login_res.ok:
                id_token = login_res.json().get('idToken')
                verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
                requests.post(verify_url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token})

            messages.success(request, 'Cuenta creada. Por favor, revisa tu correo para verificar tu cuenta antes de iniciar sesión.')
            return redirect('login')

        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                messages.error(request, 'Este correo ya está registrado.')
            else:
                messages.error(request, f'Error al registrar: {error_msg}')

    return render(request, 'register.html')


def login_view(request):
    if request.session.get('user_id'):
        rol = request.session.get('user_rol')
        if rol == 'admin': return redirect('home_admin')
        elif rol == 'empresa': return redirect('home_empresa')
        elif rol == 'estudiante': return redirect('home_estudiante')
        else: return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password')

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url, json=payload)
        data = response.json()

        if "error" in data:
            messages.error(request, "Correo o contraseña incorrectos.")
        else:
            uid = data['localId']

       #     # Validar si el correo está verificado a través de Firebase Admin
       #     firebase_user = auth.get_user(uid)
       #     if not firebase_user.email_verified:
       #         messages.error(request, "Tu cuenta aún no está verificada. Por favor, revisa tu correo electrónico.")
       #         return render(request, 'login.html')

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

                if rol == 'estudiante': return redirect('home_estudiante')
                elif rol == 'empresa': return redirect('home_empresa')
                elif rol == 'admin': return redirect('home_admin')
                else: return redirect('index') 
            else:
                messages.error(request, "El usuario no tiene un perfil registrado.")

    return render(request, 'login.html')


# --- NUEVAS VISTAS: AGREGAR AL FINAL DE views.py ---

def forgot_password_view(request):
    """Vista para solicitar el restablecimiento de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        requests.post(url, json=payload)
        
        messages.success(request, "Si el correo está registrado, recibirás un enlace seguro para restablecer tu contraseña.")
        return redirect('login')

    return render(request, 'forgot_password.html')

def solicitar_cambio_password(request):
    """Permite al usuario logueado solicitar un cambio de contraseña por correo"""
    if not request.session.get('user_id'):
        return redirect('login')
        
    email = request.session.get('user_email')
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    requests.post(url, json=payload)
    
    messages.success(request, "Se ha enviado un enlace seguro a tu correo para cambiar tu contraseña.")
    
    rol = request.session.get('user_rol')
    if rol == 'empresa': return redirect('perfil_empresa')
    return redirect('perfil_estudiante')

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
            try:
                foto_url = _procesar_imagen_base64(request.FILES['foto'])
            except Exception as e:
                print("❌ Error procesando foto de estudiante:", str(e))
                messages.warning(request, "Se guardaron tus datos, pero hubo un problema al procesar la imagen.")

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

# Lista global de carreras para usar en filtros y formularios
CARRERAS_LISTA = [
    "Ingeniería en Construcción",
    "Ingeniería en Prevención de Riesgos",
    "Técnico en Construcción",
    "Ingeniería en Informática",
    "Analista Programador",
    "Ingeniería en Redes y Telecomunicaciones",
    "Técnico en Desabolladura y Pintura Automotriz",
    "Técnico en Electricidad y Automatización Industrial",
    "Ingeniería en Electricidad y Automatización Industrial",
    "Ingeniería Agrícola",
    "Ingeniería en Mecánica Automotriz y Autotrónica",
    "Técnico en Calidad de Alimentos",
    "Técnico Veterinario y Pecuario",
    "Técnico en Operación y Supervisión de Procesos Mineros",
    "Técnico en Mecánica Automotriz y Autotrónica",
    "Técnico en Geología",
    "Técnico en Laboratorio Clínico, Banco de Sangre e Imagenología",
    "Preparador Físico",
    "Técnico en Enfermería",
    "Técnico en Química y Farmacia",
    "Técnico en Odontología",
    "Ingeniería en Marketing Digital",
    "Auditoría",
    "Ingeniería en Gestión Logística",
    "Ingeniería en Comercio Exterior",
    "Ingeniería en Administración, mención Gestión de Personas",
    "Ingeniería en Administración, mención Innovación y Emprendimiento",
    "Ingeniería en Administración, mención Finanzas",
    "Técnico en Administración",
    "Relaciones Públicas y Comunicación Organizacional",
    "Publicidad"
]

def ofertas_list(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')

    # Obtener parámetros de búsqueda del GET
    q = request.GET.get('q', '').strip()
    carrera_filtro = request.GET.get('carrera', '').strip()
    modalidad_filtro = request.GET.get('modalidad', '').strip()

    db = firestore.client()
    ofertas_ref = db.collection('ofertas').where('estado', '==', 'activa').stream()

    lista_ofertas = []
    for doc in ofertas_ref:
        data = doc.to_dict()
        data['id'] = doc.id

        # 1. Filtro por Carrera
        if carrera_filtro and data.get('carrera', '').strip() != carrera_filtro:
            continue

        # 2. Filtro por Modalidad
        if modalidad_filtro and data.get('modalidad', '').strip() != modalidad_filtro:
            continue

        # 3. Filtro por Búsqueda (Título, Empresa o Descripción)
        if q:
            q_lower = q.lower()
            titulo_match = q_lower in data.get('titulo', '').lower()
            empresa_match = q_lower in data.get('empresa_nombre', '').lower()
            descripcion_match = q_lower in data.get('descripcion', '').lower()
            if not (titulo_match or empresa_match or descripcion_match):
                continue

        lista_ofertas.append(data)

    context = {
        'ofertas': lista_ofertas,
        'q': q,
        'carrera_filtro': carrera_filtro,
        'modalidad_filtro': modalidad_filtro,
        'carreras': CARRERAS_LISTA,
        'total_resultados': len(lista_ofertas)
    }

    return render(request, 'ofertas_list.html', context)
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
        logos_cache = {}
        ofertas_cache = {}

        for doc in postulaciones_ref:
            data = doc.to_dict()
            data['id'] = doc.id

            # 1. Obtener detalles completos de la oferta
            oferta_id = data.get('oferta_id')
            oferta_data = {}
            if oferta_id:
                if oferta_id not in ofertas_cache:
                    of_doc = db.collection('ofertas').document(oferta_id).get()
                    ofertas_cache[oferta_id] = of_doc.to_dict() if of_doc.exists else {}
                oferta_data = ofertas_cache[oferta_id]

            data['oferta_modalidad'] = oferta_data.get('modalidad', '')
            data['oferta_carrera'] = oferta_data.get('carrera', '')
            data['oferta_descripcion'] = oferta_data.get('descripcion', '')

            # 2. Obtener logo de la empresa
            empresa_id = data.get('empresa_id') or oferta_data.get('empresa_id', '')
            data['empresa_id'] = empresa_id

            if empresa_id:
                if empresa_id not in logos_cache:
                    emp_doc = db.collection('usuarios').document(empresa_id).get()
                    emp_data = emp_doc.to_dict() if emp_doc.exists else {}
                    logos_cache[empresa_id] = emp_data.get('logo_url', '')
                data['logo_url'] = logos_cache[empresa_id]
            else:
                data['logo_url'] = ''

            lista_postulaciones.append(data)

        context = {
            'postulaciones': lista_postulaciones
        }
        
        return render(request, 'mis_postulaciones.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al cargar tus postulaciones: {str(e)}")
        return redirect('home_estudiante')




def ver_perfil_empresa_publico(request, empresa_id):
    """Vista pública para que los estudiantes consulten el perfil e historial de una empresa."""
    if not request.session.get('user_id'):
        return redirect('login')

    try:
        db = firestore.client()
        empresa_doc = db.collection('usuarios').document(empresa_id).get()

        if not empresa_doc.exists:
            messages.error(request, "El perfil de la empresa no fue encontrado.")
            return redirect('ofertas_list')

        empresa_data = empresa_doc.to_dict()

        # Cargar ofertas de práctica activas publicadas por esta empresa
        ofertas_ref = db.collection('ofertas').where('empresa_id', '==', empresa_id).where('estado', '==', 'activa').stream()
        ofertas_empresa = [{**doc.to_dict(), 'id': doc.id} for doc in ofertas_ref]

        context = {
            'empresa': empresa_data,
            'ofertas': ofertas_empresa,
            'total_ofertas': len(ofertas_empresa)
        }
        return render(request, 'ver_perfil_empresa.html', context)

    except Exception as e:
        messages.error(request, f"Error al cargar el perfil de la empresa: {str(e)}")
        return redirect('ofertas_list')
# ==========================================
# VISTAS DE EMPRESA
# ==========================================

def home_empresa(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    empresa_id = request.session.get('user_id')
    db = firestore.client()

    # Contar ofertas de la empresa
    ofertas_ref = db.collection('ofertas').where('empresa_id', '==', empresa_id).stream()
    total_ofertas = len(list(ofertas_ref))

    # Contar postulaciones recibidas
    postulaciones_ref = db.collection('postulaciones').where('empresa_id', '==', empresa_id).stream()
    total_postulantes = len(list(postulaciones_ref))

    context = {
        'nombre': request.session.get('user_name'),
        'total_ofertas': total_ofertas,
        'total_postulantes': total_postulantes,
    }
    return render(request, 'home_empresa.html', context)



def perfil_empresa(request):
    user_id = request.session.get('user_id')
    user_rol = request.session.get('user_rol')

    if not user_id or user_rol != 'empresa':
        messages.error(request, "Acceso no autorizado.")
        return redirect('login')

    db = firestore.client()
    user_ref = db.collection('usuarios').document(user_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        rut = request.POST.get('rut')
        telefono = request.POST.get('telefono')
        sitio_web = request.POST.get('sitio_web')
        rubro = request.POST.get('rubro')
        descripcion = request.POST.get('descripcion')

        doc_actual = user_ref.get()
        data_actual = doc_actual.to_dict() if doc_actual.exists else {}
        logo_url = data_actual.get('logo_url', '')

        if 'logo' in request.FILES:
            try:
                logo_url = _procesar_imagen_base64(request.FILES['logo'])
            except Exception as e:
                print("❌ Error procesando logo de empresa:", str(e))
                messages.warning(request, "Se guardaron los datos, pero hubo un problema al procesar el logo.")

        user_ref.update({
            'nombre': nombre,
            'rut': rut,
            'telefono': telefono,
            'sitio_web': sitio_web,
            'rubro': rubro,
            'descripcion': descripcion,
            'logo_url': logo_url
        })

        request.session['user_name'] = nombre

        messages.success(request, "¡Perfil de la empresa actualizado exitosamente!")
        return redirect('home_empresa')

    doc = user_ref.get()
    empresa_data = doc.to_dict() if doc.exists else {}

    return render(request, 'perfil_empresa.html', {'empresa': empresa_data})


def crear_oferta(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        requisitos = request.POST.get('requisitos')
        modalidad = request.POST.get('modalidad')
        # NUEVO: Capturamos la carrera del formulario HTML
        carrera = request.POST.get('carrera') 
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
                'carrera': carrera, # NUEVO: Guardamos la carrera en Firebase
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
    fotos_cache = {}

    for doc in postulaciones_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        
        estudiante_id = data.get('estudiante_id')
        if estudiante_id:
            if estudiante_id not in fotos_cache:
                est_doc = db.collection('usuarios').document(estudiante_id).get()
                est_data = est_doc.to_dict() if est_doc.exists else {}
                fotos_cache[estudiante_id] = est_data.get('foto_url', '')
            data['foto_url'] = fotos_cache[estudiante_id]
        else:
            data['foto_url'] = ''

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


def eliminar_oferta_admin(request, oferta_id):
    if request.method == 'POST':
        print(f"--- INTENTANDO BORRAR LA OFERTA CON ID: {oferta_id} ---")
        try:
            db = firestore.client()
            # Intenta borrar el documento
            db.collection('ofertas').document(oferta_id).delete()
            print("--- ¡BORRADO EXITOSO EN FIREBASE! ---")
            messages.success(request, 'La oferta ha sido eliminada exitosamente.')
            
        except Exception as e:
            print(f"--- ERROR AL BORRAR EN FIREBASE: {e} ---")
            messages.error(request, f'Error al eliminar en Firebase: {e}')
            
    return redirect('home_admin')




#########################
