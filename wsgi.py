"""gunicorn entrypoint for the Flask API (Plan 07-02).

This module exposes the module-level `app` object that gunicorn's
`wsgi:app` target resolves against
(`gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app`).

It is the single designated `create_app()` call site: `create_app()`
is invoked with no arguments, so it reads MONGODB_URI and CORS_ORIGINS
from the environment internally via its own existing defaults (see
`api/app.py`). This module adds no config reading, no logging, and no
other side effects beyond that one call.
"""

from api.app import create_app

app = create_app()
