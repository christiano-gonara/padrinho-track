from datetime import date
from pathlib import Path
import io
import os
import re
import subprocess
import tempfile
import unicodedata
import zipfile

from flask import render_template

from database import DB_PATH
from models import contar_reunioes, get_padrinho, get_todos_padrinhos
from repositories import calouro_repository
from services.status_service import calcular_todos_status


MULHERES_MADRINHAS = {
    "alexia andrade",
    "amanda bicalho silva",
    "anny victorya azevedo oliveira",
    "karen joilly araujo",
    "laura noronha lara",
    "rayssa pierre da silva ramiro",
}


def _normalizar_nome(nome):
    return unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode("ascii").lower().strip()


def _slug_semestre(semestre):
    return re.sub(r"[^A-Za-z0-9-]+", "-", str(semestre).replace("/", "-")).strip("-") or "Semestre"


def _nome_curto_arquivo(nome):
    nome_ascii = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode("ascii")
    partes = [p for p in re.split(r"\s+", nome_ascii.strip()) if p]
    if not partes:
        return "Padrinho"
    if len(partes) == 1:
        selecionadas = partes
    else:
        selecionadas = [partes[0], partes[-1]]
    return re.sub(r"[^A-Za-z0-9_-]+", "_", "_".join(selecionadas)).strip("_") or "Padrinho"


def _funcao_certificado(padrinho):
    """Define o termo exibido no certificado conforme gênero/nome conhecido."""
    genero = (padrinho["genero"] or "").upper() if "genero" in padrinho.keys() else ""
    if genero == "F" or _normalizar_nome(padrinho["nome"]) in MULHERES_MADRINHAS:
        return {"titulo": "Madrinha", "texto": "madrinha"}
    return {"titulo": "Padrinho", "texto": "padrinho"}


def listar_coordenacao_certificados(config):
    """Lista pessoas da coordenação que recebem certificado próprio."""
    nomes = []
    if config.get("coordenadora_geral"):
        nomes.append(config["coordenadora_geral"])
    nomes.extend(config.get("coordenadores") or [])

    vistos = set()
    coordenacao = []
    for nome in nomes:
        nome = (nome or "").strip()
        normalizado = _normalizar_nome(nome)
        if not nome or normalizado in vistos:
            continue
        vistos.add(normalizado)
        coordenacao.append({"nome": nome, "tipo": "coordenacao"})
    return coordenacao


def _funcao_certificado_coordenacao():
    return {"titulo": "Coordenação", "texto": "coordenador(a)"}


def _contexto_base_certificado(pessoa, total_padrinhos, total_calouros, config, funcao, horas_acg):
    return {
        "padrinho": pessoa,
        "total_padrinhos": total_padrinhos,
        "total_calouros": total_calouros,
        "semestre": config["semestre"],
        "config": config,
        "hoje": date.today(),
        "funcao_certificado": funcao,
        "horas_acg": horas_acg,
    }


def montar_contexto_certificado(padrinho_id, config):
    """Valida aptidão e monta os dados do certificado individual de padrinho."""
    padrinho = get_padrinho(padrinho_id)
    if not padrinho:
        return None, "Padrinho não encontrado.", 404

    limite = contar_reunioes()
    todos_status = calcular_todos_status([padrinho_id], limite)
    status = todos_status.get(padrinho_id, {"status": "apto"})["status"]
    if status not in ("apto", "alerta"):
        return None, "Este padrinho não está apto para receber certificado.", 403

    total_padrinhos = len(get_todos_padrinhos())
    total_calouros = calouro_repository.contar_todos()

    return _contexto_base_certificado(
        padrinho,
        total_padrinhos,
        total_calouros,
        config,
        _funcao_certificado(padrinho),
        4,
    ), None, None


def montar_contexto_certificado_coordenacao(indice, config):
    """Monta os dados do certificado individual de coordenação."""
    coordenacao = listar_coordenacao_certificados(config)
    if indice < 0 or indice >= len(coordenacao):
        return None, "Coordenador(a) não encontrado(a).", 404

    total_padrinhos = len(get_todos_padrinhos())
    total_calouros = calouro_repository.contar_todos()
    return _contexto_base_certificado(
        coordenacao[indice],
        total_padrinhos,
        total_calouros,
        config,
        _funcao_certificado_coordenacao(),
        5,
    ), None, None


