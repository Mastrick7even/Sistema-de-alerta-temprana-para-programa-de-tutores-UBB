# Sistema de Alerta Temprana - Programa de Tutores UBB

[![Django](https://img.shields.io/badge/Django-3.2.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Sistema web de gestión y seguimiento para el **Programa de Tutores** de la Universidad del Bío-Bío. Permite identificar estudiantes en riesgo académico mediante alertas tempranas, gestión de tutorías y seguimiento personalizado.

## 📋 Descripción

El SAT (Sistema de Alerta Temprana) es una plataforma web desarrollada con Django que facilita la gestión integral del Programa de Tutores de la UBB. Permite a tutores y encargados de carrera:

- **Monitorear** el estado académico de estudiantes en tiempo real
- **Registrar** observaciones y alertas temprana de riesgo
- **Gestionar** tutorías individuales y grupales
- **Generar** reportes y fichas de seguimiento en PDF
- **Visualizar** estadísticas mediante dashboards interactivos

---

## ✨ Funcionalidades Principales

### 🎯 Dashboard Inteligente
- KPIs de estudiantes por nivel de riesgo (Alto, Medio, Bajo)
- Gráficos de distribución por año de ingreso
- Bitácora de observaciones recientes
- Filtros por carrera, fecha y tipo de alerta

### 👥 Gestión de Estudiantes
- Listado de estudiantes asignados a cada tutor
- Fichas individuales con historial académico completo
- Información socioeconómica y beneficios
- Búsqueda y filtrado avanzado

### 📝 Bitácora de Seguimiento
- Registro de observaciones con fechas y alertas asociadas
- Sistema de alarmas categorizadas por tipo
- Edición y eliminación de registros
- Exportación a PDF

### 📚 CRUD de Tutorías
- Creación de tutorías individuales y grupales
- Registro de asistencia de estudiantes
- Edición y eliminación con control de permisos
- Historial completo de tutorías realizadas

### 🔐 Control de Acceso por Roles
- **Tutor**: Acceso a sus estudiantes y tutorías asignadas
- **Encargado de Carrera**: Vista global de todos los estudiantes
- Navegación adaptativa según rol de usuario

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 3.2.6** - Framework web principal
- **Python 3.8+** - Lenguaje de programación
- **SQLite** - Base de datos (desarrollo)
- **PostgreSQL** - Base de datos (producción)

### Frontend
- **Argon Dashboard** - Template Bootstrap 4
- **Chart.js** - Gráficos interactivos
- **Font Awesome** - Iconografía
- **jQuery** - Interacciones dinámicas

### Herramientas
- **WeasyPrint / xhtml2pdf** - Generación de PDFs
- **Docker** - Contenedorización
- **Gunicorn** - Servidor WSGI para producción
- **WhiteNoise** - Servir archivos estáticos

---

## 🚀 Instalación

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- virtualenv (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/Mastrick7even/Sistema-de-alerta-temprana-para-programa-de-tutores-UBB.git
cd tesis-sat-programatutores
```

2. **Crear entorno virtual**
```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Crear archivo .env en la raíz del proyecto
cp .env.sample .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Poblar base de datos** (opcional)
```bash
python manage.py poblar_bd
```

7. **Crear superusuario**
```bash
python manage.py createsuperuser
```

8. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

9. **Acceder a la aplicación**
```
http://127.0.0.1:8000/
```

---

## 📁 Estructura del Proyecto

```
tesis-sat-programatutores/
│
├── core/                      # Configuración principal de Django
│   ├── settings.py           # Configuraciones globales
│   ├── urls.py               # URLs principales
│   └── wsgi.py               # Punto de entrada WSGI
│
├── sat/                       # App principal del SAT
│   ├── models.py             # Modelos de datos
│   ├── views.py              # Vistas y lógica de negocio
│   ├── forms.py              # Formularios de Django
│   ├── urls.py               # URLs de la app
│   ├── templates/sat/        # Templates HTML
│   ├── templatetags/         # Template tags personalizados
│   ├── management/commands/  # Comandos personalizados
│   └── migrations/           # Migraciones de BD
│
├── apps/
│   ├── authentication/       # Sistema de autenticación
│   ├── home/                 # Vistas estáticas
│   ├── static/               # Archivos CSS, JS, imágenes
│   └── templates/            # Templates base y componentes
│       ├── layouts/          # Layouts principales
│       └── includes/         # Componentes reutilizables
│
├── requirements.txt          # Dependencias Python
├── manage.py                 # CLI de Django
├── Dockerfile                # Configuración Docker
├── docker-compose.yml        # Orquestación de contenedores
└── README.md                 # Este archivo
```

---

## 🎯 Modelos de Datos Principales

- **Usuario**: Tutores y encargados con roles diferenciados
- **Estudiante**: Información académica y socioeconómica
- **Bitacora**: Registro de observaciones y seguimiento
- **Tutoria**: Sesiones de tutoría con asistencia
- **Alarma**: Sistema de alertas tempranas
- **Estado**: Niveles de riesgo académico

---

## 🐳 Despliegue con Docker

```bash
# Construir y ejecutar contenedores
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

La aplicación estará disponible en `http://localhost:85`

---

## 📖 Uso del Sistema

### Para Tutores

1. **Iniciar sesión** con credenciales de tutor
2. Ver **dashboard** con resumen de estudiantes asignados
3. Acceder a **"Mis Estudiantes"** para ver listado completo
4. Hacer clic en un estudiante para ver su **ficha detallada**
5. Agregar **observaciones** en la bitácora de seguimiento
6. Gestionar **tutorías** desde el menú "Gestión Académica"
7. **Descargar PDF** de la ficha del estudiante

### Para Encargados de Carrera

1. Acceder al **dashboard global** con vista de todas las carreras
2. Aplicar **filtros** por carrera, estado de riesgo y fechas
3. Revisar **bitácoras** de todos los estudiantes
4. Exportar **reportes** en PDF
5. Monitorear **estadísticas** y métricas del programa

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. Commit tus cambios (`git commit -m 'feat: Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/NuevaFuncionalidad`)
5. Abre un Pull Request

---

## 📝 Comandos de Gestión Personalizados

```bash
# Poblar base de datos con datos de prueba
python manage.py poblar_bd

# Exportar datos de estudiantes
python manage.py exportar_estudiantes

# Limpiar registros antiguos
python manage.py limpiar_bitacoras --dias 365
```

---

## 🔮 Próximas Funcionalidades

- [ ] Notificaciones por email a tutores
- [ ] Dashboard de métricas avanzado
- [ ] Integración con sistemas académicos UBB
- [ ] Análisis predictivo con Machine Learning

---

## 🐛 Reporte de Bugs

Si encuentras algún bug, por favor [abre un issue](https://github.com/Mastrick7even/Sistema-de-alerta-temprana-para-programa-de-tutores-UBB/issues) con:

- Descripción detallada del problema
- Pasos para reproducir
- Navegador y versión
- Capturas de pantalla (si aplica)

---

## 👨‍💻 Autor

**Bastián Arriagada Quero**
- GitHub: [@Mastrick7even](https://github.com/Mastrick7even)

---

## 📄 Licencia

Este proyecto es parte de una tesis de titulación para la Universidad del Bío-Bío.

---

## 🙏 Agradecimientos

- **Creative Tim** - Por el template Argon Dashboard
- **AppSeed** - Por la base de Django boilerplate
- **Programa de Tutores UBB** - Por la colaboración y retroalimentación

---

## 📞 Contacto

Para consultas sobre el proyecto:
- Email: [bastian.arriagada2201@alumnos.ubiobio.cl]

---

<div align="center">
  
**[⬆ Volver arriba](#sistema-de-alerta-temprana---programa-de-tutores-ubb)**

</div>
