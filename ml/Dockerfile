# The price model as an HTTP service. Build from the ml/ folder with a trained artifact:
#   docker build --build-arg ARTIFACT=artifacts/<version> -t shotti-price .
#   docker run --rm -p 8000:8000 shotti-price
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# LightGBM needs the OpenMP runtime, which the slim image leaves out.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install ".[api]"

ARG ARTIFACT
RUN test -n "$ARTIFACT" || (echo "Pass --build-arg ARTIFACT=artifacts/<version>" >&2 && exit 1)
COPY ${ARTIFACT} /app/artifact
ENV SHOTTI_ARTIFACT=/app/artifact

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "shotti_ml.api:app", "--host", "0.0.0.0", "--port", "8000"]
