# 🚀 05. Guia de Instalação e Deploy

O **Contas** foi projetado para execução simples tanto em ambiente de desenvolvimento quanto em produção conteinerizada.

---

## 📦 Opção 1: Execução com Docker / Podman Compose

Esta é a opção recomendada para subir o ambiente completo (Banco de Dados PostgreSQL e Frontend Streamlit) de forma isolada e reprodutível.

### Passo 1: Clonar o projeto e configurar `.env`
```bash
git clone git@github.com:castrocristiano/contas.git
cd contas
cp .env.example .env
```
Edite o arquivo `.env` para informar sua chave da OpenAI e credenciais do banco.

### Passo 2: Subir os containers
```bash
# Com Docker:
docker compose up --build -d

# Ou com Podman:
podman-compose up --build -d
```

O container da aplicação executa automaticamente as migrações do banco com Alembic na inicialização e expõe a porta `8501`.

Acesse no navegador: **`http://localhost:8501`**.

---

## 💻 Opção 2: Execução Local Nativa com `uv`

Ideal para desenvolvimento ativo e depuração de código:

### 1. Pré-requisitos
- Python 3.12 ou superior
- [uv](https://github.com/astral-sh/uv) (gerenciador de dependências)

### 2. Instalação de Dependências
```bash
uv sync
```

### 3. Iniciar o Banco PostgreSQL
Você pode rodar uma instância local do PostgreSQL ou subir apenas o container do banco:
```bash
docker compose up db -d  # ou: podman-compose up db -d
```

### 4. Executar Migrações do Banco
```bash
uv run alembic upgrade head
```

### 5. Iniciar a Aplicação
```bash
uv run streamlit run src/contas/ui/app.py
```

---

## 🧪 Suíte de Testes e Linters

Para garantir que tudo esteja funcionando corretamente:

```bash
# Executar todos os testes
uv run pytest

# Executar verificação de linters
uv run ruff check

# Verificar formatação de código
uv run ruff format --check
```
