"""Request-scoped DB handle accessor for the Flask app factory
(api/app.py, Plan 05-06).

No top-level side effects on import: no MongoClient construction, no
os.environ read. `get_db()` only reads the handle `create_app` already
stored on `app.config["DB"]` at factory time (Pattern 1,
05-RESEARCH.md) — it never opens a connection itself.
"""

from flask import current_app


def get_db():
    """Return the pymongo Database handle for the current app context.

    Returns:
        The pymongo Database instance `create_app` stored on
        `app.config["DB"]`.
    """
    return current_app.config["DB"]
