# Bem-vindo à Wiki do Contas 💰

O **Contas** é um sistema completo de gestão financeira pessoal e residencial desenvolvido com os mais modernos padrões de Engenharia de Software, incluindo **Clean Architecture**, **Model Context Protocol (MCP)**, **OpenAI o3-mini**, autenticação multi-tenant com **aprovação de novos usuários por administrador** e conteinerização.

Esta Wiki foi estruturada para detalhar cada aspecto arquitetural, de segurança, de inteligência artificial e de infraestrutura do projeto, servindo como documentação de referência técnica.

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
   - Catálogo completo das 13 ferramentas expostas para LLMs.
   - Como conectar o servidor ao Claude Desktop, Cursor e Antigravity.
   - Schemas de validação estritos com Pydantic v2.

3. [🔐 **03. Autenticação e Multi-Tenant**](03-Autenticacao-e-Multi-Tenant)
   - Isolamento estrito de dados entre usuários por `user_id`.
   - Fluxo de Aprovação Prévia de Novos Usuários pelo Administrador.
   - Integração com Google OAuth 2.0 Web Flow.
   - Criptografia e segurança de senhas com `bcrypt`.
   - Gerenciamento e redefinição de senhas.

4. [🧾 **04. Parser de Faturas e IA**](04-Parser-de-Faturas-e-IA)
   - Pipeline de extração de PDFs com o modelo **OpenAI `o3-mini`**.
   - Pré-filtragem local em Python para redução de tokens e ruídos.
   - Resiliência a layouts multi-coluna de bancos brasileiros (Nubank, Inter, Itaú, etc.).
   - Defesas anti-alucinação e validação matemática de somas.

5. [🚀 **05. Guia de Instalação e Deploy**](05-Guia-de-Instalacao-e-Deploy)
   - Passo a passo para execução local com `uv`.
   - Orquestração completa com Podman Compose e Docker Compose.
   - Gestão de banco relacional e migrações com Alembic.
   - Configuração detalhada do arquivo `.env`.

6. [📐 **06. Metodologia Spec-Driven**](06-Metodologia-Spec-Driven)
   - Como o projeto é guiado pela metodologia Spec Kit.
   - Ciclo de vida: Especificação (`spec.md`), Planejamento (`plan.md`), Tarefas (`tasks.md`) e Implementação.
   - Constituição do projeto e convenções de código.

---

## 💡 Informações Rápidas

- **Autor**: [Cristiano Castro](https://github.com/castrocristiano)
- **Linguagem**: Python 3.12+
- **Protocolo de IA**: Model Context Protocol (MCP)
- **Interface**: Streamlit
- **Banco de Dados**: PostgreSQL 16
- **Licença**: GNU GPLv3
