# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.

---

## Tarefa 1 — Corrigir o que sumiu após a reorganização

Verificar e restaurar o que foi perdido quando o prompt de parar
interrompeu a execução no meio:

1. templates/base.html — link "Match" no sidebar entre Calouros
   e a seção Gestão:
   <a href="/match" class="pt-nav-item">
     <i class="ri-link-m"></i>
     <span>Match</span>
   </a>

2. templates/pages/reunioes.html — botão de lápis em cada linha
   da tabela abrindo modal de edição com campos:
   data, tema, descrição

3. templates/pages/temas.html — botão de lápis em cada linha
   da tabela abrindo modal de edição com campos:
   título, data_aviso, data_limite, responsáveis

As rotas e funções já existem em app.py e models.py —
só garantir que os templates estão corretos.

Roda os 29 testes e commita:
git add .
git commit -m "fix: restaurar sidebar Match e botões de edição"
git push

---

## Tarefa 2 — Integração com Google Sheets (botão Sincronizar)

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
2. Em config.html — adicionar seção "Google Forms":
   - Campo para colar o link da planilha de respostas do Forms
   - Salva na tabela config do banco (chave: sheets_url)
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

## Tarefa 3 — Importação de padrinhos e calouros via Google Forms

Pré-requisito: Tarefa 2 concluída (infraestrutura Google Sheets já pronta).

### Fluxo
1. Forms de cadastro de padrinhos coleta:
   nome, matrícula, email, telefone, turno, gênero, idade,
   cidade (BH ou não), prouni, trabalha, curso, instituição
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

## Tarefa 4 — Bot do Telegram (futuro)

Cria bot.py com python-telegram-bot integrado ao banco SQLite:
- /status — resumo de aptos/alertas/inaptos
- /faltas — lista de faltas da última reunião
- /alerta — padrinhos com 1 amarelo + telefone
- /relatorio — abre link do relatório no sistema

Mantém os 29 testes passando.