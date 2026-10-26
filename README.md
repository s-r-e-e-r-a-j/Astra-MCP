# ASTRA MCP

ASTRA MCP is a powerful MCP server that connects AI assistants to your Linux system. It allows AI assistants to run regular and interactive command-line programs, create and execute regular and interactive shell scripts, and create and run interactive and non-interactive scripts written in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++.

ASTRA supports six ways to run commands:

- **Configured tools:** You define each tool in `tools.toml`. ASTRA runs the program with separate command-line arguments, without using a shell.
- **`run_command`:** An optional tool that lets the AI choose a program and provide its command-line arguments, without using a shell.
- **`run_shell`:** An optional tool that allows the AI to create and run shell scripts. It supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), and variables.
- **Interactive commands:** An optional feature that lets the AI dynamically choose an executable and provide its command-line arguments through `start_command`. The AI can also specify an optional working directory using `cwd`. It can then read output using `read_output`, send input using `send_input`, and stop the program using `stop_command`. These tools use a session ID to interact with the same running process.
- **`run_interactive_shell`:** An optional tool that lets the AI create and run shell scripts. It supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), variables, and more. It runs scripts in an interactive shell session and returns a session ID. The AI can inspect output, respond to prompts, send input to the running script, and stop the process using `read_output`, `send_input`, and `stop_command`. It supports scripts that require interactive input, including terminal menus and editors such as `nano`, `vi`, and `vim`.	
- **`run_interactive_script`:** An optional tool that allows the AI to create and run complete source code in an interactive terminal session. Supported languages are Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. It supports both interactive scripts that require input while running and non-interactive scripts that execute without additional input. ASTRA automatically compiles C and C++ source code before execution. The tool returns a session ID that the AI can use with `read_output`, `send_input`, and `stop_command` to interact with or stop the running process. The required language runtimes and compilers must be installed on the system.

The `run_command`, `run_shell`, `run_interactive_shell`, `run_interactive_script`, and interactive command features are disabled by default. You can enable each feature separately in the `[server]` section of `tools.toml`.

For configured tools, ASTRA reads the settings in `tools.toml` and creates an MCP tool with a matching JSON input schema. When the AI calls a tool, ASTRA checks the input, runs the command, and returns the result.

## Features

- Add command-line tools in `tools.toml`. You do not need to write a separate Python wrapper for every program.
- Optionally expose a generic `run_command` MCP tool so the AI can choose an executable and provide an argument list at call time, without defining a separate tool schema for each command.
- Optionally, enable `run_shell` so the AI can create and run shell scripts and combine commands.
- Use shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), and variables when using `run_shell`.
- Choose which shell ASTRA uses with the `shell_executable` setting.
- **Interactive command sessions:** Optionally enable `start_command`, `read_output`, `send_input`, and `stop_command` so the AI can start programs, read their output, send input, and stop running processes using session IDs.
- **Session management:** Keep interacting with a running process across multiple tool calls without restarting it.
- **Interactive multi-language script execution:** Create and run AI-generated scripts in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. Supports both interactive scripts that require input while running and non-interactive scripts that run without additional input. C and C++ scripts are automatically compiled before execution.
- **Interactive shell sessions:** Optionally enable `run_interactive_shell` to allow the AI to create and execute shell scripts that may require input while running. Use the returned session ID with `read_output`, `send_input`, and `stop_command` to interact with the same process.
- Show enabled tools to an AI client that supports MCP.
- Create JSON schemas from the parameters you set for each tool.
- Check required inputs, data types, unknown input names, and some unsafe characters.
- Run programs directly without using `sh`, `bash`, or `shell=True`.
- Set a time limit for each tool.
- Limit how many tools can run at once.
- Limit how much output ASTRA returns.
- Save records of tool calls in a JSON-lines audit log.
- Limit working directories and certain path placeholders. You can also allow only selected URL or target hosts when you configure them.
- **Dual transport support:** Supports the standard stdio transport and Streamable HTTP through the optional ASTRA bridge.
- **Streamable HTTP endpoint:** Exposes the MCP server over HTTP at `/mcp`, using `http://127.0.0.1:8000/mcp` by default.
- **Optional HTTP bridge:** Runs ASTRA as a subprocess and provides an HTTP interface for MCP clients that require Streamable HTTP transport.
- **Host security:** Uses MCP transport host validation with DNS rebinding protection enabled.
- Choose the configuration file and audit-log file with environment variables.
- Use `astra --help`, `astra --version`, and `astra --config`.

