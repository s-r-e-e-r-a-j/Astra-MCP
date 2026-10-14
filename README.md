# ASTRA MCP

ASTRA is an MCP server. It lets an AI assistant run command-line programs that you choose on your Linux computer.

You choose which programs ASTRA can use in the `tools.toml` file.

ASTRA reads this file and creates one MCP tool for each enabled tool. It also creates a JSON input schema from the settings you provide. When the AI calls a tool, ASTRA checks the input, runs the program without using a shell, and returns the result.

## Features

- Add command-line tools in `tools.toml`. You do not need to write a separate Python wrapper for every program.
- Show enabled tools to an AI client that supports MCP.
- Create JSON schemas from the parameters you set for each tool.
- Check required inputs, data types, unknown input names, and some unsafe characters.
- Run programs directly without using `sh`, `bash`, or `shell=True`.
- Set a time limit for each tool.
- Limit how many tools can run at once.
- Limit how much output ASTRA returns.
- Save records of tool calls in a JSON-lines audit log.
- Limit working directories and certain path placeholders. You can also allow only selected URL or target hosts when you configure them.
- Choose the configuration file and audit-log file with environment variables.
- Use `astra --help`, `astra --version`, and `astra --config`.

## Requirements

- Linux
- Python 3.13 or newer
- The command-line programs you want ASTRA to run
- An MCP-compatible client
- An internet connection to install Python packages, unless the packages are already available

Make sure your MCP client starts ASTRA using the executable from the Python environment where ASTRA is installed.

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

Check that ASTRA is installed by running:

```bash
astra --help
astra --version
```

If the `python3.13` command is not available, install Python 3.13 or a newer version first. ASTRA requires Python 3.13 or newer.

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

When a tool is called, the AI sends arguments in JSON format. ASTRA checks the arguments against the tool's parameter settings, fills in placeholders in `fixed_args`, and starts the program with each argument kept separate. ASTRA does not run the command through a shell.

While the MCP server is running, do not send normal print messages or debug messages to standard output. They can interfere with communication between ASTRA and the MCP client.

## 5. Configure the `[server]` section

The `[server]` section sets limits that apply to all ASTRA tools. Here is an example:

```toml
[server]
default_timeout_seconds = 30
max_timeout_seconds = 120
max_output_bytes = 200000
max_concurrency = 4
audit_log = "./audit.jsonl"
```

| Setting | What it means |
|---|---|
| `default_timeout_seconds` | The default number of seconds ASTRA allows a tool to run when that tool does not have its own timeout. The value must be at least `1` and cannot be greater than `max_timeout_seconds`. |
| `max_timeout_seconds` | The longest time a tool is allowed to run. The value must be at least `1`. A tool's own timeout cannot be higher than this value. |
| `max_output_bytes` | The maximum number of bytes ASTRA keeps from standard output and standard error in the returned result. The limit applies separately to each one. The value must be at least `1`. ASTRA currently captures all process output before cutting it down, so this setting does not fully limit memory use. |
| `max_concurrency` | The maximum number of tool calls ASTRA allows to run at the same time. The value must be at least `1`. |
| `audit_log` | The file where ASTRA adds audit records in JSON-lines format. By default, this is `./audit.jsonl`. ASTRA creates the parent folder if it does not already exist. |

To choose a different audit-log file, set `ASTRA_MCP_AUDIT_LOG`:

```bash
export ASTRA_MCP_AUDIT_LOG='/absolute/path/to/audit.jsonl'
```

When this environment variable is set, it takes priority over `audit_log` in `tools.toml`.

Audit records may include tool names and arguments. Keep the log safe if those values could contain private information.

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
parameters = {
  repo = { type = "string", description = "Repository path", required = true },
  count = { type = "integer", description = "Number of commits to show", required = true },
  format = { type = "string", description = "Git log output format", required = true }
}
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

## 10. Connect an MCP client

ASTRA uses stdio, so your MCP client must start the ASTRA executable. The exact setup steps depend on the MCP client, but you will usually need these settings:

- **Command:** The full path to the `astra` executable inside the project's `.venv/bin/` folder.
- **Arguments:** If needed, add `--config` followed by the full path to `tools.toml`.
- **Working directory:** The project folder, if your client has this setting.
- **Environment variables:** You can set `ASTRA_MCP_CONFIG` and `ASTRA_MCP_AUDIT_LOG` to full paths.

For example, the command could be `/absolute/path/to/project/.venv/bin/astra`. Replace this example with the actual path on your computer.

A tunnel client is a separate program from ASTRA. Its profile, login details, and connection settings depend on the tunnel-client product you use. You do not configure those settings in `tools.toml`.

## License
This project is licensed under the MIT License
