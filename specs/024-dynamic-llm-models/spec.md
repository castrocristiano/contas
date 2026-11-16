# Feature Specification: Remoção do o3-mini e Carregamento Dinâmico de Modelos OpenAI (024-dynamic-llm-models)

**Feature Branch**: `feature/024-dynamic-llm-models`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "o modelo 3o está depreciado, remova-o e crie uma feature para carregar os novos modelos também"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remoção do Modelo Deprecado o3-mini e Definição de Novo Padrão (Priority: P1) 🎯 MVP

Como usuário do sistema de gestão financeira,
Quero que o modelo deprecado `o3-mini` seja completamente removido das opções e configurações do sistema, sendo substituído pelo `gpt-4o` como modelo padrão,
Para que o processamento inteligente de faturas em PDF e o chat do assistente financeiro utilizem um modelo moderno, estável e de alta acurácia sem erros decorrentes de depreciação de API.

**Why this priority**: Evita falhas imediatas de execução causadas pela descontinuação ou indisponibilidade do modelo `o3-mini` na API da OpenAI e estabelece o `gpt-4o` como novo alicerce estável.

**Independent Test**: Pode ser testado carregando o sistema sem configuração explícita de modelo e verificando se `settings.invoice_model` e as seleções de interface apontam para `gpt-4o` sem nenhuma ocorrência de `o3-mini`.

**Acceptance Scenarios**:
1. **Given** que o usuário acessa a tela de importação de fatura PDF ou o assistente financeiro, **When** visualiza as opções de modelos, **Then** o modelo `o3-mini` não está mais presente na lista e o modelo selecionado por padrão é `gpt-4o`.
2. **Given** a configuração padrão em `src/contas/config.py` e documentações, **When** o valor padrão de `invoice_model` é lido, **Then** seu valor padrão é estritamente `"gpt-4o"`.

---

### User Story 2 - Carregamento Dinâmico de Modelos da Conta OpenAI (Priority: P2)

Como usuário com chave de API da OpenAI configurada,
Quero que a aplicação consulte dinamicamente os modelos disponíveis na minha conta OpenAI através de `client.models.list()`,
Para que novos modelos lançados pela OpenAI fiquem imediatamente disponíveis para seleção na interface sem necessidade de alterações no código-fonte.

**Why this priority**: Elimina o acoplamento rígido a listas estáticas de modelos no código, permitindo que a aplicação evolua de forma fluida conforme a OpenAI lança novas versões e famílias de modelos.

**Independent Test**: Pode ser testado configurando uma chave de API da OpenAI válida, acionando a função de listagem de modelos e verificando que a lista retornada contém os modelos ativos da conta filtrados para compatibilidade com chat e structured outputs (ex: `gpt-4o`, `gpt-4o-mini`, `o1`).

**Acceptance Scenarios**:
1. **Given** uma chave de API da OpenAI válida configurada, **When** a interface de importação de fatura ou assistente financeiro é carregada, **Then** o sistema consulta os modelos da OpenAI, filtra modelos incompatíveis (ex: embeddings, tts, whisper, dall-e) e apresenta os modelos compatíveis ordenados alfabeticamente ou por relevância.
2. **Given** uma falha de conexão com a API da OpenAI ou ausência de chave de API, **When** a listagem é solicitada, **Then** o sistema utiliza uma lista de fallback estática pré-definida (`gpt-4o`, `gpt-4o-mini`, `o1`), sem quebrar a interface nem lançar exceções não tratadas.
3. **Given** que a consulta à API da OpenAI foi realizada com sucesso, **When** o usuário navega entre páginas do sistema, **Then** a lista de modelos é armazenada em cache (TTL ou session state) para evitar chamadas de rede repetitivas e lentidão de renderização.

---

### User Story 3 - Botão de Atualização Manual de Modelos na Interface (Priority: P3)

Como usuário na tela de importação de fatura ou configurações,
Quero dispor de um botão de ação rápida (ícone de recarregar / "Atualizar Modelos"),
Para forçar uma nova consulta à API da OpenAI e sincronizar a lista caso eu tenha acabado de obter acesso a um novo modelo ou alterado minha chave de API.

**Why this priority**: Melhora a autonomia e transparência da experiência do usuário, permitindo invalidar o cache sob demanda sem reiniciar a aplicação inteira.