## Requirements

- Linux
- Python 3.13 or newer
- The command-line programs you want ASTRA to run
- An MCP-compatible client
- An internet connection to install Python packages, unless the packages are already available

Make sure your MCP client starts ASTRA using the executable from the Python environment where ASTRA is installed.

## Compatibility

Choose the Astra-MCP version that matches your MCP Python SDK version to avoid compatibility issues.

- **MCP Python SDK `< 2.0.0`:** Use `Astra-MCP v1.3.0-Stable`, compatible with SDK 1.x.x clients.
- MCP Python SDK `>= 2.0.0`, `< 3.0.0`: Use `Astra-MCP v1.4.0-Stable` or `Astra-MCP v1.5.0-Stable`, compatible with SDK `2.x.x` clients. `Astra-MCP v1.5.0-Stable` additionally supports the optional Streamable HTTP bridge for clients connecting over HTTP and introduces the optional `run_interactive_script` tool for executing interactive and non-interactive scripts in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++, with automatic compilation of C and C++ source code.

## 1. Get the project

```bash
git clone https://github.com/s-r-e-e-r-a-j/Astra-MCP.git
cd Astra-MCP
```

## 2. Install ASTRA

Run these commands from the project folder:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

These commands create a virtual environment, turn it on, update `pip`, and install ASTRA.

If the `python3.13` command is not available, install Python 3.13 or a newer version first. ASTRA requires Python 3.13 or newer.

Check that ASTRA is installed by running:

```bash
astra --help
astra --version
```

## 3. Choose the configuration file

By default, ASTRA looks for `tools.toml` in the folder where it is started. To use a different file, pass its path with `--config`:

```bash
astra --config /absolute/path/to/tools.toml
```

You can also choose the file by setting the `ASTRA_MCP_CONFIG` environment variable:

```bash
export ASTRA_MCP_CONFIG='/absolute/path/to/tools.toml'
astra
```

If you use `--config`, ASTRA uses that path instead of the path set by `ASTRA_MCP_CONFIG`.

Use an absolute path in your MCP client settings. This helps ASTRA find the file even if the client starts ASTRA from a different folder.

## 4. Understand how ASTRA runs

ASTRA uses MCP **stdio** transport. This means the MCP client starts ASTRA as a program and communicates with it through standard input and standard output.

For tools defined in `tools.toml`, the AI sends arguments in JSON format. ASTRA checks the arguments against each tool's parameter settings, fills in placeholders in `fixed_args`, and starts the program with each argument kept separate. ASTRA does not run these commands through a shell.

You can also enable `run_command` by setting `enable_dynamic_command_tool = true` in the `[server]` section of `tools.toml`. The AI can then choose a program and send its arguments in an `args` list. You do not need to add a separate tool entry for every program. For example, `executable = "git"` and `args = ["status", "--short"]` run `git status --short`.

You can enable the optional `run_shell` tool by setting `enable_shell_tool = true` in the `[server]` section of `tools.toml`. This lets the AI create and run shell scripts using the shell specified by `shell_executable`. It supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), and variables. The tool is disabled by default.

You can enable the optional `run_interactive_shell` tool by setting `enable_interactive_shell_tool = true` in the `[server]` section of `tools.toml`. This allows the AI to create and run a complete shell script using the shell specified by `shell_executable` and supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), variables, and other shell syntax. 
Unlike `run_shell`, `run_interactive_shell` runs the script in an interactive shell session and returns a session ID. The AI can use `read_output` to inspect output and prompts, `send_input` to provide input to the running script, and `stop_command` to stop the process and release its resources. These session-control tools use the session ID returned by `run_interactive_shell`. The interactive shell tool is disabled by default.

You can also enable the optional interactive command tools by setting `enable_interactive_command_tool = true` in the `[server]` section of `tools.toml`. When calling `start_command`, the AI can provide the `executable` to run, an `args` list containing the command-line arguments, and an optional `cwd` working directory. This lets the AI choose the program and its arguments at runtime. The `start_command` tool starts the program and returns a session ID. The AI uses this ID to interact with the same running program through `read_output`, `send_input`, and `stop_command`. These tools let the AI read output, respond to prompts, send more input, and stop the program when finished. The interactive command tools are disabled by default.

