# Padrinho Track

<div align="center">

![Padrinho Track](web/static/brand/padrinho-track-lockup.svg#gh-light-mode-only)
![Padrinho Track](web/static/brand/padrinho-track-lockup-dark.svg#gh-dark-mode-only)

**Sistema integrado para gestão do Programa de Apadrinhamento de Calouros**  
*PUC Minas — Engenharia de Software*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask_REST-1e40af?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-2563eb?logo=react&logoColor=white)](https://react.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![GitHub Pages](https://img.shields.io/badge/Landing_Page-GitHub_Pages-22c55e?logo=githubpages&logoColor=white)](https://christiano-gonara.github.io/padrinho-track/)
[![Test Suite](https://img.shields.io/badge/Tests-pytest-green?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[🌐 Ver Landing Page Online](https://christiano-gonara.github.io/padrinho-track/) • [📐 Documento de Arquitetura](docs/arquitetura.md) • [📋 Tarefas e Roadmap](docs/tarefas.md)

</div>

---

## 📌 Visão Geral

O **Padrinho Track** elimina o retrabalho e o risco de inconsistências causados por múltiplas planilhas desconexas na coordenação do programa de mentoria universitária.

O sistema centraliza em um único ambiente:
- **Inscrição e match inteligente** entre padrinhos/madrinhas veteranos e calouros por compatibilidade de turno e perfil.
- **Registro e acompanhamento de reuniões** periódicas e sincronização de presenças (Google Forms/Sheets ou lançamento direto).
- **Controle de temas e prazos** com atribuição de responsáveis individuais ou grupos.
- **Motor automático de regras de ACG e advertências** (sistema de cartões amarelos e vermelhos com histórico rastreável).
- **Emissão automática de relatórios finais** de aptidão e geração em lote de **certificados em PDF / ZIP** para alunos e coordenação.

---

## 🖼️ Capturas do Sistema

### Landing Page (Tema Claro · Azul Cobalto) e Cenários de Uso
![Landing Page Padrinho Track](docs/images/landing_page.png)

### Dashboard Interativo (Gráficos em Barras e Diagrama de Fluxo)
![Dashboard Padrinho Track](docs/images/dashboard.png)

### Tela de Relatórios e Fechamento ACG
![Tela de Relatório Padrinho Track](docs/images/relatorio_tela.png)

### Exemplos Reais em A4 (Relatório de Aptidão ACG e Certificado)
| Relatório de Aptidão ACG (A4) | Certificado de Participação (A4) |
|---|---|
| ![Relatório de Aptidão ACG](docs/images/relatorio_aptidao_a4.png) | ![Certificado de Participação](docs/images/certificado_a4.png) |

---

## 📐 Arquitetura do Sistema

O projeto adota uma arquitetura em camadas orientada a serviços e repositórios, desacoplando o protocolo de transporte HTTP da lógica de negócio e do acesso a dados.

```mermaid
graph TD
    subgraph Apresentacao["Camada de Apresentação & UI"]
        Landing["Landing Page (Estática no GitHub Pages ou Flask)"]
        Painel["Painel Administrativo Jinja2 + RemixIcon"]
    end

    subgraph Transporte["Rotas & Middlewares (Flask Blueprints)"]
        Auth["Controle de Sessão & Autenticação"]
        Routes["routes/ (dashboard, padrinhos, reunioes, match, temas, relatorios...)"]
    end

    subgraph Dominio["Serviços de Domínio (Business Logic)"]
        StatusSvc["status_service (Regras de Aptidão ACG)"]
        MatchSvc["match_service & match_algorithm (Afinidade de Turno/Perfil)"]
        CertSvc["certificado_service & relatorio_service (PDFs e ZIP)"]
    end

    subgraph Dados["Acesso a Dados (Repository Pattern)"]
        Repos["repositories/ (padrinho, calouro, reuniao, presenca, advertencia...)"]
        DB["database.py & database_schema.py"]
    end

    subgraph Persistencia["Armazenamento & Integrações"]
        SQLite[("SQLite Local (dev)")]
        Postgres[("PostgreSQL (prod)")]
        Sheets[("Google Sheets / Forms")]
    end

    Apresentacao --> Transporte
    Transporte --> Dominio
    Dominio --> Dados
    Dados --> DB
    DB --> SQLite
    DB --> Postgres
    Dominio --> Sheets
```

---

## 🔄 Ciclo de Vida Semestral

O fluxo do programa é estruturado em 4 etapas principais ao longo do semestre letivo:

```mermaid
flowchart LR
    E1["1. Inscrições & Importação\n(Google Sheets / Manual)"] --> E2["2. Match de Afinidade\n(Turno e Perfil)"]
    E2 --> E3["3. Acompanhamento Contínuo\n(Reuniões, Presenças & Temas)"]
    E3 --> E4["4. Fechamento de Semestre\n(Relatório ACG & Certificados ZIP)"]

    subgraph Advertencias["Motor de Regras Automático"]
        A1["Falta sem justificativa ➔ Amarelo"]
        A2["Atraso de tema ➔ Amarelo"]
        A3["Não entrega de tema ➔ Vermelho"]
        A4["2 Amarelos ou 1 Vermelho ➔ Inapto ACG"]
    end

    E3 -.-> Advertencias
    Advertencias -.-> E4
```

---

## 🗄️ Modelo de Dados (ERD)

```mermaid
erDiagram
    PADRINHOS ||--o{ MATCHES : "recebe"
    CALOUROS ||--o{ MATCHES : "atribuido a"
    PADRINHOS ||--o{ PRESENCAS : "possui"
    REUNIOES ||--o{ PRESENCAS : "contem"
    PADRINHOS ||--o{ TEMA_PADRINHOS : "responde por"
    TEMAS ||--o{ TEMA_PADRINHOS : "distribuido para"
    PADRINHOS ||--o{ ADVERTENCIAS : "acumula"

    PADRINHOS {
        int id PK
        string nome
        string matricula
        string email
        string turno
        boolean ativo
    }
    CALOUROS {
        int id PK
        string nome
        string telefone
        string turno
        int primeiro_periodo
    }
    MATCHES {
        int id PK
        int padrinho_id FK
        int calouro_id FK
    }
    REUNIOES {
        int id PK
        date data
        string tema
    }
    PRESENCAS {
        int id PK
        int reuniao_id FK
        int padrinho_id FK
        int presente
        int justificada
    }
    TEMAS {
        int id PK
        string titulo
        date data_limite
        string situacao
    }
    ADVERTENCIAS {
        int id PK
        int padrinho_id FK
        string tipo
        string origem
        string motivo
    }
```

---

## ⚖️ Regras de ACG e Advertências

| Situação | Cartão / Penalidade | Efeito no Status ACG |
|---|:---:|---|
| Todas as presenças confirmadas e temas entregues no prazo | — | **Apto para ACG** |
| 1 falta não justificada ou atraso leve de tema | 🟨 Amarelo | **Em Alerta** (aviso formal) |
| 2 advertências amarelas acumuladas | 🟨🟨 Amarelos | **Não Apto por Faltas** |
| Não entrega de tema no prazo estendido | 🟥 Vermelho | **Não Apto por Infração** |
| Falta em todas as reuniões do semestre | 🟥 Vermelho | **Não Apto** |
| Infração grave reportada pela coordenação (manual) | 🟥 Vermelho | **Reportado à Coordenação Geral** |

---

## 📂 Estrutura de Diretórios

```text
padrinho-track/
├── app.py                  # Ponto de entrada leve (compatível com gunicorn app:app)
├── backend/                # Camada de servidor, regras de negócio e dados
│   ├── app.py              # Factory da aplicação Flask e registro de Blueprints
│   ├── database.py         # Conexão híbrida SQLite / PostgreSQL
│   ├── database_schema.py  # DDL, constraints e migrações do banco
│   ├── models.py           # Camada de compatibilidade e utilitários
│   ├── routes/             # Blueprints modulares por domínio
│   ├── services/           # Lógica pura de negócio (status, match, relatórios, certificados)
│   ├── repositories/       # Consultas e persistência SQL isoladas
│   └── integrations/       # Integração com Google Sheets e CSVs
├── web/                    # Frontend React + TypeScript + Vite e templates de impressão
│   ├── src/                # Aplicação React + TypeScript (CSS separado por página/componente)
│   │   ├── pages/          # Landing Page, Dashboard (barras/fluxo), Padrinhos, Match, Relatórios...
│   │   ├── components/     # AppShell, gráficos em barras, diagrama de fluxo e seletor de cenários
│   │   ├── data/           # Cenários de uso interativos (Início, Em Andamento, Fechamento ACG)
│   │   ├── services/       # Cliente HTTP tipado para /api/*
│   │   └── styles/         # Design tokens (Azul Acadêmico/Cobalto em tema claro fixo)
│   ├── public/             # Identidade visual e ícones estáticos
│   ├── templates/          # Templates Jinja2 para relatórios A4 e certificados PDF
│   └── static/             # CSS e imagens para impressão A4/PDF
├── scripts/                # Gerador do GitHub Pages (build_site.py), seed e handoff
├── docs/                   # Documentação arquitetural e site gerado (docs/site/)
└── tests/                  # Suíte de testes automatizados com pytest
```

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório e preparar o ambiente

```bash
git clone https://github.com/christiano-gonara/padrinho-track.git
cd padrinho-track

# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e defina suas credenciais:

```bash
cp .env.example .env
```

Conteúdo mínimo do `.env`:
```env
APP_USERNAME=admin
APP_PASSWORD=sua_senha_aqui
SECRET_KEY=uma_chave_longa_e_segura

# Opcional (se não informado, utiliza SQLite local em instance/mentoria.db):
# DATABASE_URL=postgresql://user:pass@localhost:5432/padrinho_track
```

### 3. Executar o servidor de desenvolvimento

```bash
python app.py
```

Acesse:
- **Landing Page Pública**: `http://localhost:5000/`
- **Painel Administrativo**: `http://localhost:5000/dashboard` (requer login)

---

## 🧪 Testes Automatizados

A suíte de testes foi reformulada para ser **concisa, ágil e focada em valor de negócio**, cobrindo regras de status, algoritmo de match e segurança de rotas sem testes redundantes de biblioteca:

```bash
pytest -v
```

**Principais áreas validadas:**
- `tests/test_regras_negocio.py`: Progressão de status (apto, alerta, inapto), faltas justificadas, penalidades por atraso/falta de temas e idempotência.
- `tests/test_match.py`: Algoritmo de cruzamento padrinho-calouro com afinidade de turno e casos de borda.
- `tests/test_integracao.py`: Rota pública da landing page, controle estrito de autenticação nas rotas internas e endpoints principais.

---

## 🌐 Publicação Estática no GitHub Pages

O projeto conta com automação para publicar a landing page institucional via GitHub Pages:

- **Geração local**:
  ```bash
  python scripts/build_site.py
  ```
  Renderiza a página estática em `docs/site/index.html` com todos os assets copiados.
- **Automação CI/CD**: O workflow `.github/workflows/pages.yml` publica automaticamente a cada push na branch `main`.

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">
Desenvolvido por <strong>Christiano Gonçalves</strong> — Engenharia de Software, PUC Minas.
</div>
