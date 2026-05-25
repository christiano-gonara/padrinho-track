# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.

---

## Tarefa 1 — Corrigir JavaScript dos modais de edição

O console do browser mostra:
- reunioes:195 — Uncaught SyntaxError: Unexpected end of input
- reunioes:232:253 — Uncaught SyntaxError: Unexpected end of input
- temas:234:230 — Uncaught SyntaxError: Unexpected end of input

Os blocos <script> no final de reunioes.html e temas.html
estão com sintaxe JavaScript incompleta — alguma chave ou
parêntese faltando. Corrige os dois arquivos.

Roda os 29 testes e commita:
git add .
git commit -m "fix: corrigir sintaxe JavaScript nos modais de edição"
git push

---

## Tarefa 2 — Simplificar página de match

A página de match precisa ser mais limpa e intuitiva.

### Remover da interface
- Campo "Score mínimo" — remover da tela, fixar como 0 no código
- Campo "Máx. calouros por padrinho" — remover da tela, calcular
  automaticamente: ceil(total_calouros / total_padrinhos)
- Tabela de pesos exposta — substituir por tooltip no ícone ⓘ

### Comportamento por estado

Estado 1 — sem matches:
- Mostrar apenas botão "Gerar matches automaticamente"
- Algoritmo roda e salva direto, sem etapa de confirmação separada

Estado 2 — matches confirmados:
- Mostrar lista padrinho → calouros
- Sem botões desnecessários

### Redistribuição de calouros (caso raro)
No detalhe do padrinho, botão "Remover do programa":
- Mostra os calouros órfãos
- Para cada calouro, dropdown pra escolher novo padrinho
- Botão "Confirmar redistribuição"
Remover botão "Resetar matches" da página de match.

### Exportar lista de contatos
Botão "Exportar lista de contatos" na página de match:
- Gera CSV com: Padrinho, Turno, Calouro, Telefone do Calouro
- Um arquivo único com todos os pares
- Coordenador manda pra cada padrinho via WhatsApp

Roda os 29 testes e commita:
git add .
git commit -m "feat: simplificar página de match e exportar lista de contatos"
git push

---

## Tarefa 3 — Integração com Google Sheets — Presença

Pré-requisito: credentials.json do Google Cloud no .gitignore.

### Fluxo
Durante a reunião o coordenador manda o link do Google Forms no chat.
O Forms coleta: nome completo, matrícula, email, telefone.
Após a reunião, clica "Sincronizar" no sistema — presenças são registradas
automaticamente. Padrinho que faltou mas tem justificativa preenche o mesmo
Forms e também ganha presença na próxima sincronização.
Os dados do Forms são usados só pra identificação — não ficam salvos no sistema.

### Identificação do padrinho (ordem de prioridade)
1. Matrícula — bate, registra, para.
2. Email — se matrícula não bater, tenta email.
3. Nome completo — último recurso, case insensitive e sem acentos.
Resposta que não bater em nenhum dos três vai para lista de não reconhecidas.

### Implementação
1. Instalar dependência: pip install gspread, adicionar ao requirements.txt
2. Em config.html — adicionar seção "Google Forms — Presença":
   - Campo para colar o link da planilha de respostas do Forms
   - Salva na tabela config do banco (chave: sheets_presenca_url)
3. Criar função em models.py sincronizar_presencas_sheets(reuniao_id):
   - Lê a planilha via gspread usando credentials.json
   - Para cada resposta, tenta identificar o padrinho na ordem acima
   - Registra presença para os reconhecidos
   - Idempotente — rodar duas vezes não gera duplicatas
   - Retorna dict com: registradas, nao_reconhecidas (lista de respostas)
4. Em reunioes.html — adicionar botão "Sincronizar Forms" em cada reunião
   - Rota POST /reunioes/<reuniao_id>/sincronizar em app.py
   - Exibe toast com resultado:
     "8 presenças registradas. 2 não reconhecidas: João 99999, Maria abc@"
5. Roda os 29 testes após a implementação

---

## Tarefa 4 — Integração com Google Sheets — Inscrição em temas

Pré-requisito: Tarefa 3 concluída (infraestrutura Google Sheets já pronta).

### Fluxo
Coordenador mantém uma planilha template reutilizável a cada semestre:
- Apaga inscrições antigas
- Cola os temas novos com o limite de vagas (média: total padrinhos ÷ total temas)
- Manda o link pros padrinhos
- Padrinhos inserem o nome até o limite
- Coordenador clica "Sincronizar temas" no sistema

### Implementação
1. Em config.html — adicionar campo para link da planilha de temas
   - Salva na tabela config (chave: sheets_temas_url)
2. Criar função em models.py sincronizar_responsaveis_temas():
   - Lê a planilha via gspread
   - Bate nomes com padrinhos cadastrados (mesma lógica da presença)
   - Atualiza tema_padrinhos no banco
   - Idempotente
