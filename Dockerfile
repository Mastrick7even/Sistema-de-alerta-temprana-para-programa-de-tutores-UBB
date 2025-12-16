FROM python:3.9-slim

# 1. Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 2. Directorio de trabajo
WORKDIR /app

# 3. Instalar dependencias del SISTEMA (Necesario para Postgres y compilación)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Instalar dependencias de PYTHON
COPY requirements.txt /app/
RUN pip install --upgrade pip
# Instalamos gunicorn y whitenoise explícitamente por si faltan en requirements
RUN pip install gunicorn whitenoise dj-database-url psycopg2-binary
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el código
COPY . /app/

# 6. RECOLECTAR ESTÁTICOS (El paso mágico de WhiteNoise)
# Usamos una clave falsa temporal solo para que este comando corra sin .env
RUN SECRET_KEY=dummy python manage.py collectstatic --noinput

# 7. Comando de arranque (Quitamos el config file para hacerlo simple y directo)
# Exponemos en el puerto 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]

