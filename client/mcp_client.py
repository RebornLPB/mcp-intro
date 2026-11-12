"""Small helpers to talk to the Programming Learning MCP server.

The client starts the server itself as a subprocess (stdio transport),
so nothing needs to be running before using it.
"""

from pathlib import Path

from fastmcp import Client

# Build the path from this file's location, so it works from any directory.
SERVER_PATH = Path(__file__).resolve().parent.parent / "server" / "learning_server.py"


def create_client() -> Client:
    """Create an MCP client that launches the server script over stdio."""
    return Client(SERVER_PATH)


async def call_tool(client: Client, name: str, arguments: dict):
    """Call an MCP tool and return its data (a dict or a list)."""
    result = await client.call_tool(name, arguments)
    return result.data
