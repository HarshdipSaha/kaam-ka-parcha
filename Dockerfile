FROM python:3.12-slim

# FFmpeg is required for audio normalisation and G.711 / AMR-NB degradation.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY data/real_world_samples ./data/real_world_samples
RUN pip install --no-cache-dir .

# Sessions live in memory, so run exactly one worker. Secrets come from the platform environment.
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK CMD python -c "import os,urllib.request as u;u.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health')"
CMD ["sh", "-c", "uvicorn parcha.app:app --host 0.0.0.0 --port ${PORT} --workers 1"]
