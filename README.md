# 🎓 PrácticasPro - Portal de Prácticas Profesionales & Panel Admin

Plataforma web integral desarrollada con **Django** y **Firebase Firestore** diseñada para conectar a estudiantes con empresas para sus prácticas profesionales. La plataforma incluye un modelo **Freemium / Premium**, integración con pasarela de **pagos**, métricas analíticas en tiempo real y un panel de administración avanzado.

---

## 🚀 Características Principales

### 👤 Módulo de Estudiantes
* **Catálogo de Prácticas:** Búsqueda y postulación a ofertas en tiempo real.
* **Modelo Freemium / Premium:** Acceso a ventajas exclusivas al actualizar el plan.
* **Flujo de Pagos Integrado:** Procesamiento seguro de suscripciones Premium.

### 🏢 Módulo de Empresas
* **Publicación de Ofertas:** Creación y administración de convocatorias de práctica.
* **Gestión de Postulantes:** Visualización y seguimiento de solicitudes recibidas.

### 🛡️ Módulo de Administración (`home_admin`)
* **KPIs Analíticos:**
  * Total de usuarios registrados (Estudiantes Free/Premium y Empresas).
  * Tasa de conversión Freemium $\rightarrow$ Premium.
  * Módulo financiero con **ingresos acumulados en CLP**.
  * Promedio de postulantes por oferta y totales generales.
* **Visualización de Datos con Chart.js:**
  * Gráfico de rosquilla (*Doughnut*) para la distribución de roles y cuentas Premium.
  * Gráfico de barras (*Bar Chart*) para el estado de las postulaciones (Pendientes, Aceptadas, Rechazadas).
* **Gestión de Usuarios:**
  * Tabla interactiva de usuarios registrados.
  * Eliminación segura de usuarios directamente en Firestore con diálogo de confirmación.
* **Exportación de Reportes a CSV:**
  * Descarga instantánea de reportes en formato CSV (con compatibilidad UTF-8 BOM para MS Excel) para:
    1. Usuarios
    2. Suscripciones / Pagos
    3. Ofertas de Práctica

---

## 🛠️ Tecnologías Utilizadas

| Categoría | Tecnología |
| :--- | :--- |
| **Backend** | Python 3, Django 4.x |
| **Base de Datos** | Google Firebase Firestore (NoSQL) |
| **Pasarela de Pagos** | Mercado Pago API / Webhooks |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Bootstrap Icons |
| **Gráficos & Analítica** | Chart.js |
| **Formatos de Salida** | CSV (Módulo nativo `csv` de Python) |

---

## 📂 Estructura del Proyecto

```text
.
├── portal/
│   ├── templates/
│   │   ├── home_admin.html         # Panel principal de administración con gráficos
│   │   ├── login.html
│   │   └── ...
│   ├── views.py                    # Vistas (Lógica de pagos, métricas, CRUD y CSV)
│   ├── urls.py                     # Definición de rutas del sistema
│   └── ...
├── manage.py
├── requirements.txt                # Dependencias del proyecto
└── README.md