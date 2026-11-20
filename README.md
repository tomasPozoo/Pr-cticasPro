# PrácticasPro

[![Live Demo](https://img.shields.io/badge/Producción-practicaspro.onrender.com-00C7B7?style=for-the-badge&logo=render)](https://practicaspro.onrender.com)
![Django](https://img.shields.io/badge/Django-6.1.1-092E20?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![Gemini AI](https://img.shields.io/badge/Google%20Gemini-3.8%20Flash-8E75B2?style=for-the-badge&logo=googlegemini)
![Firebase](https://img.shields.io/badge/Firebase-Auth%20%26%20Firestore-FFCA28?style=for-the-badge&logo=firebase)

Plataforma web de vinculación laboral y geolocalización de prácticas profesionales para estudiantes de **Duoc UC**. Integra herramientas de inteligencia artificial para orientación vocacional, redacción de cartas de presentación y revisión de currículums.

**Entorno en producción:** [https://practicaspro.onrender.com](https://practicaspro.onrender.com)

---

## Vista General

![Vista Principal de PrácticasPro](static/img/banner.png)

---

## Funcionalidades

- **ProBot IA:** Asistente conversacional basado en **Google Gemini (`gemini-3.8-flash`)** orientado a resolver consultas sobre procesos de práctica, entrevistas técnicas y empleabilidad.
- **Asistente de CV y Cartas:** Módulo de análisis de perfil que genera cartas de presentación personalizadas y sugiere palabras clave y mejoras de redacción según la carrera y el cargo objetivo.
- **Tolerancia a Fallos en API:** Rotación automática entre múltiples claves de API con control estricto de tiempos de espera HTTP para evitar bloqueos de workers ante límites de cuota (`429`) o latencia externa (`504`).
- **Mapa Interactivo de Ofertas:** Visualización georreferenciada de vacantes mediante **Leaflet.js** y cartografía **CARTO Voyager**.
- **Gestión de Usuarios y Roles:** Autenticación diferenciada para estudiantes y empresas sobre **Firebase Authentication** y persistencia en **Cloud Firestore**.

---

## Arquitectura y Tecnologías

| Componente | Tecnología |
| :--- | :--- |
| **Backend** | Python 3.12, Django 6.1.1, Gunicorn |
| **Inteligencia Artificial** | Google GenAI SDK (`google-genai`), `gemini-3.8-flash` |
| **Base de Datos y Auth** | Firebase Authentication, Cloud Firestore |
| **Frontend** | HTML5, Tailwind CSS, JavaScript ES6+, Leaflet.js |
| **Servicios Cartográficos** | CARTO Voyager Basemaps / OpenStreetMap |
| **Infraestructura** | Render Cloud |

---

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone [https://github.com/tomasPozoo/Pr-cticasPro.git](https://github.com/tomasPozoo/Pr-cticasPro.git)
cd Pr-cticasPro