# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
import os
import shutil
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import uvicorn
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server import Server, ServerRequestContext
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
)


TUNNEL_URL_FILE = Path(__file__).with_name("tunnel_url.txt")


def monitor_tunnel_url(allowed_hosts: list[str]) -> None:
    last_url = None

    while True:
        try:
            url = TUNNEL_URL_FILE.read_text(encoding="utf-8").strip()

            if url and url != last_url:
                parsed = urlparse(url)
                hostname = parsed.hostname

                if (
                    parsed.scheme in ("http", "https")
                    and hostname
                    and not parsed.username
                    and not parsed.password
                ):
                    hostname = hostname.lower()

                    if hostname not in ("localhost", "127.0.0.1", "::1"):
                        for host in (hostname, f"{hostname}:*"):
                            if host not in allowed_hosts:
                                allowed_hosts.append(host)

                        last_url = url

        except (OSError, ValueError):
            pass

        time.sleep(1)

def build_bridge() -> Any:
    state: dict[str, Any] = {}

    @asynccontextmanager
    async def lifespan(_server: Server) -> AsyncIterator[dict[str, Any]]:
        env = {}
        config_path = os.environ.get("ASTRA_MCP_CONFIG")

        if config_path:
           env["ASTRA_MCP_CONFIG"] = config_path

        astra_path = shutil.which("astra")
        if not astra_path:
           raise RuntimeError("Could not find 'astra' on PATH")

        params = StdioServerParameters(
                 command=astra_path,
                 args=[],
                 env=env,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                state["session"] = session
                try:
                    yield {"upstream_session": session}
                finally:
                    state.pop("session", None)

    async def list_tools(
        ctx: ServerRequestContext,
        params: PaginatedRequestParams | None,
    ) -> ListToolsResult:
        session = state.get("session")
        if session is None:
            raise RuntimeError("The upstream stdio MCP server is not connected")
        return await session.list_tools()

    async def call_tool(
        ctx: ServerRequestContext,
        params: CallToolRequestParams,
    ) -> CallToolResult:
        session = state.get("session")
        if session is None:
            raise RuntimeError("The upstream stdio MCP server is not connected")
        return await session.call_tool(
            params.name,
            params.arguments or {},
        )

    server = Server(
        "astra-stdio-http-bridge",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        lifespan=lifespan,
    )

    host_allowlist = [
        "127.0.0.1:*",
        "localhost:*",
        "[::1]:*",
    ]

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=host_allowlist,
        allowed_origins=[],
    )

    threading.Thread(
       target=monitor_tunnel_url,
       args=(security.allowed_hosts,),
       daemon=True,
    ).start()

    return server.streamable_http_app(
        streamable_http_path="/mcp",
        host="127.0.0.1",
        transport_security=security,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = build_bridge()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