You can also enable the optional `run_interactive_script` tool by setting `enable_interactive_script_tool = true` in the `[server]` section of `tools.toml`. This allows the AI to create and execute scripts written in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. It supports both interactive scripts that require input while running and non-interactive scripts that execute without requiring additional input. ASTRA automatically compiles C and C++ scripts before execution. The tool runs each script in a session and returns a session ID. The AI can use `read_output` to inspect output and prompts, `send_input` to provide input or respond to prompts, and `stop_command` to stop the running process and release its resources. The necessary language runtimes and compilers must be installed on the Linux host. The interactive script tool is disabled by default.

While the MCP server is running, do not send normal print messages or debug messages to standard output. They can interfere with communication between ASTRA and the MCP client.

## 5. Configure the `[server]` section

The `[server]` section sets limits that apply to all ASTRA tools. Here is an example:

```toml
[server]
default_timeout_seconds = 30
max_timeout_seconds = 120
max_output_bytes = 200000
max_concurrency = 4
enable_dynamic_command_tool = false
enable_interactive_command_tool = false
enable_shell_tool = false
enable_interactive_shell_tool = false
enable_interactive_script_tool = false
shell_executable = "/bin/bash"
audit_log = "./audit.jsonl"
```

| Setting | What it means |
|---|---|
| `default_timeout_seconds` | The default number of seconds ASTRA allows a tool to run when that tool does not have its own timeout. The value must be at least `1` and cannot be greater than `max_timeout_seconds`. |
| `max_timeout_seconds` | The longest time a tool is allowed to run. The value must be at least `1`. A tool's own timeout cannot be higher than this value. |
| `max_output_bytes` | The maximum number of bytes ASTRA keeps from standard output and standard error in the returned result. The limit applies separately to each one. The value must be at least `1`. ASTRA currently captures all process output before cutting it down, so this setting does not fully limit memory use. |
| `max_concurrency` | The maximum number of tool calls ASTRA allows to run at the same time. The value must be at least `1`. |
| `enable_dynamic_command_tool` | When `true`, exposes the generic `run_command` tool. When `false` or omitted, the tool is disabled. |
| `enable_interactive_command_tool` | When `true`, enables `start_command`, `read_output`, `send_input`, and `stop_command`. The AI can provide the `executable` to run, an `args` list of command-line arguments, and an optional `cwd` working directory when calling `start_command`. The tool returns a session ID, which the AI uses to read output, send input, and stop the same running program. When `false` or omitted, these tools are disabled. |
| `enable_shell_tool` | When `true`, enables the `run_shell` tool. When `false` or omitted, the tool is disabled. |
| `enable_interactive_shell_tool` | When `true`, enables the `run_interactive_shell` tool. The AI can provide a shell script to run using the configured `shell_executable`. The tool returns a session ID, which the AI uses to read output, send input, and stop the same running process through `read_output`, `send_input`, and `stop_command`. When `false` or omitted, the tool is disabled. |
| `enable_interactive_script_tool` | When `true`, enables the `run_interactive_script` tool. The AI can create and execute scripts written in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. It supports both interactive scripts that require input while running and non-interactive scripts that execute without requiring additional input. ASTRA automatically compiles C and C++ scripts before execution. The required language runtimes and compilers must be installed on the Linux host. The tool returns a session ID, which the AI uses to read output, send input, and stop the running process through `read_output`, `send_input`, and `stop_command`. When `false` or omitted, the tool is disabled. |
| `shell_executable` | The shell ASTRA uses to run shell scripts. The default is `/bin/bash`. |
| `audit_log` | The file where ASTRA adds audit records in JSON-lines format. By default, this is `./audit.jsonl`. ASTRA creates the parent folder if it does not already exist. |

To choose a different audit-log file, set `ASTRA_MCP_AUDIT_LOG`:

```bash
export ASTRA_MCP_AUDIT_LOG='/absolute/path/to/audit.jsonl'
```

When this environment variable is set, it takes priority over `audit_log` in `tools.toml`.

