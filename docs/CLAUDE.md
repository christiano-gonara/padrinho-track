# Padrinho Track — Contexto do Projeto

## O que é
Sistema web interno de gestão do programa de mentoria acadêmica da PUC Minas — Engenharia de Software. Coordena 50 padrinhos (veteranos voluntários) e 127 calouros ao longo do semestre.

Desenvolvido por: Christiano Gonçalves — Coordenador da Monitoria
Professor Coordenador: Prof. Laerte Xavier
Coordenadora Geral: Ana Santos
Coordenadores: Christiano Gonçalves, Perciliana, Giovanna, Zaine, Luiz
Instituição: PUC Minas · Eng. de Software · 2026/1

## Stack
- Backend: Python + Flask
- Banco: SQLite (instance/mentoria.db)
- Frontend: HTML + Tailwind CSS + app.css (design system próprio) + Remix Icon
- Gráficos: ApexCharts
- Testes: pytest (18 testes em tests/)

## Estrutura
```
padrinho-track/
├── app.py                  — rotas Flask
├── database.py             — conexão e criação do banco
├── models.py               — funções de leitura/escrita
├── templates/
│   ├── base.html           — shell do sistema
│   ├── components/         — modais reutilizáveis
│   └── pages/              — páginas principais
├── static/
│   ├── css/app.css         — design system completo com classes pt-
│   └── *.svg               — logo e favicon
├── tests/                  — pytest
├── scripts/
│   ├── match.py            — script standalone de match via CSV
│   ├── seed_exemplo.py     — dados fictícios para demo
│   ├── seed.py             — seed com dados reais (gitignore)
│   └── seed_calouros.py    — seed de calouros reais (gitignore)
├── docs/
│   ├── CLAUDE.md           — este arquivo
│   ├── tarefas.md          — tarefas pendentes
│   ├── APRENDIZADOS.md     — lições aprendidas
│   └── images/             — screenshots para o README
├── config_semestre.json    — configurações do semestre (gitignore)
└── README.md
```

## Banco de dados — tabelas
- padrinhos (id, nome, matricula, email, telefone, turno, ativo)
- reunioes (id, data, tema, descricao)
- presencas (id, reuniao_id, padrinho_id, presente, justificada)
- temas (id, titulo, data_aviso, data_limite, data_entrega, situacao)
- tema_padrinhos (tema_id, padrinho_id)
- advertencias (id, padrinho_id, tipo, origem, motivo, data)
- calouros (id, nome, telefone)
- matches (id, padrinho_id, calouro_id)
- config (chave, valor) — inclui limite_amarelos
- logs (id, acao, descricao, data, ip)

## Regras de negócio
- Advertência amarela: falta sem justificativa em reunião ou atraso de 1 dia na entrega de tema
- Advertência grave (vermelha): não entrega de tema ou comportamento inadequado
- Limite de amarelos configurável (padrão 2) — salvo na tabela config
- Status calculado pelo calcular_status(padrinho_id) em models.py

