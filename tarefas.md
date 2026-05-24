# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.

---

## Tarefa 1 — Corrigir bugs críticos

### C1 — calcular_status retorna amarelos: 0 fixo
Arquivo: models.py linha ~278
Trocar:
  return {"status": "apto", "amarelos": 0, "vermelhos": 0}
Por:
  return {"status": "apto", "amarelos": amarelos, "vermelhos": vermelhos}

### C2 — emitir_advertencias_falta gera duplicatas
Arquivo: models.py:220-232
Verificar se já existe registro para (padrinho_id, reuniao_id, origem='falta')
antes de inserir. Duplo submit ou F5 corrompe dados.

### C3 — registrar_entrega_tema e marcar_tema_nao_entregue geram duplicatas
Arquivo: models.py:159-218
Verificar se já existe advertência para (padrinho_id, tema_id) antes de inserir.

### C4 — get_config abre conexão extra dentro do loop de calcular_status
Arquivo: models.py:258-278
Receber limite_amarelos como parâmetro ou ler uma vez fora do loop.
Com 50 padrinhos → 150 conexões desnecessárias no dashboard.

### C5 — Funções mortas com import pandas
Arquivo: models.py:460-484
Remover exportar_aptos_csv e exportar_vermelhos_csv.

Roda os 18 testes após cada correção.

---

## Tarefa 2 — Migrar relatórios para HTML/Jinja

1. Mover os 3 templates para templates/pages/:
   - relatorio_aptidao_acg.html
   - relatorio_resumo_semestre.html
   - relatorio_reportados.html
2. Substituir rotas atuais pelas 3 novas (ver rotas_relatorios.py)
3. Carregar config_semestre.json uma vez no topo do app.py como CONFIG
4. Adaptar chamadas de funções para os nomes reais de models.py
5. No relatorio.html adicionar 3 botões que abrem as rotas em nova aba:
   - [Ver Aptidão ACG]
   - [Ver Resumo do Semestre]
   - [Ver Reportados]
6. Usuário imprime via Ctrl+P → Salvar como PDF
7. Roda os 18 testes — nenhum pode quebrar

---

## Tarefa 3 — Atualizar config_semestre.json com equipe

Adicionar ao JSON:
  "coordenadora_geral": "Ana Santos",
  "coordenadores": ["Christiano Gonçalves", "Perciliana", "Giovanna", "Zaine", "Luiz"]

Garantir que get_config_semestre usa .get() com defaults para os campos
novos — evita UndefinedError se o JSON estiver em versão antiga.

---

## Tarefa 4 — Corrigir bugs médios de performance

### M1 — N+1 em get_todos_temas
1 query por tema para buscar responsáveis. Resolver com JOIN em query única.

### M2 — N+1 no dashboard e rotas de relatório
Passar limite_amarelos uma vez fora do loop de calcular_status.

### M3 — presencas_por_reuniao faz 2 queries por reunião
Trocar por SUM(CASE WHEN presente=1 THEN 1 ELSE 0 END) com GROUP BY.

### M4 — POST de presenças abre uma conexão por padrinho
Refatorar para inserção em lote numa transação única.

### M5 — importar_presencas_csv faz SELECT de matrícula linha a linha
Buscar todos os padrinhos de uma vez, criar dict {matricula: id} antes do loop.

### M6 — init_db() chamado em toda requisição
Mover para antes do app.run ou with app.app_context().

### M7 — N+1 em get_calouros_match_completo
Resolver com LEFT JOIN matches JOIN calouros.

### M8 — get_relatorio_aptos e get_relatorio_vermelhos são código morto
Remover ou simplificar para filtros sobre get_relatorio_geral().

### M9 — Bloco de emissão de advertências duplicado
Extrair _emitir_advertencias_tema(conn, tema_id, tipo, motivo).

### M10 — calcular_status faz 2 queries que poderiam ser 1
Trocar por GROUP BY tipo em query única.

---

## Tarefa 5 — Corrigir bugs baixos (antes do deploy)

### B1 — Open redirect no login
Validar next_url.startswith("/") antes de redirecionar.

### B2 — debug=True em produção
Trocar por debug=os.environ.get("FLASK_DEBUG", "0") == "1"

### B3 — SECRET_KEY e APP_PASSWORD com fallbacks inseguros
Garantir que sem .env o app não sobe em produção.

### B4 — except Exception silencia erros reais
Trocar por except sqlite3.IntegrityError no cadastro de padrinhos.

### B5 — Falta de índices nas colunas mais usadas
Adicionar em database.py:
  CREATE INDEX IF NOT EXISTS idx_advertencias_padrinho ON advertencias(padrinho_id);
  CREATE INDEX IF NOT EXISTS idx_presencas_padrinho ON presencas(padrinho_id);
  CREATE INDEX IF NOT EXISTS idx_presencas_reuniao ON presencas(reuniao_id);
  CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_tema ON tema_padrinhos(tema_id);
  CREATE INDEX IF NOT EXISTS idx_tema_padrinhos_padrinho ON tema_padrinhos(padrinho_id);

### B6 — config_semestre.json sem fallback para campos novos
Já coberto pela Tarefa 3.

---

## Tarefa 6 — Revisar e atualizar testes

### Passo 1 — Análise (não mexe em nada ainda)
Analisa os 18 testes em tests/ e responde:

1. Algum teste está testando comportamento que
   não bate mais com a lógica atual do sistema?
2. Quais funcionalidades importantes de models.py
   e app.py não têm nenhum teste cobrindo?
3. A calcular_status() está sendo testada para
   todos os cenários possíveis?
   (apto, alerta, inapto_amarelo, inapto_vermelho)
4. O limite_amarelos configurável está sendo
   testado ou está hardcoded nos testes?

Apresenta o relatório e aguarda aprovação antes de continuar.

### Passo 2 — Execução (após aprovação do relatório)
- Corrige os testes desatualizados
- Escreve os testes que estão faltando
- Roda pytest até todos passarem
- Mostra o resultado final

---

## Tarefa 7 — Atualizar README.md

Substituir o README.md atual pelo novo (arquivo README.md em anexo).
Mudanças principais:
- Equipe completa: coordenadora geral Ana Santos + todos os coordenadores
- PDFs substituídos por "Relatórios HTML para impressão via browser"
- Pandas removido da stack
- Passo do .env adicionado no "Como rodar"
- Roadmap corrigido — logs e match já estão feitos, marcar como concluídos

---

## Tarefa 8 — Bot do Telegram (futuro)
Cria bot.py com python-telegram-bot integrado ao banco SQLite:
- /status — resumo de aptos/alertas/inaptos
- /faltas — lista de faltas da última reunião
- /alerta — padrinhos com 1 amarelo + telefone
- /pdf — abre link do relatório no sistema

Mantém os 18 testes passando.