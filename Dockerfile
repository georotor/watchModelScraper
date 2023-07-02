FROM python:3.11.2-slim

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install --no-install-recommends -y \
     curl \
     iputils-ping \
     netcat \
     \
     && pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt \
     \
     && apt autoremove -y \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*

COPY src/ /opt/app/

RUN mkdir -p /opt/app/downloads

RUN groupadd -r watch && useradd -d /opt/app -r -g watch watch \
     && chown watch:watch -R /opt/app

USER watch

ENTRYPOINT ["python", "main.py"]