Audit records may include tool names and arguments. Keep the log safe if those values could contain private information.

### Optional dynamic command tool

By default, ASTRA exposes only the individual tools you define in `[[tools]]` sections. To let the AI select an executable and supply arbitrary command-line arguments at call time, enable the generic tool in the `[server]` section:

```toml
[server]
enable_dynamic_command_tool = true
```

When enabled, the MCP client is shown a `run_command` tool with these inputs:

- `executable`: the program to launch, such as `git` or `hostname`.
- `args`: a list of arguments, each passed as a separate argument to the program. Use `[]` when no arguments are needed.

For example, a call to `run_command` could supply `executable = "git"` and `args = ["status", "--short"]`. Unlike configured tools, you do not need to add a new `[[tools]]` section or predefine placeholders for each command.

### Optional shell tool

By default, the `run_shell` tool is disabled. To enable it, set `enable_shell_tool = true` in the `[server]` section of `tools.toml`.

You can choose which shell ASTRA uses by setting `shell_executable`. The default is `/bin/bash`.

When enabled, the MCP client is shown a `run_shell` tool that lets the AI create and run shell scripts. It supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), and variables.

**Security note:** Shell scripts can run commands with the same operating-system permissions as ASTRA. They may read, change, or delete files that ASTRA's user can access. Enable this tool only if you trust the commands the AI may run.

### Optional interactive command tools

Set `enable_interactive_command_tool = true` in the `[server]` section of `tools.toml` to enable these tools.

| Tool | Purpose |
|---|---|
| `start_command` | Starts a program using the executable and arguments provided by the AI. The AI can also provide an optional working directory (`cwd`). Returns a session ID. |
| `read_output` | Reads the program's output. |
| `send_input` | Sends input to the running program, such as answering a prompt. |
| `stop_command` | Stops the running program. |

When calling `start_command`, the AI can choose which program to run, provide its command-line arguments, and optionally specify a working directory (`cwd`).

After starting a program, the AI uses the session ID to read its output, send input, and stop it when finished. This lets the AI continue working with the same running program across multiple tool calls.

These tools are disabled by default. After enabling them in `tools.toml`, restart ASTRA to apply the change.

### Optional interactive shell tool

By default, the `run_interactive_shell` tool is disabled. To enable it, set `enable_interactive_shell_tool = true` in the `[server]` section of `tools.toml`.

You can choose which shell ASTRA uses by setting `shell_executable` in `tools.toml`. The default is `/bin/bash`.

When enabled, the MCP client is shown a `run_interactive_shell` tool that lets the AI create and run complete shell scripts. It supports shell features such as pipes (`|`), logical OR (`||`), redirects (`>`), command chaining (`&&`), variables, and other shell syntax.

Unlike `run_shell`, this tool runs the script in an interactive shell session and returns a session ID. The AI can use this ID to interact with the same running process through `read_output`, `send_input`, and `stop_command`.

| Tool | Purpose |
|---|---|
| `read_output` | Reads output from the session and helps check whether the process has finished. |
| `send_input` | Sends input to the running script, such as responding to a prompt. |
| `stop_command` | Stops the process and releases its session resources. |

This is useful for scripts and programs that require input while running, including interactive prompts, terminal menus, and terminal editors such as `nano`, `vi`, and `vim`.

**Security note:** Shell scripts can run commands with the same operating-system permissions as ASTRA. They may read, change, or delete files that ASTRA's user can access. Enable this tool only if you trust the commands the AI may run.

After enabling the tool in `tools.toml`, restart ASTRA to apply the change.

### Optional interactive script tool

By default, the `run_interactive_script` tool is disabled. To enable it, set `enable_interactive_script_tool = true` in the `[server]` section of `tools.toml`.

When enabled, the MCP client is shown a `run_interactive_script` tool that lets the AI create and execute scripts written in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. It supports both scripts that require input while running and scripts that execute without requiring additional input.

The tool runs each script in a session and returns a session ID. The AI can use this ID to interact with the running process through `read_output`, `send_input`, and `stop_command`.

| Tool | Purpose |
|---|---|
| `read_output` | Reads output from the session and helps check whether the process has finished. |
| `send_input` | Sends input to the running script, such as responding to prompts. |
| `stop_command` | Stops the process and releases its session resources. |

