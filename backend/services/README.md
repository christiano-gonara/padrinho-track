# Camada de Serviços (`services/`)

Este diretório concentra o **coração das regras de negócio (Domain Services)** do Padrinho Track.

---

## 🎯 Princípios de Design

- **Independência de Framework**: Funções e classes aqui contidas operam sobre dados estruturados (dicionários, tuplas, modelos), sem acoplamento direto com objetos de requisição HTTP (`request`, `session`).
- **Testabilidade**: Todo o comportamento crítico de negócio pode ser testado de forma rápida e determinística sem necessidade de subir um servidor web.
- **Idempotência**: Processamentos em lote (ex: reprocessar faltas de uma reunião) são concebidos para não duplicar penalidades caso invocados mais de uma vez.

---

## 🛠️ Principais Módulos

### 1. `status_service.py` (Engine de ACG & Advertências)
Gerencia as regras de aptidão para concessão de horas complementares (ACG):
- **Apto**: Padrinho ativo, com faltas dentro da tolerância e sem advertências impeditivas.
- **Alerta**: Padrinho com 1 falta não justificada (cartão amarelo), recebendo aviso prévio.
- **Inapto (Amarelos)**: Padrinho que atingiu o limite de tolerância (2 amarelos por padrão).
- **Inapto (Vermelho)**: Padrinho com falta grave manual, não entrega de tema ou ausência total em reuniões.

### 2. `match_service.py` & `match_algorithm.py` (Cruzamento Padrinho-Calouro)
Algoritmo ponderado de correspondência de perfis:
- **Prioridade de Turno**: Padrinhos e calouros do mesmo turno (Manhã vs Noite) recebem pontuação máxima.
- **Distribuição Balanceada**: Distribui calouros de modo equitativo entre os padrinhos ativos disponíveis.
- **Redistribuição Automática**: Ao desativar ou remover um padrinho do programa, seus calouros vinculados são realocados sem perda de rastreabilidade.

### 3. `certificado_service.py` & `relatorio_service.py` (Fechamento & Documentos)
- Compila o balanço semestral de presenças, reuniões e atividades entregues.
- Renderiza certificados individuais padronizados com os dados acadêmicos do aluno e da coordenação.
- Empacota e disponibiliza o download em lote de certificados através de arquivo comprimido (`.zip`).

### 4. Módulos Auxiliares
- `presenca_service.py`: Lançamento e validação de frequência em reuniões.
- `tema_service.py`: Acompanhamento de entregas de temas, verificação de datas limites e penalização por atraso.
- `padrinho_service.py` & `calouro_service.py`: Regras de ciclo de vida das entidades participantes.
