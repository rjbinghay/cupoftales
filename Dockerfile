# Stage 1 — build Tailwind CSS
FROM node:20-alpine AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY static/css/input.css ./static/css/
COPY stories/templates/ ./stories/templates/
COPY users/templates/ ./users/templates/
RUN npm run build

# Stage 2 — Python runtime
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /build/static/css/main.css ./static/css/main.css

# Collect static files into /app/staticfiles/
RUN DJANGO_SECRET_KEY=build-dummy \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# Data directory for the SQLite volume mount
RUN mkdir -p data

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
