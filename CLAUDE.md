# Padrinho Track — Contexto do Projeto

## O que é
Sistema web interno de gestão do programa de mentoria acadêmica da PUC Minas — Engenharia de Software. Coordena 50 padrinhos (veteranos voluntários) e 127 calouros ao longo do semestre.

## Stack
- Backend: Python + Flask
- Banco: SQLite (instance/mentoria.db)
- Frontend: HTML + Tailwind CSS + Remix Icon
- Testes: pytest (18 testes em tests/)
- PDF: reportlab
- Dados: Pandas

## Estrutura
- app.py — rotas Flask
- database.py — conexão e criação do banco
- models.py — funções de leitura/escrita
- templates/ — páginas Jinja2
- static/ — SVGs da logo e assets
- tests/ — testes automatizados
- seed_exemplo.py — dados fictícios pra demo

## Regras de negócio
- Advertência amarela: falta sem justificativa em reunião ou atraso de 1 dia na entrega de tema
- Advertência grave (vermelha): não entrega de tema ou comportamento inadequado
- Limite de amarelos configurável (padrão 2) — salvo na tabela config do banco
- Status: apto / alerta / inapto / inapto grave
- Inapto grave reporta ao professor coordenador

## Status atual
Bloco 7 em andamento:
- PDF de aptidão ACG implementado (reportlab)
- Logs de auditoria pendente
- Histórico por semestre pendente
- Interface de match pendente

## Importante
- Nunca quebrar os 18 testes existentes
- Manter dark mode em todos os templates
- Sidebar sempre escura (#0f1424) independente do tema
- Credenciais via .env (APP_USERNAME, APP_PASSWORD, SECRET_KEY)
- seed.py e seed_calouros.py estão no .gitignore (dados reais)

## Idioma
Sempre responda em português do Brasil. Mostre todas as saídas, confirmações e mensagens em português do Brasil.
