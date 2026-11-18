# Próximos passos — Padrinho Track

Lista enxuta do que ainda vale melhorar nos próximos semestres.

## Prioridade alta

- **Testes no fluxo PostgreSQL em produção**: validar importação de planilhas, lançamento de presenças e geração do ZIP de certificados rodando com `DATABASE_URL`.
- **Organização do ZIP de certificados**: manter pastas separadas (`padrinhos/` e `coordenacao/`) com nomes padronizados sem acento.
- **Validação de planilhas**: melhorar mensagens de erro quando alguma coluna obrigatória do Google Forms vier com nome diferente.

## Melhorias futuras

- **Histórico de ocorrências graves**: impedir reimportação automática de padrinhos que já receberam cartão vermelho grave em semestres anteriores (permitindo liberação manual apenas pela coordenação).
- **Envio de certificados por e-mail**: automatizar o disparo após o fechamento do semestre, mantendo o download em ZIP como alternativa.
- **Tela simples de diagnóstico**: exibir status da conexão com o banco, totais cadastrados e últimos erros registrados.
