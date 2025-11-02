# Usa una imagen oficial de Python como base
FROM python:3.12-slim

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