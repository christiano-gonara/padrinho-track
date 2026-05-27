# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.
>
> Após cada commit, matar todos os processos Python na porta 5000
> via PowerShell e reiniciar o servidor limpo antes de concluir.

---

## Tarefa 1 — Handoff para o próximo coordenador

### Criar scripts/setup_handoff.py
Script que o próximo coordenador roda uma vez pra configurar
o sistema para o novo semestre:

```python
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import set_config

with open('config_handoff.json') as f:
    config = json.load(f)

set_config('sheets_presenca_url', config['google']['planilha_presencas_url'])
set_config('sheets_inscricoes_url', config['google']['planilha_inscricoes_url'])
set_config('sheets_padrinhos_url', config['google']['forms_padrinhos_url'])
set_config('sheets_calouros_url', config['google']['forms_calouros_url'])
print("[OK] Sistema configurado para o novo semestre.")
```

### Criar config_handoff.json na raiz
Adicionar ao .gitignore — contém links e chaves reais do próximo coordenador.

```json
{
  "semestre": "2026/2",
  "data_inicio": "2026-08-01",
  "data_fim": "2026-12-15",
  "google": {
    "service_account_email": "padrinho-track@padrinho-track.iam.gserviceaccount.com",
    "planilha_presencas_url": "COLE_O_LINK_AQUI",
    "planilha_inscricoes_url": "COLE_O_LINK_AQUI",
    "forms_padrinhos_url": "COLE_O_LINK_AQUI",
    "forms_calouros_url": "COLE_O_LINK_AQUI"
  },
  "apis": {
    "gemini_key": "COLE_A_CHAVE_AQUI",
    "anthropic_key": "COLE_A_CHAVE_AQUI"
  }
}
```

### Criar docs/HANDOFF.md
Guia completo passo a passo para o próximo coordenador:
1. Clonar o repositório GitHub
2. Gerar novo client_secrets.json no Google Cloud Console
3. Preencher config_handoff.json com os novos links e chaves
   (as chaves ficam só localmente — nunca commitar)
4. Rodar python scripts/setup_handoff.py
5. Copiar o backup do banco instance/mentoria.db do coordenador anterior

### Implementação no sistema
- Botão "Exportar backup do banco" em Configurações
  — baixa o instance/mentoria.db atual

Roda os 29 testes após a implementação.

---

## Tarefa 2 — Deploy no Fly.io

Pré-requisito: login reativado (descomentar before_request em app.py).

1. Criar conta no Fly.io (gratuito — https://fly.io)
2. Instalar flyctl (CLI do Fly.io) e fazer login
3. Rodar fly launch na raiz do projeto — detecta Flask automaticamente
4. Configurar variáveis de ambiente via fly secrets set
5. fly deploy — sobe o sistema
6. Testar todas as rotas em produção
7. Atualizar README.md com a URL de produção

Observação: SQLite persiste com volume Fly — configurar fly volumes create.
Não migrar para PostgreSQL neste momento.

---

## Opcional — Bot do Telegram

Cria bot.py com python-telegram-bot integrado ao banco SQLite.
Agrega no portfólio mas não é essencial pro programa.

### Consultas
- /status — resumo de aptos/alertas/inaptos
- /faltas — faltas da última reunião
- /alerta — padrinhos com 1 amarelo + telefone

### Ações de tema
- /entregue <nome do tema> — marca tema como entregue
- /nao_entregue <nome do tema> — marca tema como não entregue

### Relatórios
- /relatorio acg — manda link do relatório de aptidão
- /relatorio resumo — manda link do resumo do semestre

### Alertas automáticos
- Tema com prazo vencido sem entrega registrada
- Padrinho que atingiu o limite de amarelos
- Lembrete de reunião próxima

Mantém os 29 testes passando.

---

## Opcional — Integração com Claude API (Anthropic)

Agrega no portfólio mas não é essencial pro programa.

### Análise de risco por padrinho
Botão "Analisar com IA" no detalhe do padrinho — gera parágrafo
curto de análise de risco baseado no histórico. Máximo 3 frases.

### Resumo do semestre em linguagem natural
No Resumo do Semestre, parágrafo gerado pela IA resumindo
o desempenho geral. Máximo 4 frases, tom profissional.

### Implementação
- ANTHROPIC_API_KEY no .env
- Modelo: claude-sonnet-4-20250514
- Tratamento de erro — se API falhar, exibe campo vazio