For C and C++ scripts, ASTRA automatically compiles the source code before execution. The required language runtimes and compilers must be installed on the Linux host.

**Security note:** Scripts can execute commands and access files with the same operating-system permissions as ASTRA. Enable this tool only if you trust the scripts the AI may run.

After enabling the tool in `tools.toml`, restart ASTRA to apply the change.

## 6. Configure tools in `tools.toml`

Each `[[tools]]` section defines one MCP tool that ASTRA may provide. Add a separate section for every command you want ASTRA to make available.

```toml
[[tools]]
name = "hostname"
description = "Print the computer's hostname."
executable = "hostname"
enabled = true
timeout_seconds = 5
fixed_args = []
parameters = {}
allowed_paths = []
```

### Tool settings

| Setting | Required? | What it means |
|---|---|---|
| `name` | Yes | The unique name the MCP client uses for this tool. Give every tool a different name. |
| `description` | No | A short explanation that is shown to the AI. Say what the tool does and when the AI should use it. |
| `executable` | Yes | The program ASTRA runs. This can be a command found on `PATH`, such as `git`, or the full path to an executable. ASTRA rejects a relative path that contains `/`. |
| `enabled` | No | Controls whether the tool can be used. The default is `false`. Set it to `true` only after you have checked the command and its permissions. Disabled tools are not shown to the MCP client. |
| `timeout_seconds` | No | The maximum time this tool can run. If you leave this out, ASTRA uses `default_timeout_seconds`. The value must be from `1` to `max_timeout_seconds`. |
| `fixed_args` | No | The command-line arguments ASTRA always passes, in the order you list them. You can use placeholders such as `"{target}"` for values supplied by the AI. The default is an empty list. |
| `parameters` | No | The JSON fields the AI is allowed to send. For each field, you can set its type and whether it is required. The default is an empty table. |
| `working_directory` | No | The folder ASTRA uses as the command's current working directory. It can include parameter placeholders such as `"{repo}"`. ASTRA fills in the placeholder, resolves the resulting path, and checks that the path is inside one of the folders listed in `allowed_paths`. If you set `working_directory`, `allowed_paths` must not be empty. |
| `allowed_paths` | No | The folder paths ASTRA uses to approve `working_directory` and certain path placeholders. Use absolute paths and allow only the smallest folder the tool needs. An empty list rejects `working_directory` and `output` placeholders. For `path`, `file`, `directory`, and `repo` placeholders in `fixed_args`, also set `allowed_paths`. ASTRA checks those arguments against allowed paths only when this list is not empty. |
| `allowed_hosts` | No | A list of exact hostnames or IP addresses that are allowed for URL parameters named `url` or `uri`, and target parameters named `target` or `host`. An empty list disables these host checks. Wildcards are not supported. |

### Parameter settings

Parameters are the JSON values the AI sends when it calls a tool. Set them inside `parameters`.

| Setting | Required? | What it means |
|---|---|---|
| `type` | No | The type of value: `string`, `integer`, `number`, or `boolean`. Use `integer` for whole numbers and `number` for whole or decimal numbers. The default is `string`. You can also use `int` as another name for `integer`. |
| `description` | No | Explains what the value is used for. The AI can see this description in the generated JSON schema. |
| `required` | No | Set this to `true` if the AI must provide the value. The default is `false`. |

ASTRA rejects JSON fields that are not defined and checks that required fields are present and that values use the configured types.

### How `fixed_args` and placeholders work

ASTRA passes each item in `fixed_args` as a separate command-line argument. A placeholder such as `"{count}"` is replaced with the value supplied by the AI.

This example uses three parameters: the repository path, the number of commits to show, and the output format.

```toml
[[tools]]
name = "git_log"
description = "Show recent commits in a repository."
executable = "git"
enabled = true
timeout_seconds = 10
working_directory = "{repo}"
fixed_args = ["log", "-n", "{count}", "--format={format}"]
parameters = {repo = { type = "string", description = "Repository path", required = true }, count = { type = "integer", description = "Number of commits to show", required = true }, format = { type = "string", description = "Git log output format", required = true }}
allowed_paths = ["/home/your-user/projects"]
```

For example, the AI can provide these values:

