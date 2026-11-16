# Bem-vindo à Wiki do Contas 💰

O **Contas** é um sistema completo de gestão financeira pessoal e residencial desenvolvido com os mais modernos padrões de Engenharia de Software, incluindo **Clean Architecture**, **Model Context Protocol (MCP)**, **OpenAI gpt-4o**, autenticação centralizada com **Keycloak 26 (OpenID Connect)**, isolamento multi-tenant com **aprovação de novos usuários por administrador** e esteira automatizada de CI/CD com **SonarQube**.

Esta Wiki foi estruturada para detalhar cada aspecto arquitetural, de segurança, de inteligência artificial, de infraestrutura e de fluxo de desenvolvimento (Gitflow) do projeto.

---

## 🗺️ Mapa de Navegação da Wiki

Para explorar os detalhes do sistema, navegue pelos capítulos abaixo ou utilize o menu lateral:

1. [🏛️ **01. Arquitetura & Clean Code**](01-Arquitetura-e-Clean-Code)
   - Princípios da Clean Architecture (Hexagonal / Onion).
   - Camadas de Domínio, Casos de Uso, Portas e Repositórios.
   - Regras de integridade financeira: por que usamos `Decimal` e proibimos `float`.
   - Inversão de Controle e Dependency Container.

2. [🔌 **02. Servidor MCP e Ferramentas**](02-Servidor-MCP-e-Ferramentas)
   - O que é o Model Context Protocol (MCP) e por que adotá-lo.
   - Catálogo completo das 14 ferramentas expostas para LLMs (incluindo `clear_transaction`).
   - Como conectar o servidor ao Claude Desktop, Cursor e Antigravity.
   - Schemas de validação estritos com Pydantic v2.

3. [🔐 **03. Autenticação, Keycloak e Multi-Tenant**](03-Autenticacao-e-Multi-Tenant)
   - Isolamento estrito de dados entre usuários por `user_id`.
   - Integração com **Keycloak 26 (OpenID Connect / SSO & Direct Grant)** na porta `8180`.
   - Fluxo de Aprovação Prévia de Novos Usuários e mapeamento da role `admin`.
   - Criptografia e segurança de senhas locais com `bcrypt`.

4. [🧾 **04. Parser de Faturas e IA**](04-Parser-de-Faturas-e-IA)
   - Pipeline de extração de PDFs com o modelo **OpenAI `gpt-4o`** e seleção dinâmica de modelos.
   - Pré-processamento linear em Python para isolamento de transações concatenadas e colunas paralelas.
   - Resiliência a layouts bancários complexos (Nubank, Inter, Itaú, etc.) e compras parceladas de meses anteriores.
   - Defesas anti-alucinação e validação matemática de somas.

5. [🚀 **05. Guia de Instalação e Deploy**](05-Guia-de-Instalacao-e-Deploy)
   - Orquestração completa com Podman Compose e Docker Compose (PostgreSQL + Keycloak + App).
   - Atualização automatizada do servidor remoto via `./update_remote.sh`.
   - Passo a passo para execução local com `uv` e migrações com Alembic.

6. [📐 **06. Metodologia Spec-Driven**](06-Metodologia-Spec-Driven)
   - Como o projeto é guiado pela metodologia Spec Kit (`specs/001` a `024`).
   - Ciclo de vida: Especificação (`spec.md`), Planejamento (`plan.md`), Tarefas (`tasks.md`) e Implementação.
   - Skills e Regras do Agente (`.agents/skills/formatter` e `.agents/rules/formatter.md`).

7. [🔄 **07. Gitflow, CI/CD e Qualidade (SonarQube & Go Runner)**](07-Gitflow-e-CI-CD)
   - Estratégia de branches (`main`, `develop`, `feature/*`, `phase/*` e `hotfix/*`).
   - Ferramenta unificada de CI/CD em Go (`contas-ci`) executável nativamente ou via container Podman isolado.
   - Fluxo de Pull Requests automatizados (`feature/* → develop → main` e `hotfix/* → main`).
   - Geração automática de Releases no GitHub e Quality Gate do SonarQube (`SONAR_TOKEN`).

---

## 💡 Informações Rápidas

- **Autor**: [Cristiano Castro](https://github.com/castrocristiano)
- **Linguagem**: Python 3.12+ & Go 1.23+ (CI/CD Tooling)
- **Protocolo de IA**: Model Context Protocol (MCP)
- **Identidade & Auth**: Keycloak 26 (OIDC) + bcrypt
- **Interface**: Streamlit
- **Banco de Dados**: PostgreSQL 16
- **Conteinerização**: Podman / Docker
- **Licença**: GNU GPLv3
