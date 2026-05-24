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
- Cadastro de padrinhos com turno, email e telefone
- Match padrinho-calouro com histórico completo
- Histórico individual — presenças, temas e advertências

**Presenças e reuniões**
- Registro manual de presença por reunião
- Importação automática via CSV exportado do Google Forms
- Advertência automática para faltas sem justificativa

**Temas informativos**
- Controle de entrega de temas em grupo
- Advertência automática por atraso ou não entrega
- Advertência manual para comportamentos inadequados

**Relatórios e aptidão ACG**
- Dashboard com visão geral — aprovados, em alerta, reprovados, reportados
- Gráficos de distribuição de status e presenças por reunião
- Relatório geral exportável em CSV
- Relatório de Aptidão ACG — HTML para impressão via browser (Ctrl+P → Salvar como PDF)
- Resumo do Semestre — HTML para impressão via browser
- Reportados ao Professor Coordenador — HTML para impressão via browser
- Limite de advertências configurável pela coordenação

**Interface**
- Design system próprio com identidade visual da marca
- Sidebar colapsável com animação suave
- Dark mode com toggle e preferência salva
- Busca em tempo real na lista de padrinhos
- Toast notifications nas ações

---

## Sistema de advertências

| Situação | Tipo | Consequência |
|---|---|---|
| Falta sem justificativa em reunião | Advertência | — |
| Entrega de tema com 1 dia de atraso | Advertência | — |
| N advertências acumuladas (configurável) | — | Reprovado para ACG |
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

## Telas

### Dashboard
![Dashboard](docs/images/dashboard.png)

### Padrinhos
![Padrinhos](docs/images/padrinhos.png)

### Reuniões
![Reuniões](docs/images/reunioes.png)

### Lançar presenças
![Presenças](docs/images/presencas.png)

### Temas
![Temas](docs/images/temas.png)

### Calouros
![Calouros](docs/images/calouros.png)

### Advertências
![Advertências](docs/images/advertencias.png)

### Detalhe do padrinho
![Detalhe](docs/images/padrinho_detalhe.png)

### Relatório geral — dark mode
![Relatório](docs/images/relatorio_dark.png)

### Modais

| Novo padrinho | Nova reunião | Novo tema | Advertência manual |
|---|---|---|---|
| ![](docs/images/modal_padrinho.png) | ![](docs/images/modal_reuniao.png) | ![](docs/images/modal_tema.png) | ![](docs/images/modal_advertencia.png) |

---

## Stack

- **Backend:** Python + Flask
- **Banco de dados:** SQLite
- **Frontend:** HTML + Tailwind CSS + design system próprio (app.css)
- **Ícones:** Remix Icon
- **Gráficos:** ApexCharts
- **Testes:** pytest — 29 testes cobrindo regras de advertência, aptidão e idempotência
- **Relatórios:** páginas HTML/Jinja impressas via browser (sem dependência externa)
- **PDF:** reportlab (mantido para uso interno, não exposto na interface)

---

## Estrutura

```
padrinho-track/
├── app.py                  # Flask: configuração e rotas
├── database.py             # Conexão e criação do banco SQLite
├── models.py               # Funções de leitura e escrita no banco
├── seed_exemplo.py         # Dados fictícios para demonstração
├── config_semestre.json    # Configurações do semestre (gitignore)
├── CLAUDE.md               # Contexto do projeto para Claude Code
├── APRENDIZADOS.md         # Lições aprendidas no desenvolvimento
├── tarefas.md              # Tarefas pendentes para Claude Code
├── tests/                  # Testes automatizados com pytest
├── templates/              # Páginas HTML
│   ├── base.html
│   ├── components/         # Modais reutilizáveis
│   └── pages/              # Páginas principais
├── static/
│   ├── css/app.css         # Design system completo
│   └── *.svg               # Logo e favicon
├── instance/               # Banco de dados local (gitignore)
├── docs/                   # Screenshots para o README
└── requirements.txt
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
```

**4. Popule o banco com dados de exemplo**
```bash
python seed_exemplo.py
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
- [x] Importação de presenças via CSV do Google Forms
- [x] Relatórios HTML para impressão/PDF via browser
- [x] Login com autenticação
- [x] Design system com identidade visual própria
- [x] Logs de auditoria
- [x] Interface de match padrinho-calouro
- [ ] Deploy em nuvem
- [ ] Bot do Telegram para a coordenação
- [ ] Integração com Google Sheets API

---

## Autor

**Christiano Gonçalves**
Coordenador da Monitoria — Engenharia de Software · PUC Minas
[LinkedIn](https://linkedin.com/in/christiano-gonara) · [GitHub](https://github.com/christiano-gonara)