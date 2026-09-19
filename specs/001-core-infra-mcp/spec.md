# Especificação de Funcionalidade: Infraestrutura Base e Servidor MCP de Finanças

**Branch da Funcionalidade**: `001-core-infra-mcp`

**Data de Criação**: 2026-09-19

**Status**: Rascunho

**Entrada**: Descrição do usuário: "Criar a infraestrutura base do sistema Contas com podman-compose (PostgreSQL), ambiente Python com uv e servidor MCP básico com schemas de transações financeiras."

## Cenários de Usuário e Testes *(obrigatório)*

### História de Usuário 1 - Registro de Transação Financeira via Assistente (Prioridade: P1)

Como gestor das finanças domésticas interagindo com um assistente inteligente, quero registrar despesas e receitas informando valor, data, descrição, conta e categoria em linguagem natural estruturada, para que a transação seja validada e salva de forma confiável no banco de dados.

**Por que esta prioridade**: É o valor essencial do produto (MVP). Sem a capacidade de registrar e persistir transações com segurança, nenhum relatório ou automação financeira tem utilidade.

**Teste Independente**: Pode ser testado de ponta a ponta enviando uma operação de lançamento estruturada ao assistente e verificando a confirmação do registro e a atualização imediata do saldo da conta correspondente.

**Cenários de Aceitação**:

1. **Dado** uma conta financeira previamente cadastrada com saldo de R$ 100,00, **Quando** o usuário solicitar o registro de uma despesa de R$ 35,50 com categoria "Alimentação", **Então** a transação é gravada com precisão decimal exata e o saldo da conta passa a ser R$ 64,50.
2. **Dado** o sistema operacional e pronto para receber conexões, **Quando** uma receita de R$ 1.500,00 for submetida com data e descrição válidas, **Então** o sistema confirma a criação com identificador único e status de liquidado.

---

### História de Usuário 2 - Consulta de Saldos e Extrato Consolidado (Prioridade: P2)

Como gestor financeiro, quero solicitar ao assistente o saldo consolidado de todas as contas e o extrato detalhado de um período específico, para que eu possa acompanhar a evolução dos gastos e entradas domésticas.

**Por que esta prioridade**: Usuários precisam auditar e visualizar o histórico após registrarem dados. Dá transparência imediata à saúde financeira da residência.

**Teste Independente**: Pode ser testado populando contas com transações preexistentes e solicitando o extrato do mês corrente; a resposta deve conter a lista cronológica de transações e o balanço final exato.

**Cenários de Aceitação**:

1. **Dado** transações registradas em diferentes datas e categorias, **Quando** o usuário requisitar o extrato do mês corrente, **Então** o sistema retorna as transações ordenadas cronologicamente com valor, categoria e saldo resultante.
2. **Dado** múltiplas contas ativas (ex: "Corrente", "Carteira", "Poupança"), **Quando** for solicitada a listagem de saldos, **Então** o sistema apresenta os saldos individuais e a soma patrimonial consolidada.

---

### História de Usuário 3 - Validação Estrita e Proteção contra Lançamentos Inválidos (Prioridade: P3)

Como usuário, quero que o sistema rejeite imediatamente tentativas de lançamentos com dados corrompidos, valores negativos indevidos, contas inexistentes ou datas inválidas, para que a base de dados contábil nunca fique inconsistente.

**Por que esta prioridade**: Garante a integridade financeira estabelecida na Constituição do projeto, impedindo que erros do usuário ou alucinações de modelos de IA degradem os dados.

**Teste Independente**: Submeter transações sem valor, com valor zero, com valores mal formatados ou apontando para contas não cadastradas e verificar se todas são recusadas com mensagens de erro claras e informativas.

**Cenários de Aceitação**:

1. **Dado** uma requisição de transação com valor zero ou formato monetário corrompido, **Quando** a validação for processada, **Então** a operação é abortada sem alterar o banco de dados e um erro explicativo é retornado.
2. **Dado** uma solicitação de transferência entre contas, **Quando** a conta de destino não existir, **Então** nenhuma dedução na conta de origem é realizada (atomicidade garantida).

---

### Casos de Borda

