import os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import auth, firestore

# Reemplaza esto con tu 'Clave de API web' de Firebase Console (empieza por AIzaSy...)
FIREBASE_WEB_API_KEY = "AIzaSyCqOyF0LYCHlHGU44ClVfG5DPeCPnUGRHo"

# --- VISTAS GENERALES ---
def index(request):
    return render(request, 'index.html')

def dashboard_view(request):
    rol = request.session.get('user_rol')
    if rol == 'estudiante':
        return redirect('home_estudiante')
    elif rol == 'empresa':
        return redirect('home_empresa')
    return redirect('login')

# --- AUTENTICACIÓN Y REGISTRO ---
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

                if rol == 'estudiante':
                    return redirect('home_estudiante')
                elif rol == 'empresa':
                    return redirect('home_empresa')
                else:
                    return redirect('index')
            else:
                messages.error(request, "El usuario no tiene un perfil registrado.")

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')

# --- VISTAS DE ESTUDIANTE ---
def home_estudiante(request):
    if request.session.get('user_rol') != 'estudiante':
        return redirect('login')
    return render(request, 'home_estudiante.html', {'nombre': request.session.get('user_name')})

def perfil_estudiante(request):
    return render(request, 'base.html')

def ofertas_list(request):
    return render(request, 'base.html')

def oferta_detail(request, oferta_id):
    return render(request, 'base.html')

def mis_postulaciones(request):
    return render(request, 'base.html')

# --- VISTAS DE EMPRESA ---
def home_empresa(request):
    if request.session.get('user_rol') != 'empresa':
        return redirect('login')
    return render(request, 'home_empresa.html', {'nombre': request.session.get('user_name')})

def perfil_empresa(request):
    return render(request, 'base.html')

def crear_oferta(request):
    return render(request, 'base.html')

def mis_ofertas(request):
    return render(request, 'base.html')

def ver_postulantes(request, oferta_id):
    return render(request, 'base.html')