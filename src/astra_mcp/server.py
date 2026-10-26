
# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

import argparse
import asyncio
import json
from pathlib import Path

from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)

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
    async def list_tools(
        ctx: ServerRequestContext,
        params: PaginatedRequestParams | None,
    ) -> ListToolsResult:
        tools = [
            Tool(name=tool.name, description=tool.description, input_schema=json_schema(tool))
            for tool in config.tools
            if tool.enabled
        ]

        if config.enable_interactive_command_tool:
            tools.append(Tool(
                name="start_command",
                description=(
                    "Start an opt-in interactive command session. when a command may ask "
                    "one or more questions. Returns a session_id. Use read_output to inspect "
                    "prompts and send_input to provide answers. Use stop_command to stop the "
                    "session and release its associated resources."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "executable": {"type": "string", "description": "Executable name on PATH or absolute executable path."},
                        "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments, one string per argument."},
                        "cwd": {"type": "string", "description": "Optional working directory."},
                    },
                    "required": ["executable", "args"],
                    "additionalProperties": False,
                },
            ))

        if config.enable_interactive_command_tool or config.enable_interactive_shell_tool or config.enable_interactive_script_tool:
            tools.extend([
                Tool(
                    name="read_output",
                    description=(
                        "Read new output from an interactive command, interactive shell, or interactive "
                        "script session and check whether it has finished. "
                        "Accepts the session_id returned by start_command, run_interactive_shell, "
                        "or run_interactive_script."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {"session_id": {"type": "string", "description": "Session ID returned by start_command, run_interactive_shell, or run_interactive_script."}},
                        "required": ["session_id"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="send_input",
                    description=(
                        "Send arbitrary text input to a running interactive command, interactive shell, "
                        "or interactive script session. "
                        "By default, appends a newline (Enter). Set append_newline=false for "
                        "raw terminal input without appending a newline. "
                        "Do not send confirmations for consequential actions without user approval. "
                        "Accepts the session_id returned by start_command, run_interactive_shell, "
                        "or run_interactive_script."
                    ),
                    input_schema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID returned by start_command, run_interactive_shell, or run_interactive_script."},
                            "text": {"type": "string", "description": "Text or terminal input to send."},
                            "append_newline": {"type": "boolean", "description": "Append Enter after the input (default true)."},
                        },
                        "required": ["session_id", "text"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="stop_command",
                    description=(
                        "Stop an interactive command, interactive shell, or interactive script session "
                        "and release its resources. "
                        "Accepts the session_id returned by start_command, run_interactive_shell, "
                        "or run_interactive_script."

                    ),
                    input_schema={
                        "type": "object",
                        "properties": {"session_id": {"type": "string", "description": "Session ID returned by start_command, run_interactive_shell, or run_interactive_script."}},
                        "required": ["session_id"],
                        "additionalProperties": False,
                    },
                ),
            ])

        if config.enable_interactive_shell_tool:
            tools.append(Tool(
                name="run_interactive_shell",
                description=(
                    "Execute a complete script using the configured shell. Supports shell syntax "
                    "such as &&, ||, ;, pipes, redirection, variables, quoting, globbing, "
                    "subshells, command substitution, loops, functions, and shell built-ins. "
                    "This tool executes commands on the host system. "
                    "Runs the script in an interactive shell session and returns a session_id. "
                    "Use read_output to inspect output and prompts, send_input to provide input "
                    "to the running script, and stop_command to stop the process and release "
                    "its resources. The session can be interacted with while the process is running. "
                    "After it finishes, use read_output to collect remaining output "
                    "and stop_command to release session resources."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "Full shell script to execute interactively."},
                        "cwd": {"type": "string", "description": "Optional working directory."},
                    },
                    "required": ["script"],
                    "additionalProperties": False,
                },
            ))

        if config.enable_interactive_script_tool:
            tools.append(Tool(
                name="run_interactive_script",
                description=(
                    "Run complete Python, Ruby, JavaScript (Node.js), Perl, Bash, C, or C++ source code "
                    "in an interactive PTY-backed session. C/C++ source code is compiled first. "
                    "Returns a session_id. Use read_output to inspect output and prompts, "
                    "send_input to provide input to the running script, and stop_command to "
                    "stop the process and release its resources."
                ),
                input_schema={"type": "object", "properties": {
                    "language": {"type": "string", "enum": ["python", "ruby", "javascript", "perl", "bash", "c", "cpp"]},
                    "script": {"type": "string", "description": "Complete source code to execute."},
                    "cwd": {"type": "string", "description": "Optional working directory."}},
                    "required": ["language", "script"], "additionalProperties": False},
            ))

        if config.enable_dynamic_command_tool:
            tools.append(Tool(
                name="run_command",
                description=(
                    "Run an installed executable with model-selected arguments and flags. "
                    "Pass the executable separately and every argument as one string in args. "
                    "Arguments are passed directly without shell parsing."
                ),
                input_schema={
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
                input_schema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "Full shell script to execute."},
                        "cwd": {"type": "string", "description": "Optional working directory."},
                    },
                    "required": ["script"],
                    "additionalProperties": False,
                },
            ))
        return ListToolsResult(tools=tools)

    async def call_tool(
        ctx: ServerRequestContext,
        params: CallToolRequestParams,
    ) -> CallToolResult:
        name = params.name
        arguments = params.arguments or {}
        interactive_methods = {
            "start_command": executor.start_command,
            "read_output": executor.read_output,
            "send_input": executor.send_input,
            "stop_command": executor.stop_command,
            "run_interactive_shell": executor.run_interactive_shell,
            "run_interactive_script": executor.run_interactive_script,
        }
        if name in interactive_methods:
            if name == "run_interactive_script":
                if not config.enable_interactive_script_tool:
                    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Interactive script execution is disabled"}))])
            elif name == "run_interactive_shell":
                if not config.enable_interactive_shell_tool:
                    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Interactive shell execution is disabled"}))])
            elif name == "start_command":
                if not config.enable_interactive_command_tool:
                    return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Interactive command execution is disabled"}))])
            elif not (config.enable_interactive_command_tool or config.enable_interactive_shell_tool or config.enable_interactive_script_tool):
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Interactive sessions are disabled"}))])
            try:
                result = await interactive_methods[name](arguments)
                return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))])
            except Exception as error:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))])
        if name == "run_shell":
            if not config.enable_shell_tool:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Shell execution is disabled"}))])
            try:
                result = await executor.run_shell(arguments)
                return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))])
            except Exception as error:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))])
        if name == "run_command":
            if not config.enable_dynamic_command_tool:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Dynamic command execution is disabled"}))])
            try:
                result = await executor.run_dynamic(arguments)
                return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))])
            except Exception as error:
                return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))])
        tool = next((item for item in config.tools if item.name == name), None)
        if tool is None:
            return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))])
        try:
            result = await executor.run(tool, arguments)
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))])
        except Exception as error:
            return CallToolResult(content=[TextContent(type="text", text=json.dumps({"error": str(error), "type": type(error).__name__}))])

    return Server(
        "astra-mcp",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def _run(config_path: str | Path | None = None) -> None:
    server = create_server(config_path)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="astra",
        description="ASTRA MCP: A configuration-driven Model Context Protocol server for Linux that executes command-line tools and shell scripts, supports interactive shell sessions, and runs interactive scripts in multiple programming languages.",
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
