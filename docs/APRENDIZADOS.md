# Aprendizados e fundamentos

Este projeto começou como uma solução prática para acompanhar o Programa de
Apadrinhamento de Calouros. Para os próximos ciclos, a meta é manter o sistema
mais fácil de manter, mais seguro e mais simples para outras pessoas usarem.

## Princípios para continuar

### Modularização
- Rotas devem receber requisições e chamar serviços.
- Services devem concentrar regras de negócio.
- Repositories devem concentrar consultas SQL.
- Templates devem apenas exibir dados.
- Evitar arquivos grandes demais, principalmente `app.py` e `models.py`.

### Segurança
- Proteger rotas com login.
- Nunca versionar segredos, tokens ou arquivos sensíveis.
- Validar uploads de CSV/Sheets antes de importar.
- Fazer backup do banco antes de importações grandes.
- Evitar expor nomes, matrículas, emails e telefones fora do contexto correto.

### Eficiência
- Automatizar tarefas repetitivas, como geração de certificados em PDF/ZIP.
- Manter testes para regras críticas: ACG, advertências, match, relatórios e certificados.
- Usar SQLite para desenvolvimento local e PostgreSQL para produção.
- Só otimizar performance depois de identificar gargalos reais.

### Responsividade e uso
- Tabelas grandes precisam funcionar bem em telas menores.
- Páginas de relatório devem paginar corretamente em PDF.
- Mensagens de erro devem explicar o que aconteceu e como corrigir.
- Fluxos importantes devem exigir poucos cliques: importar, conferir, gerar relatório e gerar certificados.

### Adaptabilidade
- Semestre, carga horária, coordenação e textos de certificado devem ser configuráveis.
- Critérios de aptidão ACG devem ficar fáceis de revisar a cada semestre.
- O sistema deve funcionar com dados reais sem depender de edição manual no código.

### Suporte a outras pessoas
- README deve explicar como rodar, configurar e atualizar o projeto.
- `docs/tarefas.md` deve guardar pendências e decisões.
- O sistema precisa ser compreensível para outro coordenador continuar usando.

## Ordem recomendada de melhorias

1. Autenticação e proteção das rotas.
2. Configurações editáveis de semestre, horas, coordenação e textos.
3. Mais repositories para reduzir SQL espalhado.
4. Melhor responsividade das telas com tabelas grandes.
5. Envio automático de certificados por email.
6. PostgreSQL em produção.

## Decisões que funcionaram bem

- Usar Flask, porque deixou o sistema simples de desenvolver.
- Criar testes com pytest.
- Separar rotas por domínio com Blueprints.
- Criar services para relatórios, certificados, temas, reuniões e match.
- Gerar relatórios e certificados a partir dos dados reais do banco.
- Usar ZIP de PDFs para reduzir trabalho manual no fechamento do semestre.

## Atenção para o próximo semestre

- Exigir email válido dos padrinhos no formulário inicial.
- Coletar turno, bolsa, trabalho e dados úteis já no Forms.
- Definir desde o começo quais relatórios serão entregues.
- Padronizar os nomes de arquivos gerados.
- Registrar reuniões e temas durante o semestre, não só no fechamento.
