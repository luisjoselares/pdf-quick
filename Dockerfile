# Usamos la imagen completa de Python para evitar problemas de dependencias faltantes
FROM python:3.11-bullseye

# Evitar diálogos interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalación limpia de LibreOffice y fuentes Noto (compatibles con todo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-noto-extra \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando de inicio optimizado
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:$PORT --timeout 180 --workers 2"]
