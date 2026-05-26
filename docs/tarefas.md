# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.

---

## Tarefa 1 — Gerar Forms de inscrição em temas via Gemini API

Pré-requisito: GEMINI_API_KEY no .env (gratuito via Google AI Studio).

### Fluxo
1. Coordenador cadastra os temas no sistema normalmente
2. Clica "Gerar Forms de inscrição" na página de temas
3. Sistema monta JSON com temas e limite de vagas:
   {
     "semestre": "2026/1",
     "limite_vagas": ceil(total_padrinhos / total_temas),
     "temas": [
       {"titulo": "Boas vindas e Setup", "data_limite": "27/03"},
       ...
     ]
   }
4. Sistema manda o JSON pro Gemini API com o prompt:
   "Gere um Google Apps Script completo que crie um Google Forms
   com uma pergunta de múltipla escolha onde cada opção é um tema
   com limite de {limite_vagas} respostas. Use FormApp do Google."
5. Sistema exibe o script gerado com instruções:
   - Acesse script.google.com
   - Crie um novo projeto
   - Cole o script
   - Clique em Executar
6. Padrinho acessa o Forms, escolhe o tema
7. Coordenador sincroniza as inscrições via botão existente

### Implementação
- GEMINI_API_KEY no .env
- Função gerar_script_forms_temas(temas, limite) em models.py
  - Chama Gemini API com o JSON dos temas
  - Retorna o Apps Script gerado
- Rota POST /temas/gerar-forms em app.py
- Modal em temas.html exibindo o script gerado + instruções de uso
- Remover botões "Gerar planilha de inscrições" existentes —
  substituir por "Gerar Forms de inscrição"
- Roda os 29 testes após a implementação

---

## Tarefa 2 — Sincronizar inscrições de temas via Google Sheets

Pré-requisito: credentials.json já está na raiz do projeto.

### Fluxo
Após os padrinhos preencherem o Forms gerado na Tarefa 1:
1. Respostas ficam automaticamente na planilha de respostas do Forms
   (o Google cria essa planilha automaticamente)
2. Coordenador compartilha essa planilha com:
   padrinho-track@padrinho-track.iam.gserviceaccount.com
3. Cola o link da planilha em Configurações
4. Clica "Sincronizar inscrições" na página de temas
5. Sistema lê a planilha via service account, bate os nomes
   com padrinhos cadastrados e atualiza os responsáveis no banco

### Identificação do padrinho
1. Nome completo — case insensitive e sem acentos
2. Se não bater, vai para lista de não reconhecidos

### Implementação
- Em config.html — campo para link da planilha de respostas
  do Forms de inscrição (chave: sheets_inscricoes_url)
- Corrigir sincronizar_responsaveis_temas() para usar
  service account (credentials.json) — mesmo padrão da presença
- Botão "Sincronizar inscrições" já existe em temas.html
- Toast: "15 responsáveis atualizados. 2 não reconhecidos: João, Maria"
- Roda os 29 testes após a implementação

---

## Tarefa 3 — Integração com Google Sheets — Lista de contatos

Pré-requisito: client_secrets.json já está na raiz do projeto.

### Fluxo
Na página de match, botão "Exportar para Sheets":
- Sistema cria planilha no Google Sheets automaticamente
- Colunas: Padrinho | Turno | Calouro | Telefone do Calouro
- Coordenador manda o link interno pra equipe
- Cada coordenador manda os contatos pro seu grupo via WhatsApp

### Implementação
- Rota POST /match/exportar-sheets em app.py
- Função exportar_lista_contatos_sheets() em models.py
  usando OAuth2 (client_secrets.json)
- Toast com link da planilha gerada
- Roda os 29 testes após a implementação

---

## Tarefa 4 — Importação de padrinhos e calouros via Google Forms

Pré-requisito: credentials.json já está na raiz do projeto.

### Fluxo
1. Forms de cadastro de padrinhos coleta:
   nome, matrícula, email, telefone, turno, curso, instituição,
   cidade (Grande BH ou não), prouni, trabalha, idade
