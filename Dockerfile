# Usamos una imagen oficial de Python
FROM python:3.10-slim

# Instalamos LibreOffice (el motor para convertir Word/Excel a PDF)
RUN apt-get update && apt-get install -y libreoffice

# Preparamos el entorno
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Exponemos el puerto de Streamlit
EXPOSE 8501

# Comando para arrancar tu app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
