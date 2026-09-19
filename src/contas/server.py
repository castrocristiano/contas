import sys

from mcp.server.mcpserver import MCPServer


def create_server() -> MCPServer:
    mcp = MCPServer("contas-server")
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