2. Forms de cadastro de calouros coleta os mesmos campos
3. Coordenador compartilha as planilhas de respostas com:
   padrinho-track@padrinho-track.iam.gserviceaccount.com
4. Sistema lê via service account e filtra apenas
   respostas de Engenharia de Software da PUC Minas
5. Importa os válidos pro banco — duplicatas ignoradas por matrícula

### Implementação
- Rota POST /padrinhos/importar-forms em app.py
- Rota POST /calouros/importar-forms em app.py
- Botões "Importar do Forms" nas páginas de padrinhos e calouros
- Relatório de importação: X importados, Y ignorados, Z duplicatas
- Em config.html — campos para links das planilhas de padrinhos
  e calouros (chaves: sheets_padrinhos_url, sheets_calouros_url)

Roda os 29 testes após a implementação.

---

## Tarefa 5 — Deploy no Fly.io

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

## Tarefa 6 — Bot do Telegram

Cria bot.py com python-telegram-bot integrado ao banco SQLite.

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

## Tarefa 7 — Integração com APIs de IA

### 7.1 — Gerar Forms de inscrição (Gemini API)
Já coberto na Tarefa 1.

### 7.2 — Análise de risco por padrinho (Claude API)

No detalhe do padrinho, botão "Analisar com IA" que gera um
parágrafo curto de análise de risco baseado no histórico.

Contexto enviado à API (JSON):
```json
{
  "padrinho": {"nome": "...", "turno": "...", "status": "..."},
  "presencas": {"total_reunioes": 3, "presentes": 2, "faltas": 1},
  "advertencias": {"amarelos": 1, "vermelhos": 0},
  "temas": {"pendentes": 2, "entregues": 1, "atrasados": 0}
}
```

Prompt: análise de risco de reprovação, máximo 3 frases, tom objetivo.
Exibir abaixo dos cards de advertências. Cachear por sessão.

### 7.3 — Resumo do semestre em linguagem natural (Claude API)

No Resumo do Semestre, parágrafo gerado pela IA resumindo
o desempenho geral do semestre. Máximo 4 frases, tom profissional.

### Implementação
- ANTHROPIC_API_KEY e GEMINI_API_KEY no .env
- Funções chamar_claude() e chamar_gemini() em models.py
- Modelos: claude-sonnet-4-20250514 e gemini-2.0-flash
- Tratamento de erro — se API falhar, exibe campo vazio

Roda os 29 testes após a implementação.

---

## Tarefa 8 — Handoff para o próximo coordenador

Documentar e implementar o processo de transferência do sistema
para o próximo coordenador da monitoria.

### Guia de handoff (adicionar em docs/HANDOFF.md)
Criar documento com passo a passo completo:

1. Transferência do repositório GitHub
   - Adicionar o novo coordenador como colaborador
   - Ou transferir a propriedade do repositório

2. Transferência das credenciais Google Cloud
   - Adicionar o email do novo coordenador como proprietário
     no projeto padrinho-track do Google Cloud Console
   - Orientar sobre geração de novo client_secrets.json
     (o token OAuth é pessoal — cada coordenador gera o seu)

3. Transferência das planilhas do Google Drive
   - Compartilhar as planilhas existentes com o novo coordenador
   - Transferir propriedade via Drive → clique direito →
     Compartilhar → mudar dono

4. Variáveis de ambiente (.env)
   - Passar as chaves: APP_USERNAME, APP_PASSWORD, SECRET_KEY,
     ANTHROPIC_API_KEY, GEMINI_API_KEY
   - Orientar sobre geração de novas chaves se necessário

5. Banco de dados
   - Exportar backup do instance/mentoria.db
   - Passar para o novo coordenador via Drive ou email

6. Início do novo semestre
   - Orientar sobre como rodar seed limpa pra novo semestre
   - Ou manter histórico e só adicionar novos padrinhos/calouros

### Implementação no sistema
- Adicionar página "Sobre / Handoff" em Configurações com:
  - Checklist visual dos itens acima
  - Links diretos pro Google Cloud Console e GitHub
  - Botão "Exportar backup do banco" — baixa o .db atual

Roda os 29 testes após a implementação.