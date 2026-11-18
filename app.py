"""Ponto de entrada da aplicação Flask (compatível com gunicorn app:app)."""

import os

from backend.app import app
from backend.database import init_db

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
