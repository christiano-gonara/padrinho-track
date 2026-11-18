# Arquitetura do Sistema — Padrinho Track

Documento descritivo da arquitetura, fluxo de processos e modelagem de dados do **Padrinho Track**.

---

## 1. Visão Geral

O **Padrinho Track** adota uma arquitetura modular em camadas sobre **Python 3 / Flask**, separando estritamente a interface web, as rotas de transporte (Blueprints), a lógica de domínio do programa de apadrinhamento (Services) e a persistência de dados (Repositories).

```mermaid
graph TD
    subgraph Cliente["Navegador / Cliente"]
        UI["Templates Jinja2 + CSS Puro (RemixIcon / Google Fonts)"]
        Landing["Landing Page (Pública / GitHub Pages)"]
    end

    subgraph Web["Camada Web & Transporte (Flask)"]
        App["app.py (App Factory & Middlewares)"]
        BPs["routes/ (Blueprints Modulares: dashboard, padrinhos, reunioes, etc.)"]
    end

    subgraph Dominio["Camada de Negócio (Services)"]
        StatusSvc["status_service.py (Cálculo de Status ACG)"]
        MatchSvc["match_service.py / match_algorithm.py (Algoritmo de Compatibilidade)"]
        RelatorioSvc["relatorio_service.py (Resumos e Balanço)"]
        CertSvc["certificado_service.py (Certificados e ZIP)"]
        OutrosSvc["presenca_service, tema_service, padrinho_service, reuniao_service"]
    end

    subgraph Persistencia["Camada de Dados (Repositories)"]
        Repos["repositories/ (padrinho_repo, reuniao_repo, presenca_repo, advertencia_repo...)"]
        DB["database.py & database_schema.py"]
    end

    subgraph Armazenamento["Storage & Integrações"]
        SQLite["SQLite Local (instance/mentoria.db)"]
        Postgres["PostgreSQL Remoto (DATABASE_URL)"]
        GoogleSheets["Google Sheets / Forms (CSV/API)"]
    end

    UI --> App
    Landing --> App
    App --> BPs
    BPs --> Dominio
    Dominio --> Persistencia
    Persistencia --> DB
    DB --> SQLite
    DB --> Postgres
    Dominio --> GoogleSheets
```

---

## 2. Ciclo de Vida Semestral (Fluxo do Programa)

O ciclo de vida da mentoria é automatizado de ponta a ponta:

```mermaid
sequenceDiagram
    autonumber
    actor Coord as Coordenação
    participant Sis as Padrinho Track
    participant Match as Algoritmo de Match
    participant Regras as Engine de Regras (ACG)
    actor Padrinho as Padrinho / Calouro

    Coord->>Sis: 1. Configura semestre e importa inscrições (Google Sheets/Manual)
    Sis->>Match: 2. Executa cruzamento por turno e perfil
    Match-->>Sis: Matrizes de afinidade e distribuição de calouros
    Coord->>Sis: 3. Valida e exporta lista de contatos
    loop Reuniões e Temas ao longo do Semestre
        Padrinho-->>Coord: Participação e entregas
        Coord->>Sis: Lança presenças da reunião ou entrega de tema
        Sis->>Regras: Processa faltas não justificadas e atrasos
        Regras-->>Sis: Emite advertências amarelas ou vermelhas automaticamente
    end
    Coord->>Sis: 4. Solicita fechamento do semestre
    Sis->>Regras: Calcula aptidão final ao certificado
    Regras-->>Coord: Relatório de Aptidão ACG + Resumo Executivo
    Coord->>Sis: 5. Emite certificados individuais e baixa pacote ZIP
```

---

## 3. Modelo de Entidades e Relacionamentos (ERD)

A base de dados suporta tanto **SQLite** (ambiente de desenvolvimento) quanto **PostgreSQL** (produção via `DATABASE_URL`).

```mermaid
erDiagram
    PADRINHOS ||--o{ MATCHES : "recebe"
    CALOUROS ||--o{ MATCHES : "atribuido a"
    PADRINHOS ||--o{ PRESENCAS : "registra"
    REUNIOES ||--o{ PRESENCAS : "contem"
    PADRINHOS ||--o{ TEMA_PADRINHOS : "responde por"
    TEMAS ||--o{ TEMA_PADRINHOS : "distribuido para"
    PADRINHOS ||--o{ ADVERTENCIAS : "acumula"
    CONFIG_SEMESTRE ||--o{ LOGS : "audita"

    PADRINHOS {
        int id PK
        string nome
        string matricula
        string email
        string telefone
        string turno
        boolean ativo
        datetime criado_em
    }

    CALOUROS {
        int id PK
        string nome
        string telefone
        string turno
        string genero
        int primeiro_periodo
    }

    MATCHES {
        int id PK
        int padrinho_id FK
        int calouro_id FK
        datetime data_match
    }

    REUNIOES {
        int id PK
        date data
        string tema
        string descricao
    }

    PRESENCAS {
        int id PK
        int reuniao_id FK
        int padrinho_id FK
        int presente
        int justificada
        string motivo_justificativa
    }

    TEMAS {
        int id PK
        string titulo
        date data_aviso
        date data_limite
        string situacao
        date data_entrega
    }

    ADVERTENCIAS {
        int id PK
        int padrinho_id FK
        string tipo
        string origem
        string motivo
        date data
    }

    LOGS {
        int id PK
        string acao
        string detalhe
        datetime data_hora
    }
```

---

## 4. Estrutura de Diretórios e Responsabilidades

| Diretório / Arquivo | Responsabilidade |
|---|---|
| `app.py` | Fábrica de aplicação Flask, registro de Blueprints, filtros Jinja2 e controle de sessão global |
| `database.py` | Camada de conexão compatível com SQLite e PostgreSQL (com pools de conexão seguros) |
| `database_schema.py` | Definição de tabelas, índices e rotinas de migração de schema |
| `routes/` | Controladores HTTP desacoplados por módulo (dashboard, padrinhos, reunioes, match, etc.) |
| `services/` | Regras de negócio puras (cálculo de status ACG, algoritmo de match, geração de PDF) |
| `repositories/` | Consultas SQL isoladas por entidade, prevenindo SQL Injection e abstraindo queries |
| `integrations/` | Importadores e sincronizadores de Google Sheets e formulários externos |
| `templates/` | Templates Jinja divididos em `pages/` (telas completas) e `components/` (modais e cards) |
| `static/` | Folhas de estilo (`css/`), identidade visual (`brand/`) e screenshots (`capturas/`) |
| `scripts/` | Script estático do GitHub Pages (`build_site.py`), seeds de exemplo e utilitários |
| `tests/` | Suíte de testes concisa cobrindo regras de negócio, algoritmo de match e segurança de rotas |

---

## 5. Publicação Estática no GitHub Pages

Embora a aplicação de gestão seja dinâmica (Flask + banco de dados), a **Landing Page** de apresentação do programa de mentoria é construída automaticamente para o GitHub Pages através do script `scripts/build_site.py` e da action `.github/workflows/pages.yml`:

- Gera `docs/site/index.html` renderizando `templates/pages/landing.html` com caminhos estáticos.
- Copia os assets otimizados de `static/` (marcas, capturas, estilos).
- Publica no endereço: **`https://christiano-gonara.github.io/padrinho-track/`**.
