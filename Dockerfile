# Usa la imagen base oficial de Python 3.10 en versión slim
FROM python:3.10-slim

# Instala las librerías del sistema necesarias para geopandas, shapely y gdal
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Define el directorio de trabajo en el contenedor
WORKDIR /app

# Copia todo lo que tienes en tu carpeta local al contenedor
COPY . .

# Actualiza pip y luego instala las dependencias del requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expone el puerto donde correrá la app (8501 es el de Streamlit)
EXPOSE 8501

# Comando para ejecutar tu aplicación Streamlit
CMD ["streamlit", "run", "avm.py", "--server.port=8501", "--server.address=0.0.0.0"]
