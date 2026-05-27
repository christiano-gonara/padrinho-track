# Guia de Handoff — Padrinho Track

Guia para o próximo coordenador configurar o sistema para um novo semestre.

---

## Pré-requisitos

- Python 3.11+ instalado
- Acesso ao repositório GitHub
- Conta Google com acesso ao Google Cloud Console
- Banco de dados do semestre anterior (`instance/mentoria.db`) fornecido pelo coordenador anterior

---

## Passo 1 — Clonar o repositório

```bash
git clone https://github.com/christiano-gonara/padrinho-track.git
cd padrinho-track
pip install -r requirements.txt
```

---

## Passo 2 — Configurar credenciais Google Cloud

O sistema usa uma **service account** para leitura de planilhas (presenças, inscrições, importação de padrinhos e calouros).

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Selecione o projeto `padrinho-track` (ou crie um novo)
3. Em **IAM & Admin → Service Accounts**, localize `padrinho-track@padrinho-track.iam.gserviceaccount.com`
4. Clique em **Manage Keys → Add Key → Create new key → JSON**
5. Salve o arquivo baixado como `credentials.json` na raiz do projeto

> O `credentials.json` **nunca deve ser commitado** — já está no `.gitignore`.

---

## Passo 3 — Preencher `config_handoff.json`

Na raiz do projeto existe o arquivo `config_handoff.json`. Preencha com os links das planilhas do novo semestre:

```json
{
  "semestre": "2026/2",
  "google": {
    "planilha_presencas_url":  "URL da planilha vinculada ao Forms de presença",
    "planilha_inscricoes_url": "URL da planilha vinculada ao Forms de inscrição em temas",
    "forms_padrinhos_url":     "URL da planilha vinculada ao Forms de cadastro de padrinhos",
    "forms_calouros_url":      "URL da planilha vinculada ao Forms de cadastro de calouros"
  }
}
```

**Cada planilha precisa ser compartilhada com a service account:**
`padrinho-track@padrinho-track.iam.gserviceaccount.com` (papel: Editor)

> O `config_handoff.json` **nunca deve ser commitado** — já está no `.gitignore`.

---

## Passo 4 — Rodar o script de configuração

```bash
python scripts/setup_handoff.py
```

Saída esperada:
```
[OK] Sistema configurado para o novo semestre.
```

Isso grava os links das planilhas no banco de dados local (`instance/mentoria.db`).

---

## Passo 5 — Restaurar o banco do semestre anterior (opcional)

Se o coordenador anterior forneceu um backup do banco:

1. Copie o arquivo `mentoria.db` recebido para `instance/mentoria.db`
2. O banco já contém padrinhos, advertências e histórico do semestre anterior
3. Use a página **Início do Semestre** para importar os novos padrinhos e calouros

Se estiver começando do zero (banco novo):

```bash
python -c "from database import init_db; init_db()"
```

---

## Passo 6 — Configurar o semestre

Na interface web, acesse **Configurações** e atualize:

- Nome do semestre (ex: `2026/2`)
- Professor coordenador
- Datas de início e fim
- Coordenadores da monitoria

---

## Passo 7 — Variáveis de ambiente

Crie um arquivo `.env` na raiz:

```
APP_USERNAME=admin
APP_PASSWORD=senha_escolhida
SECRET_KEY=chave_aleatoria_longa
```

---

## Exportar backup do banco

A qualquer momento, acesse **Configurações → Exportar backup do banco** para baixar o `mentoria.db` atual. Faça isso antes de encerrar o semestre e envie ao próximo coordenador.

---

## Estrutura de arquivos sensíveis (nunca commitar)

| Arquivo | Conteúdo |
|---|---|
| `credentials.json` | Service account Google Cloud |
| `client_secrets.json` | OAuth2 Google Cloud |
| `config_semestre.json` | Configurações do semestre atual |
| `config_handoff.json` | Links e chaves do próximo semestre |
| `.env` | Usuário, senha e chave secreta |
| `instance/mentoria.db` | Banco de dados |
