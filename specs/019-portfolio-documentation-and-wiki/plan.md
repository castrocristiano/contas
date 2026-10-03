# Plano de Arquitetura e Implementação - Feature 019: GitHub Wiki & Documentação de Portfólio

## 1. Visão Geral
Transformar a documentação do projeto **Contas** em uma vitrine de engenharia de software de nível sênior, detalhando a arquitetura limpa, o uso de IA com MCP e as práticas de testes automatizados e segurança.

---

## 2. Componentes e Entregas

### 2.1 README.md Principal
- Badges modernos de qualidade.
- Apresentação executiva para recrutadores, tech leads e desenvolvedores.
- Diagrama Mermaid da Clean Architecture e fluxo de dados.
- Recursos em destaque com capturas conceituais/tabelas.
- Setup rápido via Docker/Podman e setup nativo com `uv`.
- Tabela exaustiva das 13 ferramentas MCP.

### 2.2 GitHub Wiki (`wiki/`)
- Diretório `wiki/` pronto para deploy no GitHub Wiki:
  - `Home.md`
  - `01-Arquitetura-e-Clean-Code.md`
  - `02-Servidor-MCP-e-Ferramentas.md`
  - `03-Autenticacao-e-Multi-Tenant.md`
  - `04-Parser-de-Faturas-e-IA.md`
  - `05-Guia-de-Instalacao-e-Deploy.md`
  - `06-Metodologia-Spec-Driven.md`
  - `_Sidebar.md`
  - `_Footer.md`

### 2.3 Workflow de Automação CI/CD
- `.github/workflows/deploy-wiki.yml`:
  - Utiliza `Andrew-Chen-Wang/github-wiki-action@v4` ou script git para enviar as páginas de `wiki/` para o repositório `https://github.com/castrocristiano/contas.wiki.git`.