def obter_zip_certificados(config, regenerar=False):
    """Retorna o ZIP cacheado dos certificados ou gera os PDFs quando necessário."""
    padrinhos = get_todos_padrinhos()
    limite = contar_reunioes()
    todos_status = calcular_todos_status([p["id"] for p in padrinhos], limite)
    aptos = [
        p for p in padrinhos
        if todos_status.get(p["id"], {"status": "apto"})["status"] in ("apto", "alerta")
    ]

    total_calouros = calouro_repository.contar_todos()
    total_padrinhos = len(padrinhos)

    semestre_slug = _slug_semestre(config["semestre"])
    cache_dir = Path("instance") / "certificados"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"Padrinho_{semestre_slug}_Certificados.zip"
    download_name = cache_path.name

    fontes_cache = [
        Path(DB_PATH),
        Path("config_semestre.json"),
        Path("templates") / "pages" / "certificado.html",
        Path(__file__),
    ]
    if cache_path.exists() and not regenerar:
        cache_mtime = cache_path.stat().st_mtime
        cache_atual = all(not fonte.exists() or fonte.stat().st_mtime <= cache_mtime for fonte in fontes_cache)
        if cache_atual:
            return cache_path, download_name

    browser_path = _encontrar_navegador_pdf()
    if not browser_path:
        raise RuntimeError("Nenhum Chrome/Edge encontrado para gerar PDFs dos certificados.")

    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in aptos:
                nome_limpo = _nome_curto_arquivo(p["nome"])
                pdf_bytes = _gerar_certificado_pdf(
                    p,
                    tmpdir,
                    browser_path,
                    total_padrinhos,
                    total_calouros,
                    config,
                )
                zf.writestr(f"padrinhos/Certificado_{semestre_slug}_{nome_limpo}.pdf", pdf_bytes)
            for pessoa in listar_coordenacao_certificados(config):
                nome_limpo = _nome_curto_arquivo(pessoa["nome"])
                pdf_bytes = _gerar_certificado_pdf(
                    pessoa,
                    tmpdir,
                    browser_path,
                    total_padrinhos,
                    total_calouros,
                    config,
                    funcao_certificado=_funcao_certificado_coordenacao(),
                    horas_acg=5,
                    prefixo="coordenacao",
                )
                zf.writestr(f"coordenacao/Certificado_Coordenacao_{semestre_slug}_{nome_limpo}.pdf", pdf_bytes)
            zf.writestr(
                "LEIA-ME.txt",
                "Certificados do Programa de Apadrinhamento em PDF.\n"
                "A pasta padrinhos contém certificados de 4 horas.\n"
                "A pasta coordenacao contém certificados de 5 horas.\n"
                "Os PDFs foram gerados a partir do mesmo HTML do certificado individual do sistema.\n",
            )

    buffer.seek(0)
    cache_path.write_bytes(buffer.getvalue())
    return cache_path, download_name


def _encontrar_navegador_pdf():
    """Procura Chrome/Edge local para imprimir o HTML dos certificados em PDF."""
    candidates = [
        os.environ.get("PDF_BROWSER_PATH", ""),
        str(Path(os.environ.get("ProgramFiles", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
        str(Path(os.environ.get("ProgramFiles(x86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
        str(Path(os.environ.get("ProgramFiles", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
        str(Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _gerar_certificado_pdf(
    padrinho,
    tmpdir,
    browser_path,
    total_padrinhos,
    total_calouros,
    config,
    funcao_certificado=None,
    horas_acg=4,
    prefixo="certificado",
):
    """Renderiza um certificado HTML temporário e converte esse arquivo para PDF."""
    html = render_template(
        "pages/certificado.html",
        padrinho=padrinho,
        total_padrinhos=total_padrinhos,
        total_calouros=total_calouros,
        semestre=config["semestre"],
        config=config,
        hoje=date.today(),
        funcao_certificado=funcao_certificado or _funcao_certificado(padrinho),
        horas_acg=horas_acg,
    )
    icones_path = Path("static") / "images" / "certificado_icones.png"
    if icones_path.exists():
        html = html.replace('src="/static/images/certificado_icones.png"', f'src="{icones_path.resolve().as_uri()}"')
    cert_id_raw = padrinho["id"] if "id" in padrinho.keys() else padrinho["nome"]
    cert_id = re.sub(r"[^A-Za-z0-9_-]+", "_", str(cert_id_raw)).strip("_")
    html_path = Path(tmpdir) / f"{prefixo}_{cert_id}.html"
    pdf_path = Path(tmpdir) / f"{prefixo}_{cert_id}.pdf"
    profile_path = Path(tmpdir) / f"profile_{prefixo}_{cert_id}"
    profile_path.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    args = [
        browser_path,
        "--headless=new",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-background-networking",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--user-data-dir={profile_path}",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    popen_kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(args, **popen_kwargs)
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            proc.kill()
        raise

    if proc.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Falha ao gerar PDF para {padrinho['nome']}.")

    return pdf_path.read_bytes()
