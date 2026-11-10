FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SICHOSANA_WEB_ROOT=/app/static SICHOSANA_DATA_DIR=/data SICHOSANA_PORT=8080
WORKDIR /app
RUN groupadd --gid 10001 sichosana && useradd --uid 10001 --gid 10001 --no-create-home sichosana
COPY static/ /app/static/
COPY server/ /app/server/
RUN mkdir -p /data && chown -R 10001:10001 /data
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "from urllib.request import urlopen; assert urlopen('http://127.0.0.1:8080/api/health',timeout=3).status==200"
CMD ["python","-m","server.app"]
