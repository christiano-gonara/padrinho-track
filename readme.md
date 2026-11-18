# Padrinho Track

<div align="center">

![Padrinho Track](web/static/brand/padrinho-track-lockup.svg#gh-light-mode-only)
![Padrinho Track](web/static/brand/padrinho-track-lockup-dark.svg#gh-dark-mode-only)

**Gestão do Programa de Apadrinhamento de Calouros**  
*Engenharia de Software — PUC Minas*

[![Python](https://img.shields.io/badge/Python-3.12%2B-1e40af?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask_REST-2563eb?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-2563eb?logo=react&logoColor=white)](https://react.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![GitHub Pages](https://img.shields.io/badge/Demo_Online-GitHub_Pages-10b981?logo=githubpages&logoColor=white)](https://christiano-gonara.github.io/padrinho-track/)

[Ver demonstração online](https://christiano-gonara.github.io/padrinho-track/) · [Arquitetura](docs/arquitetura.md) · [Guia de transição](docs/HANDOFF.md) · [Próximos passos](docs/tarefas.md)

</div>

---

## O que o sistema resolve

Coordenar o apadrinhamento em planilhas separadas dá trabalho e gera erro na hora de fechar o semestre. O **Padrinho Track** junta todo o processo em um só lugar:

- **Cadastro e match**: importa padrinhos e calouros (do Google Forms ou manual) e sugere os pares por turno e perfil.
- **Reuniões e presenças**: registra quem foi, quem justificou e quem faltou (manual, CSV ou Google Sheets).
- **Temas e prazos**: acompanha quem ficou responsável por cada tema e se entregou no prazo.
- **Regras de ACG automáticas**: calcula quem está apto, em alerta ou reprovado sem conferência manual.
- **Relatórios e certificados**: gera o Relatório de Aptidão ACG, o Resumo do Semestre e todos os certificados em PDF (com download em ZIP).

---

## Capturas do sistema

### Apresentação e cenários de uso (GitHub Pages)
![Landing Page Padrinho Track](docs/images/landing_page.png)

### Dashboard com gráficos em barras e diagrama do semestre
![Dashboard Padrinho Track](docs/images/dashboard.png)

### Relatório geral e emissão de certificados
![Tela de Relatório Padrinho Track](docs/images/relatorio_tela.png)

### Modelos em A4 prontos para impressão e PDF
| Relatório de Aptidão ACG | Certificado de Participação |
|---|---|
| ![Relatório de Aptidão ACG](docs/images/relatorio_aptidao_a4.png) | ![Certificado de Participação](docs/images/certificado_a4.png) |

---

## Como o semestre funciona

```mermaid
flowchart LR
    A["1. Importação\nPadrinhos e calouros"] --> B["2. Match\nCruzamento por turno e perfil"]
    B --> C["3. Acompanhamento\nReuniões, presenças e temas"]
    C --> D["4. Fechamento\nRelatório ACG e certificados PDF"]
```

| Situação do padrinho | Efeito no status ACG |
|---|---|
| Dentro do limite de faltas e sem ocorrência grave | **Apto para ACG** (certificado de 04h) |
| Chegou a 1 falta do limite (aviso preventivo) | **Em alerta** (ainda apto, com aviso) |
| Faltou em todas as reuniões sem justificativa | **Reprovado** (sem certificado) |
| Não entregou tema ou recebeu advertência vermelha | **Reportado ao professor coordenador** |

---

## Organização das pastas

```text
padrinho-track/
├── app.py              # Ponto de entrada do servidor (gunicorn app:app)
├── backend/            # API REST, regras de negócio e acesso ao banco
│   ├── app.py          # Montagem do Flask e autenticação
│   ├── database.py     # Conexão SQLite (local) / PostgreSQL (produção)
│   ├── routes/         # Rotas HTML de impressão e API JSON (/api/*)
│   ├── services/       # Regras de ACG, match, relatórios e certificados
│   ├── repositories/   # Consultas SQL isoladas por entidade
│   └── integrations/   # Leitura de planilhas Google Sheets e CSV
├── web/                # Interface React + TypeScript e templates A4
│   ├── src/            # Páginas, gráficos em barras, cenários de uso e CSS separado
│   ├── public/         # Logotipo e imagens estáticas
│   ├── templates/      # Templates A4 para PDF/impressão (relatórios e certificado)
│   └── static/         # Estilos e imagens para impressão A4
├── scripts/            # Build do GitHub Pages (build_site.py), seed e handoff
├── docs/               # Documentação e capturas de tela
└── tests/              # Testes automatizados com pytest
```

---

## Como rodar localmente

### 1. Backend (Python / Flask)

```bash
git clone https://github.com/christiano-gonara/padrinho-track.git
cd padrinho-track

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python app.py
```

Variáveis mínimas no `.env`:
```env
APP_USERNAME=admin
APP_PASSWORD=sua_senha_aqui
SECRET_KEY=uma_chave_segura
```

### 2. Frontend (React + TypeScript)

```bash
cd web
npm install
npm run dev
```

Acesse `http://localhost:5173` para usar o frontend React com proxy para a API Flask (`http://localhost:5000`).

### 3. Testes e build do GitHub Pages

```bash
# Testes automatizados (regras de ACG, match, rotas e API)
pytest -v

# Gerar site estático completo em docs/site/
npm run build --prefix web -- --mode pages
python scripts/build_site.py
```

---

Desenvolvido por **Christiano Gonçalves** — Engenharia de Software, PUC Minas.
