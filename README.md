# 🚀 PrácticasPro - Red de Vinculación Duoc UC

![Django](https://img.shields.io/badge/Django-6.1.1-092E20?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![Gemini AI](https://img.shields.io/badge/Google%20Gemini-3.8%20Flash-8E75B2?style=for-the-badge&logo=googlegemini)
![Firebase](https://img.shields.io/badge/Firebase-Auth%20%26%20Firestore-FFCA28?style=for-the-badge&logo=firebase)

> Plataforma web de vinculación laboral y geolocalización de prácticas profesionales para estudiantes de **Duoc UC**, integrada con un asistente virtual impulsado por inteligencia artificial.

---

## 📸 Captura del Proyecto

![Vista Principal de PrácticasPro](documentacion/banner.png)

---

## ✨ Características Principales

* 🤖 **ProBot IA (Asistente Virtual):** Chatbot inteligente impulsado por la API de **Google Gemini (`gemini-3.8-flash`)**, con lógica de resiliencia automática de 4 reintentos y modo fallback contingente.
* 🗺️ **Mapa Interactivo de Ofertas:** Geolocalización de vacantes de prácticas en tiempo real utilizando **Leaflet.js** y cartografía de alta velocidad **CARTO Voyager**.
* 🔐 **Autenticación e Integración Cloud:** Inicio de sesión seguro integrado con **Firebase Identity Toolkit** y base de datos NoSQL en **Firestore**.
* 🛡️ **Seguridad de Credenciales:** Manejo aislado de llaves sensibles mediante archivos JSON locales protegidos por `.gitignore`.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
| :--- | :--- |
| **Backend** | Python 3.12, Django 6.1.1 |
| **Inteligencia Artificial** | Google GenAI SDK (`google-genai`), Modelo `gemini-3.8-flash` |
| **Base de Datos & Auth** | Google Firebase, Firestore, SQLite3 |
| **Frontend** | HTML5, Tailwind CSS, JavaScript ES6+, Leaflet.js |
| **Servicios de Mapas** | CARTO Voyager Basemaps / OpenStreetMap |

---

## ⚙️ Instalación y Configuración Local

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tomasPozoo/Pr-cticasPro.git](https://github.com/tomasPozoo/Pr-cticasPro.git)
cd Pr-cticasPro
