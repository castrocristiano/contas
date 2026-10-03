# Feature 016: Definir o3-mini como Modelo Padrão de Extração de Faturas

## Contexto e Motivação
A extração de faturas complexas de cartão de crédito no formato brasileiro (como LuizaCred, Magazine Luiza, Nubank, Itaú) frequentemente envolve dezenas de lançamentos parcelados, encargos misturados, tabelas em duas colunas e seções de parcelamento futuro.
Durante testes práticos, o modelo de raciocínio profundo **`o3-mini`** da OpenAI demonstrou capacidade superior na análise minuciosa de cada lançamento (identificando 53 itens com conciliação contábil quase exata de R$ 21,89), superando o `gpt-4o` em precisão e sem omitir parcelas antigas ou encargos.

Esta especificação define a configuração do modelo `o3-mini` como o padrão do sistema tanto na camada de configuração (`Settings`), quanto na interface do Streamlit e no assistente de chat.

---

## Requisitos Funcionais

- **RF-001 (Configuração Padrão em Settings)**:
  - Em `src/contas/config.py`, atualizar o valor padrão do campo `invoice_model: str` de `"gpt-4o"` para `"o3-mini"`.
  - Atualizar o arquivo `.env.example` documentando `INVOICE_MODEL=o3-mini`.

- **RF-002 (Padrão no Seletor da Interface Streamlit)**:
  - Na tela de Importação de Fatura (`src/contas/ui/app.py`), definir `o3-mini` como primeira opção / índice padrão (`index=0`) no selectbox de modelos de IA.
  - Ordem das opções: `["o3-mini", "gpt-4o", "gpt-4o-mini"]`.
  - Manter a descrição informativa destacando as vantagens do `o3-mini` (raciocínio contábil avançado e conciliação precisa).

- **RF-003 (Padronização do Chat Interativo de Faturas)**:
  - Garantir que o chat interativo de refinamento da fatura utilize `o3-mini` como padrão caso nenhum outro modelo seja explicitamente selecionado.

- **RF-004 (Retrocompatibilidade e Testes)**:
  - Manter compatibilidade com testes unitários existentes em `tests/unit/test_invoice_parser.py`, garantindo que mocks e fixtures aceitem `"o3-mini"` sem falhas.

---

## Requisitos Não Funcionais

- **RNF-001 (Transparência Operacional)**: O log de reconciliação matemática em `invoice_parser.py` deve exibir explicitamente `Modelo: o3-mini` quando este for acionado.
- **RNF-002 (Custo-Benefício)**: O `o3-mini` possui precificação mais econômica por token do que o `gpt-4o`, reduzindo os custos de chamadas com OpenAI para o usuário.
