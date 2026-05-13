# Padrinho Track

> Sistema web interno para gestão do programa de mentoria acadêmica da PUC Minas — Engenharia de Software.

---

## Sobre o projeto

O **Padrinho Track** nasceu de uma necessidade real: o programa de mentoria da PUC Minas não tinha forma estruturada de registrar presenças, controlar entregas ou aplicar advertências. Tudo ficava disperso no WhatsApp e em planilhas manuais.

O sistema centraliza a gestão de **50 padrinhos** (veteranos voluntários) e **127 calouros**, automatizando as regras de advertência que definem quem está apto a receber horas ACG ao final do semestre. Foi desenvolvido do zero por um coordenador do próprio programa, a partir de uma necessidade real identificada durante o semestre.

---

## Funcionalidades

**Gestão de padrinhos e calouros**
- Cadastro de padrinhos com turno, email e telefone
- Match padrinho-calouro com histórico completo
- Histórico individual — presenças, temas e advertências

**Presenças e reuniões**
- Registro manual de presença por reunião
- Importação automática via CSV exportado do Google Forms
- Advertência amarela automática para faltas sem justificativa

**Temas informativos**
- Controle de entrega de temas em grupo (relação muitos-para-muitos)
- Advertência automática por atraso (1 dia → amarelo) ou não entrega (vermelho)
- Advertência manual com motivo livre para comportamentos inadequados

**Relatórios e aptidão ACG**
- Dashboard com visão geral — aptos, em alerta, inaptos
- Gráficos de distribuição de status e presenças por reunião
- Relatório geral exportável em CSV
- Relatórios separados: aptos (para emissão de ACG) e vermelhos (para reportar ao professor)
- Limite de amarelos configurável pela coordenação

**Interface**
- Sidebar colapsável com animação suave e link ativo destacado
- Dark mode com toggle e preferência salva no localStorage
- Busca em tempo real na lista de padrinhos
- Toast notifications nas ações

---

## Regras de advertência

| Situação | Cartão | Consequência |
|---|---|---|
| Falta sem justificativa em reunião | Amarelo | — |
| Entrega de tema com 1 dia de atraso | Amarelo | — |
| N amarelos acumulados (configurável) | — | Inapto para ACG |
| Não entrega de tema | Vermelho | Inapto para ACG + reportar professor |
| Comportamento inadequado (manual) | Vermelho | Inapto para ACG + reportar professor |

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
- **Frontend:** HTML + Tailwind CSS + Remix Icon
- **Testes:** pytest — 18 testes cobrindo regras de advertência e aptidão ACG
- **Dados:** Pandas — importação de CSV e exportação de relatórios

---

## Estrutura

```
padrinho-track/
├── app.py              # Flask: configuração e rotas
├── database.py         # Conexão e criação do banco SQLite
├── models.py           # Funções de leitura e escrita no banco
├── seed_exemplo.py     # Dados fictícios para demonstração
├── tests/              # Testes automatizados com pytest
├── templates/          # Páginas HTML com Tailwind
├── static/             # Arquivos estáticos
├── instance/           # Banco de dados local (não sobe pro Git)
├── docs/               # Screenshots para o README
├── requirements.txt
└── README.md
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

**3. Popule o banco com dados de exemplo**
```bash
python seed_exemplo.py
```

**4. Rode o servidor**
```bash
python app.py
```

**5. Acesse no navegador**
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

- [ ] Login com autenticação para coordenadores
- [ ] Deploy em nuvem com link público (Railway + PostgreSQL)
- [ ] Geração de PDF de aptidão para ACG
- [ ] Logs de auditoria — registro de quem alterou o quê
- [ ] Integração direta com Google Sheets API

---

## Autor

**Christiano Gonara**
Engenharia de Software — PUC Minas
[LinkedIn](https://linkedin.com/in/christiano-gonara) · [GitHub](https://github.com/christiano-gonara)