# Padrinho Track

Sistema web interno para gestão do Programa de Apadrinhamento de Calouros da
PUC Minas, Engenharia de Software.

O projeto centraliza o acompanhamento de padrinhos/madrinhas, calouros,
reuniões, presenças, temas, advertências, relatórios finais e certificados ACG.

## Estado Atual

- Login simples por usuário e senha configurados no `.env`.
- Rotas modularizadas com Blueprints.
- Regras de negócio separadas em `services/`.
- Consultas principais isoladas em `repositories/`.
- `models.py` mantido apenas como fachada de compatibilidade.
- Banco local em SQLite e suporte a PostgreSQL via `DATABASE_URL`.
- Relatórios finais em HTML prontos para gerar PDF pelo navegador.
- Certificados individuais e ZIP com PDFs de padrinhos/madrinhas e coordenação.
- Testes automatizados com pytest.

## Funcionalidades

### Padrinhos, Calouros e Match

- Cadastro e edição de padrinhos/madrinhas.
- Cadastro e importação de calouros.
- Algoritmo de match por compatibilidade de turno e perfil.
- Lista de contatos entre padrinhos/madrinhas e calouros.
- Redistribuição de calouros ao remover um padrinho do programa.

### Reuniões e Presenças

- Cadastro de reuniões.
- Registro manual de presenças.
- Sincronização de presenças via Google Forms/Sheets.
- Advertência automática para falta sem justificativa.

### Temas

- Cadastro de temas e responsáveis.
- Sincronização de responsáveis via Google Sheets.
- Registro de entrega.
- Advertência automática por atraso ou não entrega.

### ACG, Relatórios e Certificados

- Relatório de aptidão ACG.
- Resumo final do semestre.
- Lista de contatos.
- Certificado individual de padrinho/madrinha.
- Certificado de coordenação.
- Download em ZIP com certificados em PDF.

## Regras de ACG

| Situação | Consequência |
|---|---|
| Sem advertência grave e dentro do limite de faltas | Apto para ACG |
| Uma advertência amarela antes do limite | Em alerta |
| Faltas em todas as reuniões | Não apto |
| Advertência vermelha | Reportado ao coordenador do programa |
| Não entrega de tema | Advertência vermelha |
| Entrega de tema com atraso relevante | Advertência conforme regra do sistema |

## Arquitetura

```text
padrinho-track/
├── app.py                    # Criação do Flask, login, dashboard e rotas gerais
├── database.py               # Conexão SQLite/PostgreSQL e inicialização
├── database_schema.py        # Schemas e migrações
├── models.py                 # Fachada temporária de compatibilidade
├── routes/                   # Blueprints por domínio
├── services/                 # Regras de negócio
├── repositories/             # Consultas e escrita no banco
├── integrations/             # Importações Google Sheets/CSV
├── templates/                # HTML do sistema e relatórios
├── static/                   # CSS, logos e imagens
├── scripts/                  # Seeds e scripts auxiliares
├── tests/                    # Testes automatizados
└── docs/                     # Tarefas e aprendizados
```

### Camadas

- `routes/`: recebem requisições HTTP e chamam services.
- `services/`: aplicam regras do programa.
- `repositories/`: concentram SQL.
- `integrations/`: conversam com Google Sheets, CSV e fontes externas.
- `templates/`: exibem dados; não devem conter regra pesada.

## Configuração Local

### 1. Criar ambiente e instalar dependências

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Criar `.env`

Use `.env.example` como base:

```env
APP_USERNAME=admin
APP_PASSWORD=troque_esta_senha
SECRET_KEY=uma_chave_longa_e_aleatoria

# Opcional: se definido, usa PostgreSQL em vez de SQLite local.
DATABASE_URL=

# Opcional: usado apenas nas funcionalidades que dependem de IA.
GEMINI_API_KEY=
```

### 3. Rodar o sistema

```bash
python app.py
```

Acesse:

```text
http://127.0.0.1:5000
```

## Dados Locais

Arquivos com dados reais ficam fora do Git:

```text
scripts/seed.py
scripts/seed_calouros.py
config_semestre.json
credentials.json
client_secrets.json
authorized_user.json
.env
instance/
```

Para popular o banco local com dados reais, mantenha os seeds localmente e rode:

```bash
python scripts/seed.py
python scripts/seed_calouros.py
```

## Testes

Rodar a suite completa:

```bash
pytest -q -p no:cacheprovider --basetemp=tmp_pytest_run tests
```

Estado atual:

```text
62 passed
```

## Produção

O projeto está preparado para Railway:

- `Procfile`
- `railway.json`
- suporte a `DATABASE_URL`
- `gunicorn` nas dependências

Antes de divulgar uma URL de produção:

- usar senha forte em `APP_PASSWORD`;
- usar `SECRET_KEY` forte;
- confirmar que `.env` e credenciais Google não foram versionados;
- testar geração de relatórios e ZIP de certificados;
- testar importações Google Sheets no ambiente de produção.

## Próximos Passos

As pendências estão em [docs/tarefas.md](docs/tarefas.md).

Prioridades atuais:

1. Revisar segredos e configuração de produção.
2. Testar PostgreSQL ponta a ponta.
3. Reduzir SQL restante em `integrations/importers.py`.
4. Criar entidades/dataclasses quando fizer sentido.
5. Melhorar responsividade de telas com tabelas grandes.
6. Ampliar testes para ZIP, PDF e login obrigatório.

## Observação Sobre Flutter

Flutter não reaproveita diretamente os templates HTML atuais. A abordagem mais
realista seria manter este backend Flask e criar, no futuro, um frontend Flutter
consumindo endpoints JSON. Relatórios, certificados, regras de ACG e importações
continuariam no backend Python.

## Autor

Christiano Gonçalves  
Engenharia de Software - PUC Minas
