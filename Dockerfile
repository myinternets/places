FROM ubuntu:mantic

ENV DEBIAN_FRONTEND=noninteractive
COPY . /app
WORKDIR /app

EXPOSE 8080
EXPOSE 6333

RUN bash docker/install.sh
RUN mkdir -p /app/logs
RUN mkdir -p /app/share

CMD ["/app/bin/supervisord", "-c", "/app/docker/supervisord.conf"]
