# Camada de Templates (`templates/`)

Interface web do **Padrinho Track** construída sobre o motor de templates **Jinja2** integrado ao Flask.

---

## 🎨 Organização Visual

```text
templates/
├── base.html              # Layout mestre (Sidebar, cabeçalho, scripts globais e tema)
├── components/            # Blocos reutilizáveis (modais, cards e parciais)
│   ├── metric_cards.html             # Cards de contadores do dashboard
│   ├── modal_advertencia_manual.html # Modal para registrar advertência grave
│   ├── modal_nova_reuniao.html       # Formulário rápido de reunião
│   ├── modal_novo_padrinho.html      # Cadastro simplificado de padrinho
│   └── modal_novo_tema.html          # Criação de tema e atribuição de grupo
└── pages/                 # Páginas completas renderizadas pelas rotas
    ├── landing.html       # Apresentação institucional (também publicada no Pages)
    ├── login.html         # Tela de autenticação por senha
    ├── dashboard.html     # Painel principal de indicadores
    ├── padrinhos.html     # Grid e tabela de padrinhos com status
    ├── padrinho_detalhe.html # Perfil individual com histórico completo
    ├── calouros.html      # Tabela de calouros
    ├── reunioes.html      # Cronograma de reuniões
    ├── presencas.html     # Lançamento de frequência
    ├── temas.html         # Quadro de temas e status de entregas
    ├── match.html         # Assistente de geração e revisão de matches
    ├── advertencias.html  # Painel de ocorrências e cartões
    ├── config.html        # Configurações do semestre
    ├── logs.html          # Trilha de auditoria
    ├── inicio_semestre.html # Wizard de inicialização
    ├── relatorio.html     # Balanço geral
    ├── relatorio_aptidao_acg.html # Relatório formatado para impressão/PDF de ACG
    └── relatorio_resumo_semestre.html # Resumo executivo da coordenação
```

---

## 🌗 Suporte a Tema Claro e Escuro (Dark Mode)

A interface utiliza **CSS Custom Properties** (variáveis CSS) padronizadas em `static/css/app.css`. A alternância é controlada no cliente via `data-theme="dark"` no elemento `<html>`, respeitando tanto a preferência do sistema operacional (`prefers-color-scheme`) quanto a escolha explícita salva em `localStorage`.
