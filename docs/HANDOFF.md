# Guia de Transição — Padrinho Track

Passo a passo simples para o próximo coordenador preparar o sistema para um novo semestre.

---

## O que você precisa antes de começar

- Python 3.11+ e Node.js 20+ instalados
- Acesso ao repositório no GitHub
- Acesso à conta Google Cloud do projeto (para ler as planilhas do Forms)
- Arquivo de backup do semestre anterior (`instance/mentoria.db`), se quiser manter o histórico

---

## 1. Baixar o projeto e instalar dependências

```bash
git clone https://github.com/christiano-gonara/padrinho-track.git
cd padrinho-track

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

npm install --prefix web
```

---

## 2. Configurar as credenciais do Google Sheets

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) e selecione o projeto `padrinho-track`.
2. Em **IAM & Admin → Service Accounts**, abra `padrinho-track@padrinho-track.iam.gserviceaccount.com`.
3. Crie e baixe uma chave JSON e salve na raiz do projeto como `credentials.json` (esse arquivo é ignorado pelo Git).
4. Compartilhe as planilhas vinculadas aos formulários do novo semestre com esse mesmo e-mail (papel **Editor**).

> Dica: garanta no Google Forms que o campo de **e-mail institucional** dos padrinhos seja obrigatório, pois ele vai direto para o relatório de ACG.

---

## 3. Preencher links das planilhas (`config_handoff.json`)

Na raiz do projeto, crie ou preencha `config_handoff.json` (também ignorado pelo Git):

```json
{
  "semestre": "2026/2",
  "google": {
    "planilha_presencas_url": "URL da planilha de presença",
    "planilha_inscricoes_url": "URL da planilha de inscrição em temas",
    "forms_padrinhos_url": "URL da planilha de cadastro de padrinhos",
    "forms_calouros_url": "URL da planilha de cadastro de calouros"
  }
}
```

Depois rode:

```bash
python scripts/setup_handoff.py
```

---

## 4. Restaurar ou iniciar o banco de dados

- **Com backup do semestre anterior**: copie o arquivo recebido para `instance/mentoria.db`.
- **Começando do zero**:

```bash
python -c "from backend.database import init_db; init_db()"
```

---

## 5. Configurar senha de acesso (`.env`)

```env
APP_USERNAME=admin
APP_PASSWORD=senha_escolhida
SECRET_KEY=chave_aleatoria_longa
```

Ao entrar na interface web, abra **Configurações** para atualizar o nome do semestre (`2026/2`), professor coordenador, datas e equipe de monitoria.

---

## Exportar backup ao fim do semestre

Antes de passar a coordenação adiante, acesse **Configurações → Exportar backup (.db)** para baixar o `mentoria.db` atualizado.
