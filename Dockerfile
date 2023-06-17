FROM alpine:latest
MAINTAINER colethedj <colethedj@protonmail.com>

ENV PYTHONUNBUFFERED=1
COPY update.py requirements.txt yt_dlp_plugins /src/
COPY docker/ /src/docker

RUN addgroup -S -g 1000 pl-updater && adduser -S -G pl-updater -u 1000 pl-updater && \
    apk update && \
    apk add \
            python3 \
            python3-dev \
            py-pip \
            git \
            gcc \
            g++ \
            musl-dev \
            ca-certificates \
            su-exec && \
    pip3 install git+https://github.com/yt-dlp/yt-dlp.git && \
    yt-dlp --version && \
    pip3 install -r /src/requirements.txt && \
    rm -rf /var/cache/apk/* /tmp/* && \
    ls /src/docker && \
    chmod +x /src/docker/init /src/docker/run.sh

ENTRYPOINT ["/src/docker/init"]