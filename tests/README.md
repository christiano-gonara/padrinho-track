# Suíte de Testes Automatizados (`tests/`)

Este diretório contém os testes automatizados executados pelo **pytest**.

---

## 🎯 Filosofia da Suíte

Após a refatoração de simplificação, a suíte segue a filosofia de **alto valor agregado e zero redundância**:
- **Menos código de teste, maior cobertura de valor**: Eliminação de testes triviais de setters/getters de banco de dados ou requisições repetitivas de páginas.
- **Isolamento Completo**: Todos os testes usam fixtures com bancos temporários SQLite (`tmp_path`), garantindo que nenhum teste afete a base de dados de desenvolvimento ou produção.
- **Alta Velocidade**: A suíte completa executa em menos de **1 segundo** (~0.6s).

---

## 📂 Organização dos Arquivos

| Arquivo | Foco de Teste |
|---|---|
| [`test_regras_negocio.py`](test_regras_negocio.py) | Regras críticas de ACG: progressão de status (apto, alerta, inapto), faltas justificadas vs não justificadas, advertências automáticas por atraso/falta de temas e idempotência. |
| [`test_match.py`](test_match.py) | Algoritmo de cruzamento padrinho-calouro: afinidade por turno, casos de borda e balanceamento de calouros. |
| [`test_integracao.py`](test_integracao.py) | Rota pública da landing page sem login, proteção de rotas fechadas com redirecionamento para login (`302`) e principais operações de `POST`. |

---

## 🚀 Como Rodar os Testes

```bash
# Execução simples e rápida
pytest

# Execução detalhada (verbose)
pytest -v

# Executar com isolamento estrito de cache
pytest -q -p no:cacheprovider
```
