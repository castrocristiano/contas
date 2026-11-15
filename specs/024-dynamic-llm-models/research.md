# Research & Decisões Arquiteturais: Modelos Dinâmicos OpenAI (024-dynamic-llm-models)

## Contexto da Pesquisa

O sistema utilizava `o3-mini` como modelo padrão para o parser de faturas em PDF e o modelo `gpt-4o-mini` para o chat do assistente financeiro. Com a depreciação e descontinuação do `o3-mini`, o sistema precisa:
1. Eleger `gpt-4o` como o novo modelo padrão de alto desempenho.
2. Permitir que a aplicação liste dinamicamente os modelos disponíveis na conta do usuário via `client.models.list()`, mantendo resiliência e suporte a novos modelos sem intervenção no código.

---

## Decisão 1: Arquitetura de Descoberta e Filtro de Modelos OpenAI

### Decisão
Criar o módulo `src/contas/services/openai_models.py` contendo:
- `DEFAULT_FALLBACK_MODELS = ["gpt-4o", "gpt-4o-mini", "o1"]`
- `DEFAULT_MODEL = "gpt-4o"`
- Função `get_available_openai_models(client: OpenAI | None = None, force_refresh: bool = False) -> list[str]`
- Cache em memória com TTL de 1 hora para evitar chamadas de rede repetitivas à API `models.list()` da OpenAI.

### Racional
- A API `client.models.list()` retorna centenas de modelos (ex: `text-embedding-3-small`, `whisper-1`, `tts-1`, `davinci-002`, `o3-mini`).
- Filtro: consideramos apenas modelos cujo ID comece com `gpt-4` ou `o1` ou contenha `chatgpt`, e excluímos modelos de áudio (`realtime`, `audio`, `transcription`) ou deprecados.
- Se a chamada à API falhar (ex: chave de API inválida, sem permissão, timeout ou sem internet), o fallback para `DEFAULT_FALLBACK_MODELS` garante que a interface nunca quebre.

---

## Decisão 2: Atualização de Configuração e Constantes

### Decisão
Em `src/contas/config.py`:
- Alterar `invoice_model: str = "gpt-4o"`.
- Em `README.md` e documentações, atualizar a menção a `o3-mini` para `gpt-4o`.
- Nos testes unitários (`test_invoice_parser.py`), atualizar referências que esperavam `o3-mini` para `gpt-4o`.

---

## Decisão 3: Experiência do Usuário (UI) no Streamlit

### Decisão
Na tela **"🧾 Importar Fatura PDF"**:
- Adicionar o seletor alimentado por `get_available_openai_models()`.
- Se o modelo padrão `gpt-4o` estiver disponível, ele é selecionado por padrão.
- Adicionar um botão discreto de atualização (`st.button("🔄", help="Atualizar lista de modelos da OpenAI")`) ao lado do seletor que chama `get_available_openai_models(force_refresh=True)`.

---

## Conformidade Constitucional

| Princípio | Conformidade |
|:---|:---|
| **I. Simplicidade e YAGNI** | Implementação direta utilizando o SDK oficial da OpenAI sem frameworks pesados de terceiros. |
| **IV. Integração Segura com IA** | Mantém Structured Outputs estrito (`response_format=InvoiceExtractionContainer`). |
| **VI. Idioma** | Código e identificadores em EN-US (`openai_models.py`, `get_available_openai_models`, `DEFAULT_FALLBACK_MODELS`); UI e documentação em PT-BR. |
