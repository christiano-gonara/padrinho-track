# Tarefas

> Antes de começar qualquer tarefa, leia o CLAUDE.md.
> O modo de operação e as regras do projeto estão lá.
>
> ⚠️ LOGIN DESATIVADO — reativar before_request em app.py
> antes de divulgar a URL de produção:
> https://padrinho-track-production.up.railway.app/

---

## Tarefa 1 — Lista negra de padrinhos reportados

Padrinho que recebe advertência vermelha é adicionado
automaticamente à lista negra — não pode ser importado
como padrinho em semestres futuros.

### Implementação
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

Roda os 62 testes e commita:
git add .
git commit -m "feat: lista negra de padrinhos reportados"
git push

---

## Tarefa 2 — Envio de certificados por email

Botão "Enviar certificados por email" na página de relatórios:
- Gera PDF de cada certificado via weasyprint
- Envia para o email cadastrado de cada padrinho aprovado
- Corpo do email:
  "Olá, [Nome]! Parabéns pela participação como Mentor
   Voluntário. Segue em anexo seu certificado. Atenciosamente,
   Coordenação da Monitoria — Eng. de Software · PUC Minas"
- Variáveis no .env: GMAIL_USER e GMAIL_APP_PASSWORD
  (senha de app gerada no Google — não a senha da conta)

Roda os 62 testes e commita:
git add .
git commit -m "feat: envio de certificados por email"
git push

---

## Tarefa 3 — Níveis de permissão

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

### Implementação
- Dois campos no .env: APP_USERNAME, APP_PASSWORD (já existe)
  e ADMIN_PASSWORD (novo — para ações críticas)
- Modal de confirmação de senha antes de ações críticas
- Não requer sessão separada — só confirmação pontual

Roda os 62 testes e commita:
git add .
git commit -m "feat: níveis de permissão por ação"
git push

---

## Tarefa 4 — README com demonstração visual

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

Mantém os 62 testes passando.

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