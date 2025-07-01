Title: Slash commands - Anthropic

URL Source: https://docs.anthropic.com/en/docs/claude-code/slash-commands

Markdown Content:
Built-in slash commands
-----------------------

| Command | Purpose |
| --- | --- |
| `/add-dir` | Add additional working directories |
| `/bug` | Report bugs (sends conversation to Anthropic) |
| `/clear` | Clear conversation history |
| `/compact [instructions]` | Compact conversation with optional focus instructions |
| `/config` | View/modify configuration |
| `/cost` | Show token usage statistics |
| `/doctor` | Checks the health of your Claude Code installation |
| `/help` | Get usage help |
| `/init` | Initialize project with CLAUDE.md guide |
| `/login` | Switch Anthropic accounts |
| `/logout` | Sign out from your Anthropic account |
| `/mcp` | Manage MCP server connections and OAuth authentication |
| `/memory` | Edit CLAUDE.md memory files |
| `/model` | Select or change the AI model |
| `/permissions` | View or update [permissions](https://docs.anthropic.com/en/docs/claude-code/iam#configuring-permissions) |
| `/pr_comments` | View pull request comments |
| `/review` | Request code review |
| `/status` | View account and system statuses |
| `/terminal-setup` | Install Shift+Enter key binding for newlines (iTerm2 and VSCode only) |
| `/vim` | Enter vim mode for alternating insert and command modes |

Custom slash commands
---------------------

Custom slash commands allow you to define frequently-used prompts as Markdown files that Claude Code can execute. Commands are organized by scope (project-specific or personal) and support namespacing through directory structures.

### Syntax

#### Parameters

| Parameter | Description |
| --- | --- |
| `<prefix>` | Command scope (`project` for project-specific, `user` for personal) |
| `<command-name>` | Name derived from the Markdown filename (without `.md` extension) |
| `[arguments]` | Optional arguments passed to the command |

### Command types

#### Project commands

Commands stored in your repository and shared with your team.

**Location**: `.claude/commands/`

**Prefix**: `/project:`

In the following example, we create the `/project:optimize` command:

#### Personal commands

Commands available across all your projects.

**Location**: `~/.claude/commands/`

**Prefix**: `/user:`

In the following example, we create the `/user:security-review` command:

### Features

#### Namespacing

Organize commands in subdirectories to create namespaced commands.

**Structure**: `<prefix>:<namespace>:<command>`

For example, a file at `.claude/commands/frontend/component.md` creates the command `/project:frontend:component`

#### Arguments

Pass dynamic values to commands using the `$ARGUMENTS` placeholder.

For example:

#### Bash command execution

Execute bash commands before the slash command runs using the `!` prefix. The output is included in the command context.

For example:

#### File references

Include file contents in commands using the `@` prefix to [reference files](https://docs.anthropic.com/en/docs/claude-code/common-workflows#reference-files-and-directories).

For example:

#### Thinking mode

Slash commands can trigger extended thinking by including [extended thinking keywords](https://docs.anthropic.com/en/docs/claude-code/common-workflows#use-extended-thinking).

### File format

Command files support:

*   **Markdown format** (`.md` extension)
*   **YAML frontmatter** for metadata: 
    *   `allowed-tools`: List of tools the command can use
    *   `description`: Brief description of the command

*   **Dynamic content** with bash commands (`!`) and file references (`@`)
*   **Prompt instructions** as the main content

MCP servers can expose prompts as slash commands that become available in Claude Code. These commands are dynamically discovered from connected MCP servers.

### Command format

MCP commands follow the pattern:

### Features

#### Dynamic discovery

MCP commands are automatically available when:

*   An MCP server is connected and active
*   The server exposes prompts through the MCP protocol
*   The prompts are successfully retrieved during connection

#### Arguments

MCP prompts can accept arguments defined by the server:

#### Naming conventions

*   Server and prompt names are normalized
*   Spaces and special characters become underscores
*   Names are lowercased for consistency

### Managing MCP connections

Use the `/mcp` command to:

*   View all configured MCP servers
*   Check connection status
*   Authenticate with OAuth-enabled servers
*   Clear authentication tokens
*   View available tools and prompts from each server

See also
--------

*   [Interactive mode](https://docs.anthropic.com/en/docs/claude-code/interactive-mode) - Shortcuts, input modes, and interactive features
*   [CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference) - Command-line flags and options
*   [Settings](https://docs.anthropic.com/en/docs/claude-code/settings) - Configuration options
*   [Memory management](https://docs.anthropic.com/en/docs/claude-code/memory) - Managing Claude’s memory across sessions