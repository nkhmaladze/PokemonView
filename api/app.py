"""Flask application factory (Plan 05-06).

`create_app()` builds the entire Phase-5 HTTP serving layer: it
constructs the single MongoClient lazily INSIDE the factory (never at
module import time), stores the resulting database handle on
`app.config["DB"]`, initializes Flask-CORS from an env-driven origins
list, disables debug-mode tracebacks, registers a global JSON error
handler (T-05-02), and registers the `products` blueprint
(api/blueprints/products.py).

No top-level side effects on import: no MongoClient construction, no
os.environ read, no Flask app construction, no blueprint import/
registration at module scope. `import api.app` performs no DB
connection and registers no routes — everything happens only when
`create_app()` is explicitly called (mirrors scripts/ebay_client.py's
"read env only inside a called function" discipline).
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException

from api.config import Config


def create_app(mongodb_uri=None, db_name=Config.DB_NAME):
    """Build and return the configured Flask application.

    Args:
        mongodb_uri: MongoDB connection string. When None, read from
            the MONGODB_URI environment variable (KeyError if unset —
            fail loudly rather than silently connecting nowhere). The
            URI is never logged or included in any response body
            (credential hygiene, T-05-06).
        db_name: Database name to select on the client. Defaults to
            Config.DB_NAME ("pokemonview").

    Returns:
        flask.Flask: The fully configured app, ready for
        `app.test_client()` or a WSGI server — MongoClient constructed,
        CORS initialized, DEBUG=False, global error handler and the
        products blueprint registered.
    """
    app = Flask(__name__)
    app.config["DEBUG"] = False

    uri = mongodb_uri or os.environ["MONGODB_URI"]
    client = MongoClient(uri)
    app.config["DB"] = client[db_name]
    app.config["DB_NAME"] = db_name

    CORS(
        app,
        resources={
            r"/products*": {
                "origins": os.environ.get("CORS_ORIGINS", Config.CORS_ORIGINS_DEV_DEFAULT)
            }
        },
    )

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Global JSON error handler (T-05-02).

        HTTPExceptions (explicit 400/404/etc. raised via abort() or
        route logic) pass through unchanged so their intended status
        code and body are preserved. Any other unhandled exception is
        converted to a generic 500 JSON body with NO stack trace or
        exception class name — DEBUG is always False, so Flask's
        debug traceback page never renders.
        """
        if isinstance(error, HTTPException):
            return error
        return jsonify({"error": "internal_error"}), 500

    from api.blueprints.products import products_bp

    app.register_blueprint(products_bp)

    return app
