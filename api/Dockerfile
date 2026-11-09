FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client && rm -rf /var/lib/apt/lists/*
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/app.py .
# SSH local de laboratorio: la clave se genera al iniciar Hadoop y vive solo en el volumen Docker.
# No se copia ninguna clave privada dentro de esta imagen.
RUN mkdir -p /root/.ssh && \
    printf 'Host hadoop\n    HostName hadoop\n    User hadoop\n    IdentityFile /shared-ssh/id_ed25519\n    IdentitiesOnly yes\n    StrictHostKeyChecking accept-new\n' > /root/.ssh/config && \
    chmod 700 /root/.ssh && chmod 600 /root/.ssh/config
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
