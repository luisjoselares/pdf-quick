# Usamos una imagen de Python oficial
FROM python:3.11-slim

# Evitar diálogos interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# 1. Habilitar componentes 'contrib' para las fuentes de Microsoft
# 2. Aceptar automáticamente la licencia de EULA para mscorefonts
# 3. Instalar LibreOffice y fuentes
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    sed -i 's/main/main contrib/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/main/main contrib/g' /etc/apt/sources.list && \
    echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    fonts-liberation \
    ttf-mscorefonts-installer \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requerimientos e instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto que usará Flask
EXPOSE 5000

# Comando para iniciar con Gunicorn usando el puerto de Render
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:$PORT --timeout 180"]
