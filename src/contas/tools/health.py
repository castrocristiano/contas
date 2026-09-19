from datetime import UTC, datetime

from mcp.server.mcpserver import MCPServer
from sqlalchemy import text

from contas.db.session import get_session


def register_health_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def health_check() -> dict:
        """Check operational readiness and database connectivity."""
        now = datetime.now(UTC).isoformat()
        try:
            async with get_session() as session:
                await session.exec(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "server": "contas-server",
                "version": "0.1.0",
                "checked_at": now,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(exc),
                "server": "contas-server",
                "version": "0.1.0",
                "checked_at": now,
            }