## Nomenclatura de status (versão final)
- apto → **Aprovado** (verde #10b981)
- alerta → **Em alerta** (âmbar #f59e0b)
- inapto_amarelo → **Reprovado** (laranja #f97316)
- inapto_vermelho → **Reportado** (vermelho #dc2626)

## Nomenclatura de advertências
- tipo "amarelo" → exibe como **Advertência**
- tipo "vermelho" → exibe como **Advertência Grave**

## Design system (app.css)
Arquivo em static/css/app.css com prefixo pt-.
- Cor primária: #7c5cff · hover: #5b3df5
- Sidebar: #0f1424 (sempre escura)
- Fundo app: #f6f6fa
- Fontes: Inter + JetBrains Mono
- Classes principais: pt-card, pt-btn, pt-badge, pt-metric-card, pt-table, pt-modal, pt-nav-item

## config_semestre.json
```json
{
  "semestre": "2026/1",
  "professor_coordenador": "Prof. Laerte Xavier",
  "coordenadora_geral": "Ana Santos",
  "coordenadores": ["Christiano Gonçalves", "Perciliana", "Giovanna", "Zaine", "Luiz"],
  "cargo_coordenador": "Coordenadores da Monitoria",
  "programa": "Mentoria Acadêmica — Engenharia de Software",
  "instituicao": "PUC Minas",
  "total_reunioes": 3,
  "data_inicio": "2026-03-01",
  "data_fim": "2026-07-15"
}
```

## Status dos blocos
- ✅ Bloco 1 — pytest + seed de exemplo
- ✅ Bloco 2 — gráficos + toast + busca em tempo real
- ✅ Bloco 3 — CRUD + limite configurável + relatórios separados
- ✅ Bloco 4 — importação de presença via CSV
- ✅ Bloco 5 — login + refatoração + about + identidade visual
- ⏸️ Bloco 6 — deploy (pausado)
- ✅ Bloco 7 — logs + match + relatórios HTML (Jinja)
- ⬜ Bloco 8 — Bot Telegram

## Relatórios implementados
3 relatórios gerados como páginas HTML/Jinja — usuário imprime via Ctrl+P → Salvar como PDF.
Rotas: /relatorio/aptidao · /relatorio/resumo · /relatorio/reportados
1. Aptidão ACG — lista de aprovados para a secretaria
2. Resumo do semestre — cronograma de temas + resultado geral
3. Reportados — lista para entrega ao Prof. Laerte Xavier

## Integração Google Sheets — autenticação

### Leitura (sincronizar_presencas_sheets)
Usa **service account** (`credentials.json`). A conta de serviço só precisa de acesso de leitura à planilha compartilhada; não cria arquivos e portanto não consome cota de Drive.

### Criação de planilhas (gerar_planilha_temas e futura exportar_lista_contatos_sheets)
Usa **OAuth2** (`client_secrets.json`). Arquivos são criados no Drive do usuário autorizado (`pexy0000@gmail.com`), eliminando o erro 403 de cota da service account.

#### Como gerar o client_secrets.json
1. Acesse [Google Cloud Console](https://console.cloud.google.com/) → projeto `padrinho-track`
2. Menu → **APIs e serviços → Credenciais → Criar credenciais → ID do cliente OAuth**
3. Tipo de aplicativo: **App para computador** (Desktop app)
4. Baixe o JSON gerado e salve como `client_secrets.json` na raiz do projeto
5. Na primeira execução de `gerar_planilha_temas()`, o sistema abre o browser para autorização
6. Após autorizar, o token é salvo automaticamente em `~/.config/gspread/authorized_user.json`
7. Execuções seguintes usam o token salvo sem abrir o browser

`client_secrets.json` e `authorized_user.json` estão no `.gitignore` — nunca comitar.

## Importante
- Nunca quebrar os 18 testes existentes
- Manter dark mode em todos os templates
- Sidebar sempre escura (#0f1424) independente do tema
- Credenciais via .env (APP_USERNAME, APP_PASSWORD, SECRET_KEY)
- Login está comentado temporariamente no before_request — descomentar antes do deploy
- scripts/seed.py e scripts/seed_calouros.py estão no .gitignore (dados reais)
- config_semestre.json está no .gitignore (dados reais)
- Tailwind CDN convive com app.css — Tailwind para layout, app.css para componentes visuais

## Modo de operação — autonomia
Ao receber uma tarefa do docs/tarefas.md:

1. Leia o CLAUDE.md e o tarefas.md antes de começar
2. Execute a tarefa completa sem pedir confirmação no meio
3. Após cada alteração relevante, rode pytest e corrija eventuais falhas antes de continuar
4. Só conclua a tarefa quando todos os critérios estiverem satisfeitos:
   - Os 18 testes passando
   - Nenhum print() de debug no código
   - Dark mode preservado nos templates alterados
5. Avise quando terminar com um resumo do que foi feito

Se encontrar ambiguidade ou risco de quebrar algo crítico, pare e pergunte antes de agir.

## Idioma
Sempre responda em português do Brasil.