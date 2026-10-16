# Developer: Sreeraj
# GitHub: https://github.com/s-r-e-e-r-a-j

import asyncio
import os
import shutil
from pathlib import Path

from astra_mcp.config import ServerConfig, ToolConfig
from astra_mcp.policy import expand_argument, validate_arguments, validate_host, validate_path, validate_url_host
from astra_mcp.audit import write_audit


class ToolExecutor:
    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrency)

    def _build(self, tool: ToolConfig, raw_arguments: object) -> tuple[list[str], str | None]:
        arguments = validate_arguments(tool, raw_arguments)
        executable = shutil.which(tool.executable) if not Path(tool.executable).is_absolute() else tool.executable
        if not executable or not Path(executable).is_file():
            raise FileNotFoundError(f"Executable not found: {tool.executable}")
        command = [executable]
        for template in tool.fixed_args:
            expanded = expand_argument(template, arguments)
            for parameter in tool.parameters:
                if parameter.kind == "string" and parameter.name in arguments:
                    value = str(arguments[parameter.name])
                    if "{"+parameter.name+"}" in template and parameter.name in {"path", "file", "directory", "repo", "output"}:
                        if parameter.name == "output" and not tool.allowed_paths:
                            raise ValueError("Output paths require configured allowed_paths")
                        if tool.allowed_paths:
                            validate_path(value, tool.allowed_paths)
                    if "{"+parameter.name+"}" in template and parameter.name in {"url", "uri"}:
                        validate_url_host(value, tool.allowed_hosts)
                    if "{"+parameter.name+"}" in template and parameter.name in {"target", "host"}:
                        validate_host(value, tool.allowed_hosts)
            command.append(expanded)
        working_directory = None
        if tool.working_directory:
            working_directory = expand_argument(tool.working_directory, arguments)
            working_directory = str(validate_path(working_directory, tool.allowed_paths))
        return command, working_directory

    async def run_dynamic(self, raw_arguments: object) -> dict[str, object]:
        if not self.config.enable_dynamic_command_tool:
            raise PermissionError("Dynamic command execution is disabled")
        if not isinstance(raw_arguments, dict):
            raise ValueError("Arguments must be an object")
        if set(raw_arguments) - {"executable", "args"}:
            raise ValueError("Only executable and args are accepted")
        executable_value = raw_arguments.get("executable")
        args_value = raw_arguments.get("args", [])
        if not isinstance(executable_value, str) or not executable_value.strip():
            raise ValueError("executable must be a non-empty string")
        if not isinstance(args_value, list) or not all(isinstance(arg, str) for arg in args_value):
            raise ValueError("args must be a list of strings")
        values = [executable_value, *args_value]
        if any("\x00" in value or "\r" in value or "\n" in value for value in values):
            raise ValueError("Command arguments cannot contain NUL or newline characters")
        executable = (executable_value if Path(executable_value).is_absolute()
                      else shutil.which(executable_value))
        if not executable or not Path(executable).is_file():
            raise FileNotFoundError(f"Executable not found: {executable_value}")
        command = [executable, *args_value]
        async with self.semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=None,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={key: value for key, value in os.environ.items()
                         if key in {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TERM"}},
                )
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=self.config.default_timeout_seconds
                    )
                except TimeoutError:
                    process.kill()
                    await process.communicate()
                    raise TimeoutError(
                        f"Dynamic command timed out after {self.config.default_timeout_seconds} seconds"
                    )
                limit = self.config.max_output_bytes
                result = {
                    "exit_code": process.returncode,
                    "stdout": stdout[:limit].decode("utf-8", errors="replace"),
                    "stderr": stderr[:limit].decode("utf-8", errors="replace"),
                    "truncated": len(stdout) > limit or len(stderr) > limit,
                }
                write_audit(self.config.audit_log, {
                    "tool": "run_command", "executable": executable_value,
                    "args": args_value, "exit_code": process.returncode,
                })
                return result
            except Exception as error:
                write_audit(self.config.audit_log, {
                    "tool": "run_command", "executable": executable_value,
                    "args": args_value, "error": type(error).__name__,
                })
                raise

    async def run_shell(self, raw_arguments: object) -> dict[str, object]:
        if not self.config.enable_shell_tool:
            raise PermissionError("Shell execution is disabled")
        if not isinstance(raw_arguments, dict):
            raise ValueError("Arguments must be an object")
        if set(raw_arguments) - {"script", "cwd"}:
            raise ValueError("Only script and cwd are accepted")
        script = raw_arguments.get("script")
        cwd_value = raw_arguments.get("cwd")
        if not isinstance(script, str) or not script.strip():
            raise ValueError("script must be a non-empty string")
        if "\\x00" in script:
            raise ValueError("Shell script cannot contain NUL characters")
        if cwd_value is not None and not isinstance(cwd_value, str):
            raise ValueError("cwd must be a string when provided")

        shell = self.config.shell_executable
        shell_path = shell if Path(shell).is_absolute() else shutil.which(shell)
        if not shell_path or not Path(shell_path).is_file():
            raise FileNotFoundError(f"Shell executable not found: {shell}")
        cwd = None
        if cwd_value:
            cwd = str(Path(cwd_value).expanduser().resolve())
            if not Path(cwd).is_dir():
                raise NotADirectoryError(f"Working directory not found: {cwd}")

        env = {key: value for key, value in os.environ.items()
               if key in {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TMPDIR"}}
        async with self.semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    shell_path, "-c", script,
                    cwd=cwd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    start_new_session=True,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=self.config.default_timeout_seconds
                    )
                except TimeoutError:
                    try:
                        os.killpg(process.pid, 9)
                    except (ProcessLookupError, PermissionError):
                        process.kill()
                    await process.communicate()
                    raise TimeoutError(
                        f"Shell command timed out after {self.config.default_timeout_seconds} seconds"
                    )
                limit = self.config.max_output_bytes
                result = {
                    "exit_code": process.returncode,
                    "stdout": stdout[:limit].decode("utf-8", errors="replace"),
                    "stderr": stderr[:limit].decode("utf-8", errors="replace"),
                    "truncated": len(stdout) > limit or len(stderr) > limit,
                    "shell": Path(shell_path).name,
                }
                write_audit(self.config.audit_log, {
                    "tool": "run_shell", "script": script, "cwd": cwd,
                    "exit_code": process.returncode,
                })
                return result
            except Exception as error:
                write_audit(self.config.audit_log, {
                    "tool": "run_shell", "script": script, "cwd": cwd,
                    "error": type(error).__name__,
                })
                raise

    async def run(self, tool: ToolConfig, raw_arguments: object) -> dict[str, object]:
        if not tool.enabled:
            raise PermissionError(f"Tool is disabled: {tool.name}")
        command, working_directory = self._build(tool, raw_arguments)
        async with self.semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=working_directory,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TERM"}},
                )
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=tool.timeout_seconds)
                except TimeoutError:
                    process.kill()
                    await process.communicate()
                    raise TimeoutError(f"Tool timed out after {tool.timeout_seconds} seconds")
                limit = self.config.max_output_bytes
                output = stdout[:limit].decode("utf-8", errors="replace")
                error = stderr[:limit].decode("utf-8", errors="replace")
                result = {"exit_code": process.returncode, "stdout": output, "stderr": error, "truncated": len(stdout) > limit or len(stderr) > limit}
                write_audit(self.config.audit_log, {"tool": tool.name, "arguments": raw_arguments, "exit_code": process.returncode})
                return result
            except Exception as error:
                write_audit(self.config.audit_log, {"tool": tool.name, "arguments": raw_arguments, "error": type(error).__name__})
                raise
