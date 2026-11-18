# Camada de Rotas (`routes/`)

Este diretório concentra todos os **Blueprints do Flask**, desacoplando os controladores HTTP da aplicação central (`app.py`).

---

## 🎯 Arquitetura e Responsabilidade

A camada de rotas é responsável exclusivamente por:
1. Receber requisições HTTP (`GET`, `POST`).
2. Validar parâmetros de entrada (formulários, query strings e paths).
3. Delegar a execução para a camada de **Services** ou consultas especializadas em **Repositories**.
4. Responder com a renderização de templates Jinja2 ou redirecionamentos (`302`).

Nenhuma regra pesada de negócio (ex: cálculo de faltas ou pontuação de match) deve residir nos controladores.

---

## 🧭 Mapeamento de Blueprints

| Arquivo | Prefixo / Rota Base | Responsabilidade |
|---|---|---|
| [`publicas.py`](publicas.py) | `/` | Landing page institucional pública (sem autenticação prévia) |
| [`dashboard.py`](dashboard.py) | `/dashboard` | Visão executiva com métricas globais do semestre |
| [`padrinhos.py`](padrinhos.py) | `/padrinhos` | Listagem, cadastro, edição e perfil individual com histórico |
| [`calouros.py`](calouros.py) | `/calouros` | Gestão de calouros e visualização de turmas |
| [`match.py`](match.py) | `/match` | Execução do algoritmo de match e lista de contatos cruzada |
| [`reunioes.py`](reunioes.py) | `/reunioes` | Agendamento e histórico de reuniões de alinhamento |
| [`presencas.py`](presencas.py) | `/presencas` | Lançamento de frequência e controle de faltas justificadas |
| [`temas.py`](temas.py) | `/temas` | Distribuição de tópicos de apresentação e controle de prazos |
| [`advertencias.py`](advertencias.py) | `/advertencias` | Visualização de ocorrências e aplicação de advertências manuais |
| [`configuracoes.py`](configuracoes.py) | `/config` | Parâmetros do semestre (limites de falta, coordenadores, datas) |
| [`relatorios.py`](relatorios.py) | `/relatorio` | Emissão de relatórios de aptidão ACG e download de certificados ZIP |
| [`inicio.py`](inicio.py) | `/inicio` | Assistente (wizard) para inicialização de novo período letivo |

---

## 🔒 Segurança e Autenticação

Todas as rotas (com exceção de `publicas.landing`, `/login` e `/static`) são protegidas pelo interceptor global `@app.before_request` definido em `app.py`. Tentativas de acesso não autenticado são redirecionadas automaticamente para `/login`.
