import sys

from mcp.server.mcpserver import MCPServer

from contas.tools.accounts import register_account_tools
from contas.tools.budgets import register_budget_tools
from contas.tools.categories import register_category_tools
from contas.tools.health import register_health_tools
from contas.tools.transactions import register_transaction_tools


def create_server() -> MCPServer:
    mcp = MCPServer("contas-server")
    register_account_tools(mcp)
    register_category_tools(mcp)
    register_budget_tools(mcp)
    register_transaction_tools(mcp)
    register_health_tools(mcp)
    return mcp


def main() -> None:
    import logging

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
