# Feature 019: GitHub Wiki & Documentação Completa de Portfólio

## Contexto e Motivação
O **Contas** evoluiu para uma aplicação de ponta com Clean Architecture, Model Context Protocol (MCP), inteligência artificial (OpenAI `o3-mini`), autenticação multi-tenant com aprovação prévia de usuários e interface moderna em Streamlit.
Como este é um projeto estratégico de **portfólio técnico**, é fundamental fornecer documentação de excelência tanto no **README.md** principal quanto em uma **Wiki estruturada para o GitHub** (com suporte a deploy automático via GitHub Actions).

---

## Requisitos Funcionais

- **RF-001 (Revitalização Completa do README.md)**:
  - Adicionar badges modernos (Python 3.12, MCP Protocol, Streamlit, PostgreSQL, Docker/Podman, OpenAI `o3-mini`, CI Status, Licença GPL-3.0).
  - Visão geral executiva com destaques arquiteturais e de produto.
  - Demonstração dos módulos:
    1. **Autenticação Multi-Tenant com Aprovação e Google OAuth**.
    2. **Importação Inteligente de Faturas PDF** com OpenAI `o3-mini` e parser multi-coluna anti-alucinação.
    3. **Assistente Financeiro com MCP Tools**.
    4. **Gestão de Contas, Transações e Compras Parceladas**.
    5. **Orçamentos e Metas Mensais**.
  - Diagrama de arquitetura Clean Architecture em ASCII/Mermaid.
  - Guia de início rápido passo a passo (Local com `uv` e Conteinerizado com Docker/Podman).
  - Tabela explicativa de todas as variáveis de ambiente (`.env`).
  - Tabela completa com as 13 ferramentas MCP documentadas com exemplos de chamadas.
  - Sumário de testes automatizados e métricas de qualidade.

- **RF-002 (Estruturação da Wiki do GitHub no Repositório)**:
  - Criar o diretório `wiki/` contendo todas as páginas markdown padrão do GitHub Wiki:
    - `Home.md`: Página inicial da Wiki com índice, visão geral e mapa de navegação.
    - `01-Arquitetura-e-Clean-Code.md`: Detalhamento dos domínios, entidades, use cases, repositórios e inversão de controle.
    - `02-Servidor-MCP-e-Ferramentas.md`: Manual de integração com Model Context Protocol para Claude Desktop, VS Code e Antigravity.
    - `03-Autenticacao-e-Multi-Tenant.md`: Fluxos de aprovação de novos cadastros por Admin, Google OAuth e segurança de senhas.
    - `04-Parser-de-Faturas-e-IA.md`: Como funciona o pipeline de extração de PDFs com OpenAI `o3-mini` e resiliência a layouts bancários.
    - `05-Guia-de-Instalacao-e-Deploy.md`: Como rodar em desenvolvimento, produção, Podman/Docker Compose e migrations com Alembic.
    - `06-Metodologia-Spec-Driven.md`: Explicação da metodologia Spec Kit utilizada no desenvolvimento de cada feature.
    - `_Sidebar.md`: Barra de navegação lateral padrão do GitHub Wiki.
    - `_Footer.md`: Rodapé padrão da Wiki com links para o repositório.

- **RF-003 (Automação de Deploy da Wiki via GitHub Actions)**:
  - Criar workflow `.github/workflows/deploy-wiki.yml`:
    - Disparado automaticamente em push na branch `main` quando houver alterações em `wiki/**`.
    - Executa ação para clonar e sincronizar o conteúdo da pasta `wiki/` diretamente no repositório `contas.wiki.git` do GitHub.

---

## Requisitos Não Funcionais
- **RNF-001 (Padrão Visual e Clareza)**: Utilizar formatação rica em Markdown, tabelas, callouts, emojis semânticos e blocos de código com highlight de sintaxe.
- **RNF-002 (Integridade Técnica)**: Informações 100% alinhadas com a implementação real do código (`uv`, `pytest`, `o3-mini`, `user_id`, `is_approved`, etc.).
