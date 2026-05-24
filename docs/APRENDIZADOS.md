# Lições aprendidas — Padrinho Track

## O que eu faria diferente

### 1. Design antes do código
Antes de escrever uma linha de HTML, criar o design system completo no Claude Design.
Exportar o app.css com todos os tokens, classes e componentes.
Só depois começar os templates.

**Por quê:** Refatorar visual depois que o sistema já funciona é muito mais trabalhoso do que construir em cima de uma base visual sólida.

### 2. Escolher uma só abordagem de CSS
Não misturar Tailwind + CSS customizado. Escolher um e seguir até o fim.
- Tailwind — mais flexível, bom pra protótipos rápidos
- Design system próprio (app.css) — mais consistente, melhor pra projetos com identidade visual

### 3. CLAUDE.md desde o início
Criar o arquivo CLAUDE.md na raiz antes de qualquer sessão do Claude Code.
Economiza tokens e evita reexplicar o projeto a cada sessão.

### 4. tarefas.md para sequências longas
Quando tiver 3+ tarefas em sequência, criar um tarefas.md e mandar o Claude Code executar em ordem.
Mais eficiente que mandar prompt por prompt.

### 5. Componentes reutilizáveis desde o início
Identificar o que vai se repetir (cards de métricas, badges de status, modais) e criar em templates/components/ logo no começo.
Evita ter que refatorar depois.

### 6. Seed de exemplo público desde o início
Criar o seed_exemplo.py com dados fictícios antes de começar a desenvolver.
Facilita os testes e a demonstração do sistema.

### 7. Deploy antes de features avançadas
Hospedar o sistema cedo — mesmo que simples — antes de implementar features complexas.
Feedback real de uso vale mais que funcionalidades não testadas.

### 8. Definir relatórios antes de implementar
Mapear quais relatórios o sistema precisa entregar antes de começar o desenvolvimento.
Cada relatório tem um destinatário e um objetivo claro — isso define quais dados precisam estar no banco.

---

## O que funcionou bem

- Pytest desde o início — os 18 testes salvaram várias vezes
- Separar modelos (models.py) das rotas (app.py) desde o começo
- Dark mode implementado cedo — difícil de adicionar depois
- Seed de exemplo público — qualquer pessoa consegue rodar o projeto
- CLAUDE.md e tarefas.md — economizam muito token nas sessões longas
- config_semestre.json — configurações do semestre num lugar só
- app.css com design system completo — consistência visual garantida

---

## Stack recomendada para próximos projetos

**Backend:** Python + Flask (simples) ou FastAPI (mais moderno)
**Banco:** SQLite para projetos locais, PostgreSQL para deploy
**Frontend:** Design system próprio com CSS variables + Inter + JetBrains Mono
**Testes:** pytest desde o primeiro dia
**IA:** Claude Code com CLAUDE.md configurado antes de começar

---

## Relatórios do sistema

### Padrão visual dos relatórios
Os relatórios PDF devem seguir a mesma identidade visual do sistema:
- Cores de status: verde #10b981 (apto), âmbar #f59e0b (alerta), laranja #f97316 (inapto), vermelho #dc2626 (inapto grave)
- Tipografia: Inter para títulos e corpo, JetBrains Mono para matrículas e números
- Logo do sistema no cabeçalho: padrinho-track-lockup.svg
- Paleta de fundo: branco #ffffff com bordas #e6e7ee
- Badges de status com tint colorido — mesmo padrão do sistema web
- Rodapé: "Gerado automaticamente pelo Padrinho Track · PUC Minas · Eng. de Software"

### Relatório 1 — Aptidão ACG
Destinatário: secretaria / coordenação do curso
Objetivo: liberar horas ACG para os padrinhos aprovados

Conteúdo:
- Cabeçalho: programa, semestre, professor coordenador, data de geração
- Resumo: total inscritos, total aptos, total inaptos
- Tabela de aptos: nome completo, matrícula, turno, presenças/total reuniões
- Rodapé com campo para assinatura do coordenador

### Relatório 2 — Resumo do semestre
Destinatário: arquivo interno / coordenação
Objetivo: documentar o que foi realizado no semestre

Conteúdo:
- Resumo geral: total padrinhos, total calouros, total reuniões realizadas
- Cronograma de temas: título, data, responsáveis, situação de entrega
- Resultado geral: aptos X / inaptos Y / inaptos graves Z
- Gráfico de presença por reunião

### Relatório 3 — Inaptos graves
Destinatário: professor coordenador
Objetivo: comunicar formalmente os casos que precisam de ação

Conteúdo:
- Cabeçalho formal com programa e semestre
- Tabela: nome completo, matrícula, email, motivo, data da advertência grave
- Total de casos
- Campo para assinatura do coordenador