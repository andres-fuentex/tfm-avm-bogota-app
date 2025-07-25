FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgdal-dev \
    libspatialindex-dev \
    libgeos-dev \
    libproj-dev \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Instalar Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la app
COPY . .

EXPOSE 8501

# Configurar Chromium para Kaleido (si es necesario)
ENV KALIEDO_BROWSER_PATH=/usr/bin/chromium

CMD ["streamlit", "run", "avm.py", "--server.port=8501", "--server.address=0.0.0.0"]

