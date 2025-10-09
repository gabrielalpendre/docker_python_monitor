FROM python:3.11-slim

WORKDIR /monitor

COPY app.py /monitor/

COPY requirements.txt /monitor/
COPY pages /monitor/pages/
COPY static /monitor/static/
COPY backend /monitor/backend/
COPY functions /monitor/functions/

RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release && \
    curl -fsSL https://get.docker.com | sh

RUN pip install --upgrade pip

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

EXPOSE 4005

CMD ["python", "app.py"]
