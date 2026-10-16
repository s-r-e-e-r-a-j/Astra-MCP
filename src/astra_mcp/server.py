
# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

import argparse
import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from astra_mcp import __version__
from astra_mcp.config import ToolConfig, config_path_from_environment, load_config
from astra_mcp.executor import ToolExecutor


def json_schema(tool: ToolConfig) -> dict[str, object]:
    properties: dict[str, object] = {}
    required: list[str] = []
    for parameter in tool.parameters:
        properties[parameter.name] = {
            "type": parameter.kind,
            "description": parameter.description,
        }
        if parameter.required:
            required.append(parameter.name)
    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema




def create_server(config_path: str | Path | None = None) -> Server:
    path = Path(config_path) if config_path else config_path_from_environment()
    config = load_config(path)
    executor = ToolExecutor(config)
    server = Server("astra-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = [
            Tool(name=tool.name, description=tool.description, inputSchema=json_schema(tool))
            for tool in config.tools
            if tool.enabled
        ]
        if config.enable_dynamic_command_tool:
            tools.append(Tool(
                name="run_command",
                description=(
                    "Run an installed executable with model-selected arguments and flags. "
                    "Pass the executable separately and every argument as one string in args. "
                    "Arguments are passed directly without shell parsing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "executable": {"type": "string", "description": "Executable name on PATH or absolute executable path."},
                        "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments and flags, one string per argument."},
                    },
                    "required": ["executable", "args"],
                    "additionalProperties": False,
                },
            ))
        if config.enable_shell_tool:
            tools.append(Tool(
                name="run_shell",
                description=(
                    "Execute a complete script using the configured shell. Supports shell syntax "
                    "such as &&, ||, ;, pipes, redirection, variables, quoting, globbing, "
                    "subshells, command substitution, loops, functions, and shell built-ins. "
                    "This tool executes commands on the host system."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "Full shell script to execute."},
                        "cwd": {"type": "string", "description": "Optional working directory."},
                    },
                    "required": ["script"],
                    "additionalProperties": False,
                },
            ))
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, object]) -> list[TextContent]:
        if name == "run_shell":
            if not config.enable_shell_tool:
                return [TextContent(type="text", text=json.dumps({"error": "Shell execution is disabled"}))]
            try:
                result = await executor.run_shell(arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            except Exception as error:
                return [TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))]
        if name == "run_command":
            if not config.enable_dynamic_command_tool:
                return [TextContent(type="text", text=json.dumps({"error": "Dynamic command execution is disabled"}))]
            try:
                result = await executor.run_dynamic(arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            except Exception as error:
                return [TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))]
        tool = next((item for item in config.tools if item.name == name), None)
        if tool is None:
            return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]
        try:
            result = await executor.run(tool, arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        except Exception as error:
            return [TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))]

    return server


async def _run(config_path: str | Path | None = None) -> None:
    server = create_server(config_path)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="astra",
        description="ASTRA MCP configuration-driven command-line tool server",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="path to the tools TOML configuration file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)
    try:
        asyncio.run(_run(args.config))
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        parser.exit(1, f"{parser.prog}: error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