**Independent Test**: Pode ser testado clicando no botão "🔄 Atualizar Modelos" na interface do Streamlit e verificando que o cache de modelos é limpo e uma nova requisição à API da OpenAI é disparada com feedback visual (spinner/toast).

**Acceptance Scenarios**:
1. **Given** a tela de Importação de Fatura PDF aberta, **When** o usuário clica no botão de atualizar modelos, **Then** o sistema exibe feedback de carregamento, recarrega os modelos da API da OpenAI e atualiza o seletor `st.selectbox` reativamente.

---

### Edge Cases

- **Chave de API inválida ou sem permissão de leitura de modelos (`models:read`)**: O sistema deve capturar a exceção `openai.AuthenticationError` ou `openai.PermissionDeniedError`, logar um aviso informativo e carregar silenciosamente a lista de fallback com `gpt-4o`.
- **Filtro de modelos relevantes**: A API da OpenAI retorna centenas de IDs de modelos (incluindo `text-embedding-ada-002`, `whisper-1`, `tts-1`, `babbage-002`). A função de filtro deve reter exclusivamente modelos da família `gpt-4*`, `o1*`, `chatgpt-*` e versões correlatas adequadas para chat completions.
- **Modelos que não suportam Structured Outputs**: Se um modelo não suportar a API de Structured Outputs exigida pelo parser de faturas (`response_format`), o sistema deve indicar visualmente ou priorizar modelos com suporte comprovado (`gpt-4o`, `gpt-4o-mini`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE remover todas as menções e referências ao modelo `o3-mini` em `src/contas/config.py`, `src/contas/services/invoice_parser.py`, `src/contas/ui/app.py`, `README.md` e testes.
- **FR-002**: O sistema DEVE definir o modelo `gpt-4o` como o novo modelo padrão padrão em `Settings.invoice_model` e nos seletores da interface.
- **FR-003**: O sistema DEVE implementar uma função utilitária/serviço (`get_available_openai_models(client: OpenAI | None = None, force_refresh: bool = False) -> list[str]`) localizada em `src/contas/services/openai_models.py` (ou `invoice_parser.py`).
- **FR-004**: A função DEVE consultar `client.models.list()`, filtrar modelos de chat compatíveis e descartar modelos obsoletos ou incompatíveis (`dall-e`, `whisper`, `tts`, `embedding`, `o3-mini`).
- **FR-005**: O sistema DEVE prover uma lista de fallback estática (`["gpt-4o", "gpt-4o-mini", "o1"]`) caso a chave da OpenAI não esteja configurada ou ocorra timeout/falha de rede.
- **FR-006**: O sistema DEVE implementar cache em memória para a lista de modelos retornada pela API, evitando requisições desnecessárias a cada interação do Streamlit.
- **FR-007**: A tela de Importação de Fatura PDF no Streamlit DEVE carregar os modelos dinamicamente e disponibilizar um botão para forçar atualização da lista de modelos.

---

### Key Entities *(include if feature involves data)*

- **OpenAIModelInfo**: Estrutura contendo `model_id: str`, `display_name: str`, `supports_structured_outputs: bool`, `is_default: bool`.
- **ModelCacheEntry**: Estrutura interna para cache contendo `models: list[str]` e `timestamp: datetime`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das ocorrências ativas de `o3-mini` no código e configurações são substituídas por `gpt-4o`.
- **SC-002**: O tempo de carregamento da interface na presença de cache não excede 5ms adicionais em relação ao carregamento estático.
- **SC-003**: Na presença de uma chave de API válida, a interface exibe dinamicamente todos os modelos de chat disponíveis na conta do usuário.
- **SC-004**: Em caso de indisponibilidade de internet ou chave ausente, o sistema inicializa normalmente em menos de 10ms utilizando a lista de fallback sem erros.

---

## Assumptions

- A biblioteca oficial `openai` (>= 1.0) instalada no projeto suporta `client.models.list()`.
- O modelo `gpt-4o` continuará suportando Structured Outputs (`client.beta.chat.completions.parse`) conforme o SDK atual.
- A lista de modelos da conta OpenAI continuará sendo acessível utilizando a mesma chave de API configurada (`OPENAI_API_KEY` / `OPENAPI_KEY`).
