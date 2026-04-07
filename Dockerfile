FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./

RUN python -c "import pathlib, tomllib; deps = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['dependencies']; pathlib.Path('requirements-runtime.txt').write_text('\\n'.join(deps) + '\\n')"

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-runtime.txt

COPY README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN pip install --no-cache-dir --no-deps .

RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
