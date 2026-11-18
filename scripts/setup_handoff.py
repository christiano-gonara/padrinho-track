import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import set_config

config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config_handoff.json")

with open(config_path) as f:
    config = json.load(f)

set_config("sheets_presenca_url",   config["google"]["planilha_presencas_url"])
set_config("sheets_inscricoes_url", config["google"]["planilha_inscricoes_url"])
set_config("sheets_padrinhos_url",  config["google"]["forms_padrinhos_url"])
set_config("sheets_calouros_url",   config["google"]["forms_calouros_url"])
print("[OK] Sistema configurado para o novo semestre.")