3. Botão "Sincronizar inscrições" na página de temas
   - Rota POST /temas/sincronizar em app.py
   - Toast com resultado: "15 responsáveis atualizados"
4. Roda os 29 testes após a implementação

---

## Tarefa 5 — Importação de padrinhos e calouros via Google Forms

Pré-requisito: Tarefa 3 concluída (infraestrutura Google Sheets já pronta).

### Fluxo
1. Forms de cadastro de padrinhos coleta:
   nome, matrícula, email, telefone, turno, curso, instituição,
   cidade (Grande BH ou não), prouni, trabalha, idade
2. Forms de cadastro de calouros coleta os mesmos campos
3. Sistema lê a planilha via Google Sheets
4. Filtra apenas respostas de Engenharia de Software da PUC Minas
5. Importa os válidos pro banco — duplicatas ignoradas por matrícula

### Implementação
- Rota POST /padrinhos/importar-forms em app.py
- Rota POST /calouros/importar-forms em app.py
- Botões "Importar do Forms" nas páginas de padrinhos e calouros
- Relatório de importação: X importados, Y ignorados (curso diferente),
  Z duplicatas puladas

Roda os 29 testes após a implementação.

---

## Tarefa 6 — Dados demográficos no relatório

Adicionar bloco de perfil no Resumo do Semestre, exibido apenas
quando houver dados demográficos preenchidos (não NULL).

### Campos a exibir
Perfil dos padrinhos e calouros separadamente:
- Distribuição por turno (Manhã X% · Noite Y%)
- % mora na Grande BH
- % Prouni
- % trabalha

Não exibir gênero — dado pouco informativo no contexto do curso.

Exibir aviso discreto se dados demográficos ainda não estiverem
disponíveis: "Disponível após importação via Google Forms"

Roda os 29 testes após a implementação.

---

## Tarefa 7 — Deploy no Fly.io

Pré-requisito: login reativado (descomentar before_request em app.py).

1. Criar conta no Fly.io (gratuito — https://fly.io)
2. Instalar flyctl (CLI do Fly.io) e fazer login
3. Rodar fly launch na raiz do projeto — detecta Flask automaticamente
4. Configurar variáveis de ambiente via fly secrets set
5. fly deploy — sobe o sistema
6. Testar todas as rotas em produção
7. Atualizar README.md com a URL de produção

Observação: SQLite persiste no PythonAnywhere gratuito.
Não migrar para PostgreSQL neste momento.

---

## Tarefa 8 — Bot do Telegram (futuro)

Cria bot.py com python-telegram-bot integrado ao banco SQLite:
- /status — resumo de aptos/alertas/inaptos
- /faltas — lista de faltas da última reunião
- /alerta — padrinhos com 1 amarelo + telefone
- /relatorio — abre link do relatório no sistema

Mantém os 29 testes passando.

---

## Tarefa 9 — Integração com Claude API (Anthropic)

Duas funcionalidades usando a API da Anthropic. Custo estimado:
menos de R$1,00 por semestre completo.

### 9.1 — Análise de risco por padrinho

No detalhe do padrinho, botão "Analisar com IA" que gera um
parágrafo curto de análise de risco baseado no histórico.

Contexto enviado à API (JSON):
```json
{
  "padrinho": {
    "nome": "...",
    "turno": "...",
    "status": "..."
  },
  "presencas": {
    "total_reunioes": 3,
    "presentes": 2,
    "faltas": 1
  },
  "advertencias": {
    "amarelos": 1,
    "vermelhos": 0
  },
  "temas": {
    "pendentes": 2,
    "entregues": 1,
    "atrasados": 0
  }
}
```

Prompt: análise de risco de reprovação em linguagem natural,
máximo 3 frases, tom objetivo.

Exibir resultado abaixo dos cards de advertências no detalhe
do padrinho. Cachear por sessão — não rechamar a API toda vez
que a página abre.

### 9.2 — Resumo do semestre em linguagem natural

No relatório de Resumo do Semestre, bloco gerado pela IA com
um parágrafo resumindo o desempenho geral do semestre.

Contexto enviado à API (JSON):
```json
{
  "semestre": "2026/1",
  "total_padrinhos": 50,
  "aprovados": 42,
  "em_alerta": 5,
  "reprovados": 2,
  "reportados": 1,
  "total_reunioes": 3,
  "media_presenca": 87,
  "temas_entregues": 13,
  "temas_pendentes": 2
}
```

Prompt: resumo executivo do semestre em linguagem natural,
máximo 4 frases, tom profissional.

Gerar uma vez ao abrir o relatório, exibir acima dos cards
de resultado final.

### Implementação
- ANTHROPIC_API_KEY no .env
- Função chamar_claude(prompt, contexto) em models.py
- Usa modelo claude-sonnet-4-20250514
- Tratamento de erro — se API falhar, exibe campo vazio
  sem quebrar a página

Roda os 29 testes após a implementação.