from django.shortcuts import render

# Vistas Públicas e Inicio
def index(request):
    return render(request, 'index.html')

# Autenticación y Registro
def login_usuario(request):
    return render(request, 'login-usuario.html')

def login_empresa(request):
    return render(request, 'login-empresa.html')

def registro_usuario(request):
    return render(request, 'registro-usuario.html')

def registro_empresa(request):
    return render(request, 'registro-empresa.html')

# Plataforma Interna
def dashboard_estudiante(request):
    return render(request, 'dashboard-estudiante.html')

def suscripcion(request):
    return render(request, 'suscripcion.html')