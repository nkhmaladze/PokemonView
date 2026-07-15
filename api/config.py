"""Constant app-config defaults for the Flask app factory (api/app.py).

Only constant/default values live here (no os.environ read at module
import time) — env-driven values (MONGODB_URI, CORS_ORIGINS) are read
inside `create_app()`'s function body per the repo's "no top-level
side effects on import" discipline (mirrors scripts/ebay_client.py).
"""


class Config:
    """Default configuration constants for create_app().

    Attributes:
        DB_NAME: Default MongoDB database name when create_app() is
            called with no explicit db_name argument.
        DEBUG: Always False — Flask's debug-mode traceback pages must
            never be enabled (T-05-02, information-disclosure
            mitigation). The global @app.errorhandler(Exception) in
            api/app.py is the only surface for unhandled-error
            responses.
        CORS_ORIGINS_DEV_DEFAULT: The wildcard "*" origin value used
            ONLY when the CORS_ORIGINS environment variable is unset —
            documented as a LOCAL-DEV-ONLY default (T-05-03). In
            production, CORS_ORIGINS MUST be set to an explicit
            comma-separated list of allowed origins; the exact prod
            origin(s) are a Phase-7 deployment detail. This value is
            never used silently in place of a real env var — create_app
            always sources CORS_ORIGINS from os.environ, falling back
            to this constant only when the variable is absent.
    """

    DB_NAME = "pokemonview"
    DEBUG = False
    CORS_ORIGINS_DEV_DEFAULT = "*"
