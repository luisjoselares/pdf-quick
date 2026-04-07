# Usamos una imagen oficial de Python ligera
FROM python:3.11-slim

# Instalamos LibreOffice y fuentes esenciales para que los Word/Excel no pierdan formato
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-core \
    fonts-liberation \
    fonts-mscorefonts-base \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo dentro del servidor
WORKDIR /app

# Copiamos primero los requerimientos para aprovechar la caché
COPY requirements.txt .

# Instalamos las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto de tu código
COPY . .

# Comando para encender el servidor con Gunicorn
CMD gunicorn main:app --bind 0.0.0.0:$PORT
