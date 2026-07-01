FROM docker.m.daocloud.io/library/python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    LANG=C.UTF-8 \
    TZ=Asia/Shanghai \
    PORT=8000

RUN set -eux; \
    sed -i \
        -e 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
        -e 's|https://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
        -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
        -e 's|https://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
        /etc/apt/sources.list.d/debian.sources; \
    apt-get update -o Acquire::Retries=5; \
    apt-get install -y --no-install-recommends -o Acquire::Retries=5 \
        ffmpeg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        curl \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /opt/application

COPY setup.py setup.cfg README.rst /opt/application/
COPY zou /opt/application/zou
COPY run.sh /opt/application/run.sh

RUN pip install --no-cache-dir .

RUN mkdir -p /opt/application/previews /opt/application/tmp /opt/application/plugins

EXPOSE 8000

RUN chmod +x /opt/application/run.sh
CMD /opt/application/run.sh
