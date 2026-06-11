FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    TZ=Europe/Madrid

# Hosts de confianza de PyPI para que la instalación de dependencias funcione
# de forma fiable en cualquier red.
ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org"

WORKDIR /app

# Dependencias primero (mejor cacheo de capas)
COPY requirements.txt .
RUN pip install --upgrade pip \
        --trusted-host pypi.org --trusted-host files.pythonhosted.org \
 && pip install -r requirements.txt \
        --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Codigo de la aplicacion
COPY app ./app

# Volumen para persistir la base de datos SQLite
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

# Healthcheck del endpoint de estado
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/status').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
