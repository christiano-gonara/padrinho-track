# Camada de Repositórios (`repositories/`)

Este diretório implementa o padrão **Repository (Data Access Object)**, isolando todas as consultas e comandos SQL do restante da aplicação.

---

## 🎯 Objetivos de Arquitetura

1. **Isolamento de SQL**: Toda e qualquer instrução `SELECT`, `INSERT`, `UPDATE` e `DELETE` fica contida nesta camada. Nem rotas nem templates Jinja manipulam SQL diretamente.
2. **Prevenção a SQL Injection**: Todas as queries utilizam parâmetros seguros (`?` traduzidos para `%s` em PostgreSQL), sem interpolação direta de strings.
3. **Compatibilidade Multi-Banco**: Opera em conjunto com o wrapper em `database.py`, permitindo execução transparente em **SQLite local** ou **PostgreSQL em produção**.

---

## 📂 Módulos de Repositório

| Arquivo | Entidade / Domínio | Operações Principais |
|---|---|---|
| [`padrinho_repository.py`](padrinho_repository.py) | Padrinhos / Madrinhas | `listar_ativos()`, `buscar_por_id()`, `cadastrar()`, `atualizar()`, `desativar()` |
| [`calouro_repository.py`](calouro_repository.py) | Calouros | `listar()`, `cadastrar()`, `buscar_sem_match()`, `remover()` |
| [`match_repository.py`](match_repository.py) | Matches | `criar()`, `listar_com_detalhes()`, `limpar_semestre()`, `remover_por_padrinho()` |
| [`reuniao_repository.py`](reuniao_repository.py) | Reuniões | `listar()`, `criar()`, `buscar_por_id()`, `contar()` |
| [`presenca_repository.py`](presenca_repository.py) | Frequência | `lancar()`, `obter_por_reuniao()`, `contar_faltas_por_padrinho()` |
| [`tema_repository.py`](tema_repository.py) | Temas / Prazos | `listar()`, `criar()`, `vincular_padrinhos()`, `atualizar_situacao()` |
| [`advertencia_repository.py`](advertencia_repository.py) | Advertências | `criar()`, `listar_por_padrinho()`, `contar_amarelos_e_vermelhos()` |
| [`config_repository.py`](config_repository.py) | Configurações Chave-Valor | `obter()`, `salvar()`, `obter_todas()` |
| [`log_repository.py`](log_repository.py) | Auditoria | `registrar_log()`, `listar_recentes()` |
