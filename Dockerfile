# Usa una imagen oficial de Python como base
FROM python:3.12-slim

# - apt-get update: Actualiza la lista de paquetes disponibles.
# - apt-get install -y ffmpeg: Instala ffmpeg. El -y confirma automáticamente.
# - rm -rf /var/lib/apt/lists/*: Limpia el caché para mantener la imagen pequeña.
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al contenedor
COPY . .

# Comando que se ejecutará cuando el contenedor se inicie
CMD ["python", "main.py"]