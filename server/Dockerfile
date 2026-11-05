FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SICHOSANA_DB_PATH=/data/sichosana.sqlite3
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt && groupadd -r sichosana && useradd -r -g sichosana -u 10001 sichosana && mkdir -p /data && chown -R sichosana:sichosana /data
COPY server/ /app/server/
COPY static/ /app/static/
RUN chown -R sichosana:sichosana /app
USER sichosana
VOLUME ["/data"]
EXPOSE 8765
CMD ["uvicorn","server.app:app","--host","0.0.0.0","--port","8765","--proxy-headers"]