- `repo`: `/home/your-user/projects/my-repo`
- `count`: `5`
- `format`: `%h %s`

ASTRA runs the command with these values as separate arguments. Replace the example path with the folder you want to allow.

## 7. Example: Check Git status in an approved repository

In this example, `working_directory = "{repo}"` tells ASTRA to run `git status` from the repository folder given in the `repo` parameter.

ASTRA resolves that path and checks that it is inside one of the folders in `allowed_paths`. Replace the example path with the real repository folder on your computer. Do not leave `allowed_paths` empty when you use `working_directory`.

```toml
[[tools]]
name = "git_status"
description = "Show a short Git status for the approved repository."
executable = "git"
enabled = true
timeout_seconds = 10
working_directory = "{repo}"
fixed_args = ["status", "--short"]
parameters = { repo = { type = "string", description = "Absolute path to the approved repository", required = true } }
allowed_paths = ["/home/your-user/projects/my-repo"]
```

Replace `/home/your-user/projects/my-repo` with the correct folder path. The `repo` value supplied by the AI must resolve to that folder or to a folder inside an allowed folder.

ASTRA then runs `git status --short`, using that repository folder as the command's current working directory.

## 8. Example: Get headers from an approved website

```toml
[[tools]]
name = "example_headers"
description = "Get HTTP response headers from example.com."
executable = "curl"
enabled = true
timeout_seconds = 15
fixed_args = ["--head", "--fail", "--max-time", "10", "{url}"]
parameters = { url = { type = "string", description = "HTTP or HTTPS URL on example.com", required = true } }
allowed_paths = []
allowed_hosts = ["example.com"]
```

The URL must use HTTP or HTTPS. Its hostname must match an entry in `allowed_hosts`. Hostname matching ignores uppercase and lowercase differences.

An allowed-host list is not a firewall. It also cannot protect against every DNS or network-level risk.

## 9. Add or change a tool

1. Add a `[[tools]]` section with a unique `name` and the program's `executable`.
2. Put command-line options that never change in `fixed_args`. Use placeholders for values the AI will provide.
3. Add every placeholder to `parameters`. Set its type and use `required = true` if the AI must provide it, or `required = false` if it is optional.
4. Set `working_directory`, `allowed_paths`, or `allowed_hosts` if the command needs them.
5. Set `enabled = true` after checking the command and its configuration.
6. Restart ASTRA after you change `tools.toml`. The changes take effect after ASTRA restarts.

You can also enable the `run_command` tool by setting `enable_dynamic_command_tool = true` in the `[server]` section of `tools.toml`. Once enabled, the AI can choose an executable and provide its arguments when calling the tool, without requiring a separate `[[tools]]` entry for each program.

You can enable the `run_shell` tool by setting `enable_shell_tool = true` in the `[server]` section of `tools.toml`. This lets the AI create and run shell scripts without adding a separate `[[tools]]` entry. Set `shell_executable` to choose the shell ASTRA uses. Restart ASTRA after changing these settings.

You can also enable the interactive command tools by setting `enable_interactive_command_tool = true` in the `[server]` section of `tools.toml`. When calling `start_command`, the AI can provide the `executable` to run, an `args` list containing its command-line arguments, and an optional `cwd` working directory. These tools let the AI start a program, read its output, send input to answer prompts, and stop the running process. The `start_command` tool returns a session ID, which the AI uses to interact with the same process through `read_output`, `send_input`, and `stop_command`. These tools are disabled by default. Restart ASTRA after changing this setting.

You can also enable the `run_interactive_shell` tool by setting `enable_interactive_shell_tool = true` in the `[server]` section of `tools.toml`. This allows the AI to create and run shell scripts in an interactive session using the configured `shell_executable`. It returns a session ID that the AI can use with `read_output`, `send_input`, and `stop_command` to interact with the same running process. Restart ASTRA after changing this setting.

You can also enable the `run_interactive_script` tool by setting `enable_interactive_script_tool = true` in the `[server]` section of `tools.toml`. It allows the AI to create and run interactive and non-interactive scripts in Python, Ruby, JavaScript (Node.js), Perl, Bash, C, and C++. C and C++ scripts are automatically compiled before execution. Restart ASTRA after changing this setting.

## 10. Connect an MCP client

