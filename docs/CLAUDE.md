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
- Testes: pytest (29 testes em tests/)
- Google Sheets: gspread (service account para leitura, OAuth2 para criação)

## Estrutura
padrinho-track/
├── app.py                  — rotas Flask
├── database.py             — conexão e criação do banco
├── models.py               — funções de leitura/escrita
├── config_semestre.json    — configurações do semestre (gitignore)
├── credentials.json        — service account Google Cloud (gitignore)
├── client_secrets.json     — OAuth2 Google Cloud (gitignore)
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html           — shell do sistema
│   ├── components/         — modais reutilizáveis
│   └── pages/              — páginas principais
├── static/
│   ├── css/app.css         — design system completo com classes pt-
│   └── *.svg               — logo e favicon
├── tests/                  — pytest (29 testes)
├── scripts/
│   ├── match.py            — script standalone de match via CSV
│   ├── seed_exemplo.py     — dados fictícios para demo
│   ├── seed.py             — seed com dados reais (gitignore)
│   └── seed_calouros.py    — seed de calouros reais (gitignore)
└── docs/
    ├── CLAUDE.md           — este arquivo
    ├── tarefas.md          — tarefas pendentes
    └── APRENDIZADOS.md     — lições aprendidas

## Banco de dados — tabelas
- padrinhos (id, nome, matricula, email, telefone, turno, genero, idade, cidade_bh, prouni, trabalha, ativo)
- reunioes (id, data, tema, descricao)
- presencas (id, reuniao_id, padrinho_id, presente, justificada)
- temas (id, titulo, data_aviso, data_limite, data_entrega, situacao)
- tema_padrinhos (tema_id, padrinho_id)
- advertencias (id, padrinho_id, tipo, origem, motivo, data)
- calouros (id, nome, telefone, turno, genero, idade, cidade_bh, prouni, trabalha)
- matches (id, padrinho_id, calouro_id)
- config (chave, valor)
- logs (id, acao, descricao, data, ip)

## Regras de negócio
- Advertência amarela: falta sem justificativa em reunião ou manual (atraso em tema, comportamento leve)
- Advertência grave (vermelha): não entrega de tema ou comportamento grave — sempre manual
- Limite de amarelos = total de reuniões do semestre (calculado automaticamente)
- Padrinho reprova se faltar em TODAS as reuniões
- Status calculado pelo calcular_status(padrinho_id) em models.py

## Nomenclatura de status (versão final)
- apto → Aprovado (verde #10b981)
- alerta → Em alerta (âmbar #f59e0b)
- inapto_amarelo → Reprovado (laranja #f97316)
- inapto_vermelho → Reportado (vermelho #dc2626)

## Nomenclatura de advertências
- tipo "amarelo" → exibe como Advertência
- tipo "vermelho" → exibe como Advertência Grave

## Design system (app.css)
Arquivo em static/css/app.css com prefixo pt-.
- Cor primária: #7c5cff · hover: #5b3df5
- Sidebar: #0f1424 (sempre escura)
- Fundo app: #f6f6fa
- Fontes: Inter + JetBrains Mono
- Classes principais: pt-card, pt-btn, pt-badge, pt-metric-card, pt-table, pt-modal, pt-nav-item

## config_semestre.json
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

## Funcionalidades implementadas
- CRUD de padrinhos, calouros, reuniões, temas, advertências
- Sistema de advertências automáticas (faltas) e manuais (amarelo e vermelho)
- Sincronização de presença via Google Forms/Sheets
- Match padrinho-calouro com algoritmo de compatibilidade
- Redistribuição de calouros ao remover padrinho
- Relatórios HTML para impressão (Aptidão ACG, Resumo, Reportados)
- Logs de auditoria
- Login com autenticação
- Dark mode
- Design system com identidade visual própria
- Dados demográficos e distribuição por turno no relatório

## Pendente (ver docs/tarefas.md)
- Melhorias de interface (remover CSV, mover Forms pra Reuniões, etc.)
- Tela de Início do Semestre (importação via Forms)
- Limite de amarelos automático por número de reuniões
- Handoff para próximo coordenador
- Deploy no Fly.io

## Relatórios implementados
4 relatórios gerados como páginas HTML/Jinja — usuário imprime via Ctrl+P → Salvar como PDF.
Rotas: /relatorio/aptidao · /relatorio/resumo · /relatorio/reportados · /match/lista-contatos
1. Aptidão ACG — lista de aprovados para a secretaria
2. Resumo do semestre — cronograma de temas + resultado geral
3. Reportados — lista para entrega ao Prof. Laerte Xavier
4. Lista de contatos — padrinho → calouros com telefones

## Integração Google Sheets — autenticação

### Leitura (sincronizar_presencas_sheets)
Usa service account (credentials.json).
Email: padrinho-track@padrinho-track.iam.gserviceaccount.com
A planilha precisa ser compartilhada com esse email como Editor.

### Criação de planilhas (gerar_planilha_temas, exportar_lista_contatos_sheets)
Usa OAuth2 (client_secrets.json). Arquivos criados no Drive de pexy0000@gmail.com.
Na primeira execução abre o browser para autorização — token salvo em
%APPDATA%\gspread\authorized_user.json (Windows).

## Variáveis de ambiente (.env)
APP_USERNAME=admin
APP_PASSWORD=sua_senha
SECRET_KEY=uma_chave_secreta
GEMINI_API_KEY=sua_chave_gemini

## Importante
- Nunca quebrar os 29 testes existentes
- Manter dark mode em todos os templates
- Sidebar sempre escura (#0f1424) independente do tema
- Login está comentado temporariamente no before_request — descomentar antes do deploy
- scripts/seed.py e scripts/seed_calouros.py estão no .gitignore (dados reais)
- config_semestre.json, credentials.json, client_secrets.json estão no .gitignore
- Tailwind CDN convive com app.css — Tailwind para layout, app.css para componentes visuais

## Modo de operação — autonomia
Ao receber uma tarefa do docs/tarefas.md:

1. Leia o CLAUDE.md e o tarefas.md antes de começar
2. Execute a tarefa completa sem pedir confirmação no meio
3. Após cada alteração relevante, rode pytest e corrija eventuais falhas antes de continuar
4. Só conclua a tarefa quando todos os critérios estiverem satisfeitos:
   - Os 29 testes passando
   - Nenhum print() de debug no código
   - Dark mode preservado nos templates alterados
5. Avise quando terminar com um resumo do que foi feito

Se encontrar ambiguidade ou risco de quebrar algo crítico, pare e pergunte antes de agir.

## Idioma
Sempre responda em português do Brasil.