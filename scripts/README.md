# Scripts e Utilitários (`scripts/`)

Scripts operacionais, geradores estáticos e rotinas de automação fora do fluxo direto de requisições web.

---

## 🛠️ Conteúdo do Diretório

### 1. `build_site.py` (Gerador Estático da Landing Page)
Gera uma versão totalmente estática da **Landing Page** em `docs/site/` para publicação no **GitHub Pages**:
- Renderiza `templates/pages/landing.html` simulando o contexto do Flask.
- Converte rotas absolutas do Flask em caminhos estáticos relativos com tag `<base href="/padrinho-track/">`.
- Cria o arquivo `.nojekyll` para desativar o processamento padrão do Jekyll no GitHub.
- Copia recursivamente todos os recursos estáticos de `static/` (fontes, estilos, imagens e logotipos).

**Como executar manualmente:**
```bash
python scripts/build_site.py
```

### 2. `seed_exemplo.py` (Banco de Testes e Demonstração)
Popula a base de dados local com registros fictícios e seguros para desenvolvimento e demonstração (padrinhos, calouros, reuniões e presenças).

**Como executar:**
```bash
python scripts/seed_exemplo.py
```

### 3. `match.py` (Execução em Linha de Comando)
Utilitário para rodar o algoritmo de match e exportar o resultado diretamente no terminal ou em CSV.
