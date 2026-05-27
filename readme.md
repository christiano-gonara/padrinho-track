# Padrinho Track

> Sistema web interno para gestão do programa de mentoria acadêmica da PUC Minas — Engenharia de Software.

---

## Sobre o projeto

O **Padrinho Track** nasceu de uma necessidade real: o programa de mentoria da PUC Minas não tinha forma estruturada de registrar presenças, controlar entregas ou aplicar advertências. Tudo ficava disperso no WhatsApp e em planilhas manuais.

O sistema centraliza a gestão de **50 padrinhos** (veteranos voluntários) e **127 calouros**, automatizando as regras de advertência que definem quem está aprovado para receber horas ACG ao final do semestre. Foi desenvolvido do zero por um coordenador do próprio programa, a partir de uma necessidade real identificada durante o semestre.

---

## Sobre o programa

**Programa de Mentoria Acadêmica — Engenharia de Software**
PUC Minas · Semestre 2026/1

- **Professor Coordenador:** Prof. Laerte Xavier
- **Coordenadora Geral:** Ana Santos
- **Coordenadores:** Christiano Gonçalves, Perciliana, Giovanna, Zaine, Luiz

---

## Funcionalidades

**Gestão de padrinhos e calouros**
- Cadastro de padrinhos com turno, email, telefone e dados demográficos
- Match padrinho-calouro com algoritmo de compatibilidade por turno e perfil
- Redistribuição de calouros ao remover padrinho do programa
- Histórico individual — presenças, temas e advertências

**Presenças e reuniões**
- Registro manual de presença por reunião
- Sincronização automática via Google Forms/Sheets
- Advertência automática para faltas sem justificativa

**Temas informativos**
- Controle de entrega de temas em grupo
- Advertência automática por atraso ou não entrega
- Advertência manual (amarela ou grave) para comportamentos inadequados

**Relatórios e aptidão ACG**
- Dashboard com visão geral — aprovados, em alerta, reprovados, reportados
- Gráficos de distribuição de status e presenças por reunião
- Relatório de Aptidão ACG — impressão via browser (Ctrl+P → PDF)
- Resumo do Semestre — impressão via browser
- Reportados ao Professor Coordenador — impressão via browser
- Lista de contatos padrinho-calouro — impressão via browser

**Interface**
- Design system próprio com identidade visual da marca
- Sidebar colapsável com animação suave
- Dark mode com toggle e preferência salva
- Busca em tempo real na lista de padrinhos
- Toast notifications nas ações
- Logs de auditoria de todas as ações

---

## Sistema de advertências

| Situação | Tipo | Consequência |
|---|---|---|
| Falta sem justificativa em reunião | Advertência | — |
| Atraso na entrega de tema (manual) | Advertência | — |
| Faltas em todas as reuniões do semestre | — | Reprovado para ACG |
| Não entrega de tema | Advertência Grave | Reprovado + reportar professor |
| Comportamento inadequado (manual) | Advertência Grave | Reprovado + reportar professor |

## Status dos padrinhos

| Status | Cor | Significado |
|---|---|---|
| **Aprovado** | 🟢 Verde | Elegível para receber horas ACG |
| **Em alerta** | 🟡 Âmbar | Próximo do limite de advertências |
| **Reprovado** | 🟠 Laranja | Limite atingido — sem ACG |
| **Reportado** | 🔴 Vermelho | Advertência grave — reportar ao professor |

---

## Stack

- **Backend:** Python + Flask
- **Banco de dados:** SQLite
- **Frontend:** HTML + Tailwind CSS + design system próprio (app.css)
- **Ícones:** Remix Icon
- **Gráficos:** ApexCharts
- **Testes:** pytest — 29 testes cobrindo regras de advertência, aptidão e idempotência
- **Integrações:** Google Sheets API (gspread) para sincronização de presenças

---

## Estrutura

```
padrinho-track/
├── app.py                  # Flask: configuração e rotas
├── database.py             # Conexão e criação do banco SQLite
├── models.py               # Funções de leitura e escrita no banco
├── config_semestre.json    # Configurações do semestre (gitignore)
├── credentials.json        # Service account Google Cloud (gitignore)
├── client_secrets.json     # OAuth2 Google Cloud (gitignore)
├── requirements.txt
├── README.md
├── tests/                  # Testes automatizados com pytest
├── templates/              # Páginas HTML
│   ├── base.html
│   ├── components/         # Modais reutilizáveis
│   └── pages/              # Páginas principais
├── static/
│   ├── css/app.css         # Design system completo
│   └── *.svg               # Logo e favicon
├── instance/               # Banco de dados local (gitignore)
├── scripts/
│   ├── seed_exemplo.py     # Dados fictícios para demonstração
│   ├── seed.py             # Seed com dados reais (gitignore)
│   ├── seed_calouros.py    # Seed de calouros reais (gitignore)
│   └── match.py            # Script standalone de match via CSV
└── docs/
    ├── CLAUDE.md           # Contexto do projeto para Claude Code
    ├── tarefas.md          # Tarefas pendentes
    └── APRENDIZADOS.md     # Lições aprendidas
```

---

## Como rodar

**1. Clone o repositório**
```bash
git clone https://github.com/christiano-gonara/padrinho-track.git
cd padrinho-track
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente**
```bash
cp .env.example .env
```
Edite `.env` com suas credenciais:
```env
APP_USERNAME=admin
APP_PASSWORD=sua_senha_aqui
SECRET_KEY=chave_secreta_longa_e_aleatoria
GEMINI_API_KEY=sua_chave_gemini
```

**4. Popule o banco com dados de exemplo**
```bash
python scripts/seed_exemplo.py
```

**5. Rode o servidor**
```bash
python app.py
```

**6. Acesse no navegador**
```
http://127.0.0.1:5000
```

O banco de dados é criado automaticamente na primeira execução dentro da pasta `instance/`.

**Rodar os testes**
```bash
python -m pytest tests/ -v
```

---

## Roadmap

- [x] Sistema de advertências automáticas
- [x] Sincronização de presenças via Google Forms/Sheets
- [x] Relatórios HTML para impressão/PDF via browser
- [x] Login com autenticação
- [x] Design system com identidade visual própria
- [x] Logs de auditoria
- [x] Match padrinho-calouro com algoritmo de compatibilidade
- [x] Dados demográficos e distribuição por turno
- [ ] Tela de início do semestre (importação via Forms)
- [ ] Deploy no Fly.io
- [ ] Bot do Telegram para a coordenação

---

## Autor

**Christiano Gonçalves**
Coordenador da Monitoria — Engenharia de Software · PUC Minas
[LinkedIn](https://linkedin.com/in/christiano-gonara) · [GitHub](https://github.com/christiano-gonara)