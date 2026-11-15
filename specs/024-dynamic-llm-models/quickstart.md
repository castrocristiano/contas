# Quickstart: Validação de Modelos Dinâmicos OpenAI (024-dynamic-llm-models)

## Cenários de Validação

### 1. Testes Automatizados Unitários
Execute a suíte de testes unitários do serviço de modelos:
```bash
.venv/bin/pytest tests/unit/test_openai_models.py -v
```

### 2. Validação Visual no Streamlit
1. Inicie o Streamlit:
   ```bash
   .venv/bin/streamlit run src/contas/ui/app.py
   ```
2. Acesse o menu **"🧾 Importar Fatura PDF"**.
3. Verifique se o campo **"🤖 Modelo de IA (OpenAI)"**:
   - Apresenta `gpt-4o` como opção selecionada por padrão.
   - Não contém o modelo deprecado `o3-mini`.
   - Contém um botão ao lado para atualizar os modelos diretamente da conta OpenAI.