- **Precisão fracionária**: Como o sistema lida com valores monetários com mais de duas casas decimais (ex: R$ 10,555)? O sistema trunca ou arredonda estritamente para 2 casas decimais segundo regras financeiras pré-definidas (meio para cima).
- **Datas futuras**: O sistema permite agendamento de transações com data futura? Sim, transações futuras são aceitas com status "pendente", afetando o saldo projetado mas não o saldo imediatamente liquidado.
- **Caracteres especiais na descrição**: Descrições com emojis, quebras de linha ou caracteres acentuados são normalizados e armazenados sem perda de integridade.
- **Falha transitória de comunicação**: Se a conexão com a base de dados cair durante uma escrita, o assistente recebe notificação de erro transitório e nenhuma transação parcial é gravada.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **RF-001**: O sistema DEVE permitir a criação, consulta e listagem de contas financeiras (ex: nome, tipo de conta, saldo inicial e moeda padrão BRL).
- **RF-002**: O sistema DEVE permitir a criação, consulta e listagem de categorias financeiras divididas entre receitas e despesas (ex: Moradia, Alimentação, Transporte, Salário).
- **RF-003**: O sistema DEVE permitir o registro de transações financeiras contendo: identificador único, data/hora da transação, valor monetário decimal exato, tipo (receita, despesa ou transferência), conta de origem, conta de destino (opcional para transferências), categoria e descrição.
- **RF-004**: O sistema DEVE garantir atomicidade nas operações de transferência entre contas (o débito na origem e o crédito no destino ocorrem juntos ou falham juntos).
- **RF-005**: O sistema DEVE disponibilizar ferramentas padronizadas no protocolo do assistente para: `criar_conta`, `listar_contas`, `registrar_transacao`, `consultar_extrato` e `obter_resumo_financeiro`.
- **RF-006**: O sistema DEVE validar rigorosamente todos os parâmetros de entrada de acordo com esquemas declarativos antes de executar qualquer persistência.
- **RF-007**: O sistema DEVE expor um mecanismo de verificação de prontidão e saúde da base de dados e do servidor de comunicação.

### Entidades Principais

- **Conta (Account)**: Entidade que representa uma fonte ou destino de recursos financeiros (banco, carteira, corretora). Possui nome, identificador, tipo (corrente, poupança, investimento, dinheiro), saldo atual e data de criação.
- **Categoria (Category)**: Agrupador conceitual de movimentações financeiras. Possui nome, tipo (receita ou despesa) e status de ativação.
- **Transação (Transaction)**: Registro imutável de uma movimentação financeira ocorrida ou agendada. Possui identificador, valor com precisão de duas casas decimais, tipo (receita, despesa, transferência), conta de origem, conta de destino (quando transferência), categoria associada, data de competência, status (liquidada, pendente) e notas descritivas.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **CS-001**: 100% das transações e cálculos de saldos utilizam precisão decimal exata, com zero divergência de centavos decorrentes de ponto flutuante binário.
- **CS-002**: Operações de registro de transação e consulta de saldos pelo assistente são processadas e respondidas em menos de 1 segundo em ambiente local.
- **CS-003**: 100% das requisições com dados monetários inválidos ou contas inexistentes são bloqueadas na camada de validação de schema sem gravação em banco.
- **CS-004**: O ambiente completo (serviços de persistência e servidor de assistência) sobe e atinge estado de prontidão operacional com um único comando de orquestração.
- **CS-005**: Um usuário iniciante consegue interagir com o assistente para consultar contas e registrar sua primeira despesa em menos de 3 minutos após a inicialização.

## Premissas e Suposições

- **Moeda**: A moeda padrão para todas as contas e transações da residência é o Real Brasileiro (BRL).
- **Ambiente de Usuário**: O sistema é voltado para uso doméstico/unifamiliar em ambiente de infraestrutura local containerizada.
- **Comunicação do Assistente**: O protocolo padrão para interação autônoma com assistentes e modelos de linguagem externos é o Model Context Protocol (MCP).
- **Persistência Relacional**: Os dados financeiros residem em banco de dados relacional que suporte integridade referencial, transações ACID e precisão decimal numérica.
