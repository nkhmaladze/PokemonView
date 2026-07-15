# Source: pattern synthesized from fly.io/docs/languages-and-frameworks/dockerfile/
# and github.com/fly-apps/hello-gunicorn-flask
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fallback only — fly.toml's [processes] block supplies the real
# per-process-type command ("web" vs "worker"); this CMD is never used
# once fly.toml defines [processes].
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "30", "wsgi:app"]
