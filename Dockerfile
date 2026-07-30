FROM python:3.11-slim

# ==========================================================
# Working directory
# ==========================================================
WORKDIR /app

# ==========================================================
# System packages
# ==========================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre \
    wget \
    unzip \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# ==========================================================
# Apache JMeter
# ==========================================================
ENV JMETER_VERSION=5.6.3

ENV JMETER_HOME=/opt/jmeter

ENV JMETER_EXECUTABLE=${JMETER_HOME}/bin/jmeter

ENV PATH="${JMETER_HOME}/bin:${PATH}"

RUN wget -q https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt && \
    mv /opt/apache-jmeter-${JMETER_VERSION} ${JMETER_HOME} && \
    rm apache-jmeter-${JMETER_VERSION}.tgz && \
    chmod +x ${JMETER_HOME}/bin/jmeter

# ==========================================================
# Prism
# ==========================================================
RUN npm install -g @stoplight/prism-cli

ENV PRISM_PORT=4010

# ==========================================================
# Python
# ==========================================================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================================
# Application
# ==========================================================
COPY . .

# ==========================================================
# Working folders
# ==========================================================
RUN mkdir -p \
    uploads \
    generated \
    workspace \
    logs

# ==========================================================
# Environment
# ==========================================================
ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

ENV UPLOAD_DIR=/app/uploads

ENV GENERATED_DIR=/app/generated

ENV WORKSPACE_DIR=/app/workspace

ENV LOG_LEVEL=INFO

# ==========================================================
# FastAPI
# ==========================================================

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]