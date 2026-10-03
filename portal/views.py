import os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import auth, firestore

from django.core.files.storage import FileSystemStorage

# Reemplaza esto con tu 'Clave de API web' de Firebase Console (empieza por AIzaSy...)
FIREBASE_WEB_API_KEY = "AIzaSyCqOyF0LYCHlHGU44ClVfG5DPeCPnUGRHo"


# ==========================================
# VISTAS GENERALES
# ==========================================
def quienes_somos(request):
    """Página informativa sobre PrácticasPro, términos y privacidad."""
    return render(request, 'quienes_somos.html')
def index(request):
    return render(request, 'index.html')

def dashboard_view(request):
    # Nota: Tienes un 'dashboard_view.html' en tus templates, pero esta vista 
    # actualmente actúa como un enrutador que redirige según el rol. 
    # Si la idea es solo redirigir, se mantiene así.
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
        rol = request.POST.get('rol')  # 'estudiante' o 'empresa'

        try:
            # 1. Crear usuario en Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=nombre
            )

            # 2. Guardar rol en Firestore
            db = firestore.client()
            db.collection('usuarios').document(user.uid).set({
                'nombre': nombre,
                'email': email,
                'rol': rol,
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

            # Consultar ROL en Firestore
            db = firestore.client()
            doc = db.collection('usuarios').document(uid).get()

            if doc.exists:
                user_data = doc.to_dict()
                rol = user_data.get('rol')

                # Guardar sesión
                request.session['user_id'] = uid
                request.session['user_email'] = email
                request.session['user_name'] = user_data.get('nombre')
                request.session['user_rol'] = rol

                # --- AQUÍ ESTÁ LA CORRECCIÓN ---
                if rol == 'estudiante':
                    return redirect('home_estudiante')
                elif rol == 'empresa':
                    return redirect('home_empresa')
                elif rol == 'admin':
                    return redirect('home_admin') # Ahora sí reconoce al admin y lo redirige
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

    user_uid = request.session.get('user_uid')
    db = firestore.client()

    # 1. Obtener perfil del estudiante
    user_doc = db.collection('usuarios').document(user_uid).get()
    estudiante_data = user_doc.to_dict() if user_doc.exists else {}

    # 2. Contar postulaciones activas del estudiante
    postulaciones_ref = db.collection('postulaciones').where('estudiante_id', '==', user_uid).get()
    total_postulaciones = len(postulaciones_ref)

    # 3. Obtener ofertas disponibles
    ofertas_ref = db.collection('ofertas').stream()
    ofertas = [{'id': doc.id, **doc.to_dict()} for doc in ofertas_ref]

    context = {
        'estudiante': estudiante_data,
        'total_postulaciones': total_postulaciones,
        'total_ofertas': len(ofertas),
        'ofertas': ofertas[:6],  # Mostrar solo las primeras 6
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

        # Obtener datos actuales de Firestore
        doc_actual = user_ref.get()
        data_actual = doc_actual.to_dict() if doc_actual.exists else {}
        foto_url = data_actual.get('foto_url', '')

        # Si el usuario adjuntó una nueva foto
        if 'foto' in request.FILES:
            foto_file = request.FILES['foto']
            fs = FileSystemStorage()
            
            # Nombre de archivo único usando el ID del usuario
            extension = foto_file.name.split('.')[-1]
            nombre_archivo = f"perfiles/{user_id}.{extension}"

            # Si ya existe una foto anterior, la borramos para reemplazarla
            if fs.exists(nombre_archivo):
                fs.delete(nombre_archivo)

            filename = fs.save(nombre_archivo, foto_file)
            foto_url = fs.url(filename)  # Retorna '/media/perfiles/ID_USUARIO.png'

        # Actualizar Firestore
        user_ref.update({
            'nombre': nombre,
            'carrera': carrera,
            'telefono': telefono,
            'bio': bio,
            'foto_url': foto_url
        })

        messages.success(request, "¡Perfil y foto actualizados con éxito!")
        return redirect('perfil_estudiante')

    # GET: Cargar datos para llenar el formulario
    doc = user_ref.get()
    estudiante_data = doc.to_dict() if doc.exists else {}

    return render(request, 'perfil_estudiante.html', {'estudiante': estudiante_data})

def ofertas_list(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')
        
    db = firestore.client()
    # Traer todas las ofertas activas
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

    # Si se envía el formulario con el CV y mensaje
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

            messages.success(request, f"¡Te has postulado con éxito!")
            return redirect('mis_postulaciones')

        except Exception as e:
            messages.error(request, f"Error al procesar la postulación: {str(e)}")

    # Si es GET, muestra el formulario
    return render(request, 'postular_oferta.html', {'oferta': oferta_data})

def mis_postulaciones(request):
    # Proteger la ruta: solo estudiantes
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')

    estudiante_id = request.session.get('user_id')
    db = firestore.client()

    try:
        # Buscar en la colección 'postulaciones' las que sean de este usuario
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
        
        # NUEVO: Capturar las coordenadas
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
                'latitud': latitud,   # Lo guardamos en Firebase
                'longitud': longitud, # Lo guardamos en Firebase
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
    
    # Filtrar solo las ofertas creadas por esta empresa
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
    
    # Obtener oferta
    oferta_doc = db.collection('ofertas').document(oferta_id).get()
    oferta = oferta_doc.to_dict() if oferta_doc.exists else {}

    # Obtener postulantes
    postulaciones_ref = db.collection('postulaciones').where('oferta_id', '==', oferta_id).stream()
    
    postulantes = []
    for doc in postulaciones_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        postulantes.append(data)

    context = {
        'oferta': oferta,
        'oferta_id': oferta_id,  # <-- Asegúrate de incluir este campo
        'postulantes': postulantes,
        'total_postulantes': len(postulantes)
    }

    return render(request, 'ver_postulantes.html', context)

def cambiar_estado_postulacion(request, postulacion_id):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')

    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')  # 'aceptado' o 'rechazado'
        oferta_id = request.POST.get('oferta_id')
        mensaje_respuesta = request.POST.get('mensaje_respuesta', '').strip()

        try:
            db = firestore.client()
            postulacion_ref = db.collection('postulaciones').document(postulacion_id)

            # Actualizamos el estado y el mensaje en la base de datos
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
    # Opcional: Proteger la vista para que solo entren empresas
    if request.session.get('user_rol') != 'empresa':
        messages.error(request, "Acceso denegado. Solo las empresas pueden ver esta página.")
        return redirect('mis_ofertas')

    try:
        db = firestore.client()
        # IMPORTANTE: Cambia 'usuarios' por el nombre real de tu colección si se llama distinto
        estudiante_doc = db.collection('usuarios').document(estudiante_id).get()

        if not estudiante_doc.exists:
            messages.error(request, "El perfil del estudiante no fue encontrado.")
            return redirect('mis_ofertas') # O redirigir a la página anterior

        estudiante_data = estudiante_doc.to_dict()
        
        # Le enviamos los datos al nuevo template que creaste
        return render(request, 'ver_perfil_estudiante.html', {'estudiante': estudiante_data})

    except Exception as e:
        messages.error(request, f"Error al cargar el perfil: {str(e)}")
        return redirect('mis_ofertas')
# ==========================================
# VISTAS DE ADMINISTRADOR
# ==========================================
def ver_perfil_estudiante(request, estudiante_id):
    rol_actual = request.session.get('user_rol')
    print(f"\n--- [DEBUG] CARGANDO PERFIL ESTUDIANTE ---")
    print(f"1. Rol en sesión: '{rol_actual}'")
    print(f"2. ID recibido: '{estudiante_id}'")

    # Validación 1: Rol de usuario
    if rol_actual != 'empresa':
        print("❌ FALLO: El rol de usuario no es 'empresa'. Redirigiendo...")
        messages.error(request, f"Permiso denegado. Rol actual: {rol_actual}")
        return redirect('mis_ofertas')

    try:
        db = firestore.client()
        
        # OJO: Verifica si tu colección se llama 'usuarios' o 'estudiantes'
        doc_ref = db.collection('usuarios').document(estudiante_id)
        estudiante_doc = doc_ref.get()

        print(f"3. Documento existe en Firestore: {estudiante_doc.exists}")

        # Validación 2: Documento en Firestore
        if not estudiante_doc.exists:
            print(f"❌ FALLO: No existe el documento con ID '{estudiante_id}' en la colección 'usuarios'. Redirigiendo...")
            messages.error(request, "El perfil del estudiante no existe en la base de datos.")
            return redirect('mis_ofertas')

        estudiante_data = estudiante_doc.to_dict()
        print(f"4. Datos encontrados: {estudiante_data}")

        # Intentar renderizar la plantilla
        return render(request, 'ver_perfil_estudiante.html', {'estudiante': estudiante_data})

    except Exception as e:
        # Validación 3: Error de código o plantilla
        print(f"❌ EXCEPCIÓN DETECTADA: {type(e).__name__} - {str(e)}")
        messages.error(request, f"Error interno: {str(e)}")
        return redirect('mis_ofertas')
    
    
def home_admin(request):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
    
    db = firestore.client()
    
    # 1. Obtener y contar Usuarios
    usuarios_ref = db.collection('usuarios').stream()
    lista_usuarios = []
    estudiantes_count = 0
    empresas_count = 0
    
    for doc in usuarios_ref:
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        
        rol = user_data.get('rol', '')
        if rol == 'estudiante':
            estudiantes_count += 1
        elif rol == 'empresa':
            empresas_count += 1
            
        lista_usuarios.append(user_data)
        
    # 2. Obtener Publicaciones/Ofertas
    ofertas_ref = db.collection('ofertas').stream()
    lista_ofertas = []
    for doc in ofertas_ref:
        oferta_data = doc.to_dict()
        oferta_data['id'] = doc.id
        lista_ofertas.append(oferta_data)
        
    context = {
        'nombre': request.session.get('user_name', 'Administrador'),
        'usuarios': lista_usuarios,
        'ofertas': lista_ofertas,
        'total_usuarios': len(lista_usuarios),
        'estudiantes_count': estudiantes_count,
        'empresas_count': empresas_count,
        'total_ofertas': len(lista_ofertas),
    }
    return render(request, 'home_admin.html', context)

def eliminar_usuario(request, usuario_id):
    if request.session.get('user_rol') != 'admin':
        return redirect('login')
    
    try:
        # 1. Eliminar de Firebase Authentication
        auth.delete_user(usuario_id)
        
        # 2. Eliminar el documento de Firestore
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
        # Eliminar el documento de la oferta en Firestore
        db = firestore.client()
        db.collection('ofertas').document(oferta_id).delete()
        
        messages.success(request, "Oferta de práctica eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la oferta: {str(e)}")
        
    return redirect('home_admin')