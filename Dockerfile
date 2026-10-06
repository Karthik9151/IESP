FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app

COPY requirements-ml.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-ml.txt -r requirements-api.txt

COPY backend ./backend
COPY src ./src
COPY configs ./configs
COPY models ./models
COPY data ./data
COPY scripts ./scripts

ARG IESP_MODEL_OWNER=Karthik9151
ARG IESP_MODEL_REPO=IESP
ARG IESP_MODEL_RELEASE_TAG=models-v1
ENV IESP_MODEL_OWNER=$IESP_MODEL_OWNER
ENV IESP_MODEL_REPO=$IESP_MODEL_REPO
ENV IESP_MODEL_RELEASE_TAG=$IESP_MODEL_RELEASE_TAG

RUN useradd --create-home --shell /usr/sbin/nologin iesp && chown -R iesp:iesp /app
USER iesp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

ENTRYPOINT ["python", "scripts/bootstrap_models.py"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
