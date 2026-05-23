# Tarefas

## Tarefa 0 — Desativar login temporariamente
No app.py comenta o bloco do before_request que verifica login:
# @app.before_request
# def require_login():
#     ...
Não apaga — só comenta. Quando for hospedar é só descomentar.

## Tarefa 1 — Ajustar convivência entre Tailwind e app.css
Tailwind fica responsável por layout e espaçamento. app.css fica responsável por componentes visuais. Onde houver conflito, app.css tem prioridade.

1. Nos componentes pt- do app.css que estiverem sendo sobrescritos pelo Tailwind, adiciona especificidade maior (ex: .pt-btn.pt-btn-primary em vez de .pt-btn-primary)
2. Garante que pt-metric-card, pt-card, pt-modal, pt-badge, pt-table, pt-nav-item estão com visual correto sem interferência do Tailwind
3. Não remove classes Tailwind de layout (flex, grid, gap, p-, m-, w-)
4. Testa visualmente: dashboard, padrinhos, relatório e configurações

## Tarefa 2 — Trocar Chart.js por ApexCharts no dashboard
1. Remove o script do Chart.js do dashboard.html
2. Adiciona ApexCharts via CDN: https://cdn.jsdelivr.net/npm/apexcharts
3. Recria o gráfico de pizza (donut):
   - Height: 200px
   - Total no centro do donut
   - Cores: #10b981, #f59e0b, #f97316, #dc2626
   - Labels: Aptos, Em alerta, Inaptos, Inaptos Graves
   - Legenda com número e percentual ao lado de cada item
4. Recria o gráfico de linha:
   - Height: 220px
   - Duas séries: Presentes (#7c5cff) e Ausentes (#dc2626)
   - Área preenchida com opacidade 0.1
   - Tooltips em português
5. Container dos gráficos com max-width: 900px

## Tarefa 3 — Corrigir layout do config.html
1. Campos do semestre em grid lado a lado:
   - Semestre + Instituição: 2 colunas
   - Professor Coordenador: largura total
   - Programa: largura total
   - Total de reuniões + Data início + Data fim: 3 colunas
2. Todas as 3 seções com max-width: 720px e margin: 0 auto
3. Inputs com class="pt-input", labels com class="pt-label", botões com class="pt-btn pt-btn-primary"

## Tarefa 4 — Padronizar largura das páginas
No app.css atualiza pt-content-padded para:
  .pt-content-padded {
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 40px;
  }
E aplica essa classe no container principal de todos os templates.

## Tarefa 5 — Truncar nomes longos
1. No models.py adiciona função abreviar_nome(nome):
   "Maria Luiza Aparecida Trindade de Meneses" → "Maria L. A. T. Meneses"
   Lógica: primeiro nome + iniciais dos nomes do meio + último sobrenome
2. Registra como filtro Jinja no app.py: app.jinja_env.filters['abreviar'] = abreviar_nome
3. Nos templates onde o nome aparece em espaço pequeno usa: {{ p.nome | abreviar }}
4. No detalhe do padrinho e em títulos mantém o nome completo

## Tarefa 6 — Corrigir gráfico de pizza
1. Legenda com número E percentual ao lado de cada item
2. Número do total no centro legível no dark mode — cor adaptativa
3. Cards de métricas: número sempre abaixo do label, tamanho consistente nos 4 cards

## Tarefa 7 — Corrigir dark mode nas tabelas
Garante que todas as tabelas têm texto legível no dark mode:
- Texto principal: rgba(255,255,255,0.9)
- Texto secundário: rgba(255,255,255,0.55)
- Bordas: rgba(255,255,255,0.08)
- Fundo hover: rgba(255,255,255,0.04)

## Tarefa 8 — Simplificar relatórios
1. Remove páginas relatorio_aptos.html e relatorio_vermelhos.html
2. Transforma as rotas em endpoints que retornam PDF direto
3. No relatorio.html adiciona 3 botões:
   - [PDF Aptidão ACG]
   - [PDF Resumo do semestre]
   - [PDF Inaptos Graves]
4. Remove links do menu lateral que apontavam pras páginas removidas

## Tarefa 9 — Relatório 1: PDF Aptidão ACG
Refatora o PDF existente para incluir:
1. Logo padrinho-track-lockup no cabeçalho
2. Dados do config_semestre.json: programa, semestre, professor coordenador
3. Resumo: total inscritos, aptos, inaptos
4. Tabela de aptos: nome completo, matrícula, turno, presenças/total reuniões
5. Visual com cores do design system
6. Rodapé com campo de assinatura e "Gerado pelo Padrinho Track · PUC Minas"

## Tarefa 10 — Relatório 2: PDF Resumo do semestre
Cria novo PDF com:
1. Cabeçalho com logo e dados do config_semestre.json
2. Resumo geral: total padrinhos, calouros, reuniões realizadas
3. Cronograma de temas: título, data, responsáveis, situação de entrega
4. Resultado final: aptos X / inaptos Y / inaptos graves Z
5. Mesmo visual do design system

## Tarefa 11 — Relatório 3: PDF Inaptos graves
Cria novo PDF com:
1. Cabeçalho formal com logo e dados do config_semestre.json
2. Tabela: nome completo, matrícula, email, motivo, data da advertência
3. Total de casos
4. Campo para assinatura do coordenador
5. Visual em vermelho escuro #991b1b

## Tarefa 12 — Reorganizar templates em pastas
1. Cria templates/pages/ e move todos os HTMLs principais:
   - dashboard.html → templates/pages/dashboard.html
   - padrinhos.html → templates/pages/padrinhos.html
   - padrinho_detalhe.html → templates/pages/padrinho_detalhe.html
   - reunioes.html → templates/pages/reunioes.html
   - presencas.html → templates/pages/presencas.html
   - temas.html → templates/pages/temas.html
   - calouros.html → templates/pages/calouros.html
   - advertencias.html → templates/pages/advertencias.html
   - relatorio.html → templates/pages/relatorio.html
   - importar_presencas.html → templates/pages/importar_presencas.html
   - logs.html → templates/pages/logs.html
   - config.html → templates/pages/config.html
   - login.html → templates/pages/login.html
2. base.html e components/ ficam em templates/ mesmo
3. Atualiza todos os render_template no app.py para "pages/nome.html"

## Tarefa 13 — Bot do Telegram (futuro)
Cria bot.py com python-telegram-bot integrado ao banco SQLite:
- /status — resumo de aptos/alertas/inaptos
- /faltas — lista de faltas da última reunião
- /alerta — padrinhos com 1 amarelo + telefone
- /pdf — gera e envia PDF de aptidão no chat

Mantém os 18 testes passando. Confirme cada tarefa antes de prosseguir.