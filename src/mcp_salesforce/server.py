"""
MCP server entrypoint for Salesforce tools.
"""

from mcp.server.fastmcp import FastMCP

from mcp_salesforce.tools.appointments import register_salesforce_tools


def create_server() -> FastMCP:
    """
    Create and configure the MCP server instance.

    Returns:
        FastMCP: Configured MCP server with Salesforce tools registered.
    """
    mcp: FastMCP = FastMCP("mcp-salesforce")
    register_salesforce_tools(mcp)
    return mcp


def main() -> None:
    """
    Run the MCP server
    """
    server: FastMCP = create_server()
    server.run()


if __name__ == "__main__":
    main()
