"""Gera a apresentação estática em docs/site, para o GitHub Pages.

O Flask não roda no Pages: o que sobe é a página de apresentação já renderizada,
com os arquivos de static/ copiados ao lado. É a mesma landing do sistema, sem
duplicar HTML — quem muda o template muda o site.
"""

import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "docs" / "site"

# O app exige estas variáveis para subir; o build não usa banco nem login.
os.environ.setdefault("SECRET_KEY", "build-do-site")
os.environ.setdefault("APP_PASSWORD", "build-do-site")

sys.path.insert(0, str(RAIZ))

from flask import render_template  # noqa: E402
from app import app  # noqa: E402
from routes.publicas import REPOSITORIO  # noqa: E402


def main() -> int:
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir(parents=True)

    # Contexto de requisição porque o template usa url_for('static', ...).
    with app.test_request_context("/"):
        html = render_template(
            "pages/landing.html",
            estatico=True,
            repositorio=REPOSITORIO,
        )

    # Sem servidor Flask, os caminhos absolutos de /static não resolvem.
    html = html.replace('"/static/', '"static/').replace("'/static/", "'static/")
    (SAIDA / "index.html").write_text(html, encoding="utf-8")

    shutil.copytree(RAIZ / "static", SAIDA / "static")

    tamanho = sum(f.stat().st_size for f in SAIDA.rglob("*") if f.is_file())
    print(f"docs/site gerado: {len(list(SAIDA.rglob('*')))} arquivos, {tamanho / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
