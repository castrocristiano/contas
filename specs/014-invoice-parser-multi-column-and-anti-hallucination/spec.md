# Feature 014: Suporte a Faturas Multi-Coluna e Prevenção de Alucinações/Duplicações no Extrator

## Contexto e Motivação
Durante a importação de faturas de cartão de crédito em PDF (como faturas LuizaCred / Magazine Luiza / Itaú), o extrator de faturas (`src/contas/services/invoice_parser.py`) apresentou divergências financeiras significativas em relação ao PDF original:
1. **Lançamentos dispostos em duas colunas paralelas** na mesma página foram extraídos pelo `pypdf` na mesma linha de texto (ex: `23/12 COMPRA A 21,90  27/08 COMPRA B 60,00`). Com isso, o modelo de LLM extraiu apenas as transações da coluna direita, omitindo diversas compras da coluna esquerda.
2. **Extração de simulações de financiamento e parcelamento futuro**: simulações informativas ("Parcelamento de fatura", "Simulação Saque Cash", "Opções de Parcelamento Mínimo / Parcelas Fixas") continham valores de IOF simulados que foram indevidamente extraídos como despesas reais da fatura.
3. **Duplicação de encargos consolidados vs. discriminados**: a fatura continha uma linha resumo "Encargos (financiamento + moratório) R$ 183,16" e, na seção detalhada, os itens abertos ("Juros do rotativo R$ 96,51", "Multa por atraso R$ 66,79", etc.). Ambos foram extraídos simultaneamente, gerando cobrança em duplicidade na tabela.

Esta especificação define o pré-processamento inteligente do texto cru de PDFs para desacoplar transações em múltiplas colunas e o aprimoramento do System Prompt para eliminar alucinações e duplicações.

---

## Requisitos Funcionais

- **RF-001 (Pré-processamento de Colunas Múltiplas)**: 
  - Antes de enviar o texto ao modelo de IA, o extrator deve processar cada linha do texto cru extraído do PDF.
  - Linhas contendo mais de uma transação (identificadas por padrões de data `DD/MM` associados a valores monetários no formato brasileiro `R$ X,XX` ou `X,XX`) devem ser divididas em linhas individuais independentes.
  - Linhas compostas por cabeçalhos e transações agrupadas (ex: `TITULAR EXEMPLO (final 0000) 15/01 LOJA EXEMPLO 50,00`) devem ter a transação desmembrada em linha própria.
  
- **RF-002 (Prevenção de Simulações Informativas no Prompt)**:
  - O `system_prompt` do `parse_invoice_with_openai` deve proibir expressamente a extração de valores oriundos de simulações financeiras, tais como: "Simulação de Compras parc.", "Simulação Saque Cash", "Opções de Parcelamento de Fatura", "Parcelas Fixas", "Pagamento Mínimo" e valores de IOF hipotéticos dessas simulações.
  
- **RF-003 (Deduplicação de Encargos Consolidados vs. Detalhados)**:
  - O prompt deve instruir o modelo a **não extrair o totalizador de encargos** (ex.: "Total de encargos", "Encargos (financiamento + moratório)") quando os encargos individuais já estiverem detalhados na fatura (juros do rotativo, juros de mora, multa por atraso, IOF de financiamento).
  - Apenas as parcelas detalhadas individuais devem ser mantidas para correta categorização e conferência.

- **RF-004 (Detecção de Descontos e Estornos Negativos)**:
  - Lançamentos com valores negativos ou estornos (ex: `- 0,01`, estornos de compras) não devem ser confundidos com pagamentos ou descartados incorretamente quando representarem ajustes de fatura.

---

## Requisitos Não Funcionais

- **RNF-001 (Compatibilidade e Robustez)**: A função de pré-processamento deve ser puramente baseada em expressões regulares e tratamento de strings, sem adicionar dependências externas pesadas e mantendo tempo de execução desprezível (< 50ms por PDF).
- **RNF-002 (Cobertura de Testes)**: Criar testes unitários específicos cobrindo o pré-processamento de texto multi-coluna, o isolamento de linhas e a validação do prompt atualizado.
- **RNF-003 (Consistência com Clean Architecture)**: As alterações devem ser restritas aos serviços de extração e UI, preservando contratos existentes de schemas e use cases.
