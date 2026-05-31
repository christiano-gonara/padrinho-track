# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.
>
> Após cada commit, matar todos os processos Python na porta 5000
> via PowerShell e reiniciar o servidor limpo antes de concluir.

---

## Tarefa 1 — Melhorias de UX pendentes

### 1.1 — Busca em tempo real nos calouros
Já existe na lista de padrinhos — replicar o mesmo comportamento
na página de calouros.

### 1.2 — Filtro por status na lista de padrinhos
Adicionar botões de filtro no topo da lista:
Todos | Aprovados | Em alerta | Reprovados | Reportados
Filtro client-side via JavaScript — sem recarregar a página.

### 1.3 — Calouros por turno no relatório de resumo
Adicionar distribuição de calouros por turno no bloco demográfico
do relatorio_resumo_semestre.html:
  Calouros por turno: Manhã X (X%) · Noite X (X%)

### 1.4 — Separar testes por funcionalidade
Reorganizar tests/ em arquivos separados com comentário
explicativo no topo de cada um:
- test_advertencias.py — regras de advertência e status
- test_presencas.py — sincronização e lançamento
- test_temas.py — entrega, atraso, responsáveis
- test_match.py — algoritmo de match
- test_integracao.py — rotas HTTP
- test_models.py — funções gerais de models.py

### 1.5 — Corrigir menção a 29 testes no CLAUDE.md
O projeto agora tem 53 testes — atualizar as referências.

Roda os 53 testes e commita:
git add .
git commit -m "feat: melhorias de UX, calouros por turno e reorganização de testes"
git push

---

## Tarefa 2 — Lista negra e permissões

### 2.1 — Lista negra de padrinhos reportados
Padrinho que recebe advertência vermelha é adicionado
automaticamente à lista negra — não pode ser importado
como padrinho em semestres futuros.

Implementação:
- Nova tabela no banco: lista_negra (id, matricula, nome,
  motivo, semestre, data)
- Ao emitir advertência vermelha, inserir automaticamente
  na lista_negra
- Na importação via Forms (importar_padrinhos_sheets()),
  verificar se a matrícula está na lista_negra e ignorar
  com aviso: "X candidatos ignorados por histórico de
  ocorrência grave: Nome (matrícula)"
- Na tela de Início do Semestre, exibir os ignorados
  no relatório de importação
- Página de visualização da lista negra em Configurações
  com opção de remover manualmente (caso excepcional)

### 2.2 — Níveis de permissão
Adicionar dois níveis de acesso ao sistema:

**Coordenador** (acesso padrão):
- Lançar presença, sincronizar Forms
- Adicionar advertências manuais
- Ver relatórios

**Coordenador Chefe** (acesso total — senha extra):
- Tudo do coordenador
- Remover padrinho do programa
- Editar dados de padrinho
- Limpar logs
- Exportar backup do banco
- Enviar certificados

Implementação:
- Dois campos no .env: APP_USERNAME, APP_PASSWORD (já existe)
  e ADMIN_PASSWORD (novo — para ações críticas)
- Modal de confirmação de senha antes de ações críticas
- Não requer sessão separada — só confirmação pontual

Roda os 53 testes e commita:
git add .
git commit -m "feat: lista negra e permissões por ação"
git push

---

## Tarefa 3 — Certificado de participação

### Certificado individual por padrinho aprovado
Página HTML formatada para impressão, gerada automaticamente
para cada padrinho aprovado ao final do semestre.

Conteúdo do certificado:
- Logo Padrinho Track
- Nome completo do padrinho em destaque
- Matrícula e turno
- Texto:
  "participou como Padrinho Voluntário no programa de
   Mentoria Acadêmica — Engenharia de Software · PUC Minas
   Semestre 2026/1, contribuindo com a formação acadêmica
   de calouros do curso junto a uma equipe de X padrinhos."
- Assinaturas: Prof. Laerte Xavier e Ana Santos
- Data de emissão

Implementação:
- Rota GET /relatorio/certificado/<padrinho_id> em app.py
- Template templates/pages/certificado.html
- Botão "Ver certificado" no detalhe de cada padrinho aprovado
- Botão "Gerar todos os certificados" na página de relatórios
  — abre lista com link individual de cada aprovado

### Envio por email (Gmail SMTP)
Botão "Enviar certificados por email" na página de relatórios:
- Gera PDF de cada certificado
- Envia para o email cadastrado de cada padrinho aprovado
- Corpo do email:
  "Olá, [Nome]! Parabéns pela participação como Padrinho
   Voluntário. Segue em anexo seu certificado. Atenciosamente,
   Coordenação da Monitoria — Eng. de Software · PUC Minas"
- Variáveis no .env: GMAIL_USER e GMAIL_APP_PASSWORD
  (senha de app gerada no Google — não a senha da conta)

Roda os 53 testes e commita:
git add .
git commit -m "feat: certificado de participação e envio por email"
git push

---

## Tarefa 4 — Deploy na Hostinger

Pré-requisitos:
- Login reativado (descomentar before_request em app.py)
- Migração para PostgreSQL
- Cloudflare configurado na frente

### 4.1 — Migrar para PostgreSQL
- Substituir SQLite por PostgreSQL em database.py
- Usar psycopg2 como driver
- Manter compatibilidade com todos os testes
- Atualizar requirements.txt

### 4.2 — Configurar VPS na Hostinger
1. Contratar VPS Ubuntu (plano básico)
2. Instalar Python, nginx, gunicorn, PostgreSQL
3. Subir o código via git clone
4. Configurar variáveis de ambiente no servidor
5. Configurar gunicorn como serviço systemd
6. Configurar nginx como proxy reverso

### 4.3 — Configurar Cloudflare
1. Apontar domínio para o IP do VPS via Cloudflare
2. Ativar proxy (laranja) para ocultar o IP
3. Ativar SSL/TLS

### 4.4 — Pós-deploy
- Testar todas as rotas em produção
- Reativar login (before_request em app.py)
- Atualizar README.md com a URL de produção
- Adicionar índice em logs.data no banco (item B3 da auditoria)

---

## Tarefa 5 — README com demonstração visual

Adicionar seção de demonstração no README.md com GIFs
mostrando o sistema em ação:

1. Dashboard com cards de status
2. Sincronizar presença via Forms
3. Relatório de aptidão sendo gerado
4. Início do semestre importando padrinhos

Ferramentas recomendadas: ScreenToGif (Windows) — gratuito.
GIFs de 10-15 segundos cada, hospedados no próprio repositório
em docs/images/.

---

## Opcional — Bot do Telegram

Cria bot.py com python-telegram-bot integrado ao banco.
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

Mantém os 53 testes passando.

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