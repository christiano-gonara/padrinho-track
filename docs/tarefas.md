# Tarefas

## Próxima prioridade — produção segura

### 1. Revisar segredos
- Revogar e gerar nova `GEMINI_API_KEY` se ela tiver sido compartilhada fora da máquina.
- Conferir `.gitignore` para manter `.env`, `client_secrets.json` e credenciais fora do Git.
- Usar `SECRET_KEY` e `APP_PASSWORD` fortes em produção.

### 2. PostgreSQL em produção
- Manter SQLite para desenvolvimento local.
- Usar `DATABASE_URL` no Railway/produção.
- Testar fluxo completo com PostgreSQL:
  - importação de padrinhos
  - importação de calouros
  - reuniões/presenças
  - temas/entregas
  - relatórios
  - certificados em ZIP

### 3. Repositories mais completos
- Continuar removendo SQL direto de services e integrações.
- Priorizar:
  - `integrations/importers.py`
  - `services/match_algorithm.py`
  - testes que ainda montam dados com SQL manual
- Manter `models.py` apenas como fachada temporária.
- Depois remover imports de `models.py` nos services e routes.

### 4. Entidades de domínio
- Criar dataclasses simples quando fizer sentido:
  - `Padrinho`
  - `Calouro`
  - `Tema`
  - `StatusACG`
- Usar primeiro em services novos, sem tentar migrar tudo de uma vez.

### 5. Logs e suporte
- Melhorar mensagens de erro para importações.
- Registrar erros inesperados com contexto suficiente para suporte.
- Criar tela simples de diagnóstico:
  - banco conectado
  - total de padrinhos
  - total de calouros
  - total de reuniões
  - total de temas
  - últimos erros

## Testes

### 6. Atualizar cobertura por camada
- Preferir testes de services/repositories em vez de testar wrappers de `models.py`.
- Manter testes de integração para rotas principais.
- Adicionar testes para:
  - login obrigatório
  - nomes de arquivos gerados
  - ZIP com padrinhos e coordenação
  - relatório de aptidão com múltiplas páginas

### 7. Remover testes obsoletos
- Remover testes que validem rotas legadas já apagadas.
- Evitar testes que dependam de implementação interna antiga.
- Manter testes que representem regras reais do programa.

## Experiência e responsividade

### 8. Telas com tabelas grandes
- Melhorar visualização mobile/tablet de:
  - padrinhos
  - calouros
  - presenças
  - aptidão ACG
- Usar scroll horizontal ou cards responsivos quando necessário.

### 9. Relatórios PDF
- Garantir que cada relatório:
  - não corte conteúdo no meio
  - tenha header/footer consistentes
  - tenha nomes e datas legíveis
  - funcione bem com muitos participantes

## Futuro

### 10. Automação de certificados sem email por enquanto
- Manter geração em ZIP.
- Melhorar organização interna do ZIP:
  - `padrinhos/`
  - `coordenacao/`
  - nomes curtos e padronizados
- Deixar envio automático por email para etapa futura.

### 11. Estudo de versão Flutter
- Não reescrever tudo agora.
- Caminho recomendado:
  - manter backend Flask
  - criar endpoints JSON
  - fazer Flutter consumir a API
  - deixar PDF/certificados no backend

### 12. Lista negra de ocorrências graves
- Criar tabela de histórico para padrinhos reportados.
- Bloquear reimportação automática em semestres futuros.
- Permitir remoção manual apenas em caso excepcional.