ASTRA uses stdio, so your MCP client must start the ASTRA executable. The exact setup steps depend on the MCP client, but you will usually need these settings:

- **Command:** The full path to the `astra` executable inside the project's `.venv/bin/` folder.
- **Arguments:** If needed, add `--config` followed by the full path to `tools.toml`.
- **Working directory:** The project folder, if your client has this setting.
- **Environment variables:** You can set `ASTRA_MCP_CONFIG` and `ASTRA_MCP_AUDIT_LOG` to full paths.

For example, the command could be `/absolute/path/to/project/.venv/bin/astra`. Replace this example with the actual path on your computer.

A tunnel client is a separate program from ASTRA. Its profile, login details, and connection settings depend on the tunnel-client product you use. You do not configure those settings in `tools.toml`.

If your MCP client supports Streamable HTTP and you prefer to connect through an HTTP endpoint instead of launching ASTRA directly over stdio, see [Section 11: Optional Streamable HTTP Bridge](#11-optional-streamable-http-bridge).

## 11. Optional Streamable HTTP Bridge

ASTRA uses MCP stdio transport by default. If your MCP client supports Streamable HTTP but cannot launch a local stdio server, you can use the optional bridge to expose ASTRA through an HTTP endpoint.

The bridge starts ASTRA as a subprocess, connects to it over stdio, and forwards MCP tool-listing and tool-call requests over Streamable HTTP. ASTRA's existing `tools.toml` configuration and tool permissions continue to apply, provided ASTRA loads the intended configuration.

### Requirements

- ASTRA installed and accessible from the environment running the bridge.
- An HTTP-capable MCP client.
- Optionally, a tunnel client for remote access.

### Start the Bridge

The bridge script is named `astra_bridge.py`.

Start the bridge using the default port:

```bash
python astra_bridge.py
```

By default, the bridge listens on `127.0.0.1:8000`. To select another port:

```bash
python astra_bridge.py --port 9000
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Use the port you selected if it differs from `8000`.

### Configure ASTRA

The bridge passes the `ASTRA_MCP_CONFIG` environment variable to ASTRA when it is set. Otherwise, ASTRA uses its normal configuration-file discovery behavior.

For example:

```bash
export ASTRA_MCP_CONFIG='/absolute/path/to/tools.toml'
python astra_bridge.py
```

Configure your tools and settings in `tools.toml` as described in the above sections of this README.


### Expose the Bridge Through a Tunnel (Optional)

If your MCP client needs remote access, you can expose the local bridge using a tunneling service such as Cloudflare Tunnel (`cloudflared`), ngrok, or a VPS configured for remote access.

**Note:** The tunnel client is a separate program. Its installation and configuration depend on the provider you choose. Install and configure your preferred tunneling service before proceeding.

**1. Start the bridge — Terminal 1**

```bash
python astra_bridge.py
```

Uvicorn starts the server and prints its local address, by default:

```text
http://127.0.0.1:8000
```

Keep this terminal running.

**2. Start the tunnel — Terminal 2**

Open a second terminal and start your preferred tunneling service.

With Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

With ngrok:

```bash
ngrok http http://127.0.0.1:8000
```

Copy the public HTTP or HTTPS URL displayed by the tunneling service. Keep this terminal running too.

**3. Update `tunnel_url.txt` — Terminal 3**

Open a third terminal and navigate to the directory containing `astra_bridge.py` and `tunnel_url.txt`.

When downloaded fresh from GitHub, `tunnel_url.txt` is empty. Open it in a text editor, paste the public URL provided by your tunneling service, and save the file.

For example, the file should contain only the URL:

```text
https://your-tunnel.example
```

Do not append `/mcp` to the URL in this file.

**4. Configure your remote MCP client**

Configure your remote MCP client to use the tunnel URL with `/mcp` appended.

For example, if the tunnel URL is `https://your-tunnel.example`, the MCP endpoint is:

```text
https://your-tunnel.example/mcp
```

The bridge checks `tunnel_url.txt` periodically and updates its allowed-host list when the URL changes. This supports temporary tunnel URLs and stable custom domains without restarting the bridge.

If you selected a different bridge port, use that port in your tunnel configuration.

A VPS can also be used for remote access if configured to forward requests to the bridge.

## License
This project is licensed under the MIT License
