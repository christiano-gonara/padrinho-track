# Padrinho Track

<div align="center">

![Padrinho Track](static/brand/padrinho-track-lockup.svg#gh-light-mode-only)
![Padrinho Track](static/brand/padrinho-track-lockup-dark.svg#gh-dark-mode-only)

**Sistema integrado para gestão do Programa de Apadrinhamento de Calouros**  
*PUC Minas — Engenharia de Software*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.x-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
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
├── app.py                  # Factory da aplicação Flask e registro de Blueprints
├── database.py             # Conexão híbrida SQLite / PostgreSQL
├── database_schema.py      # DDL, constraints e migrações do banco
├── models.py               # Camada de compatibilidade e utilitários
├── routes/                 # Blueprints modulares por domínio
│   ├── publicas.py         # Landing page pública (sem necessidade de login)
│   ├── dashboard.py        # Painel central de métricas
│   ├── padrinhos.py        # Gestão e detalhamento de padrinhos
│   ├── calouros.py         # Cadastro e lista de calouros
│   ├── match.py            # Execução de match e listas de contatos
│   ├── reunioes.py         # Reuniões de alinhamento
│   ├── presencas.py        # Lançamento de presenças por reunião
│   ├── temas.py            # Temas periódicos e prazos de entrega
│   ├── advertencias.py     # Gestão e aplicação de advertências
│   ├── configuracoes.py    # Configurações do semestre letivo
│   ├── relatorios.py       # Relatórios de aptidão e certificados
│   └── inicio.py           # Wizard de início de semestre
├── services/               # Lógica pura de negócio (status, match, relatórios)
├── repositories/           # Consultas e persistência SQL isoladas
├── integrations/           # Integração com Google Sheets e CSVs
├── templates/              # Templates Jinja2 (pages/ e components/)
├── static/                 # Estilos CSS, identidade visual (brand/) e capturas
├── scripts/                # Script de build para GitHub Pages (build_site.py) e seeds
├── docs/                   # Documentação arquitetural detalhada e histórico
└── tests/                  # Suíte concisa de testes automatizados com pytest
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
