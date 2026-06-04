# Connecting to the Notifier MCP Server

## 1. Clone the repository

```bash
git clone <repo_url>
cd samcpar
```

## 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Verify the MCP server runs correctly

From the repository root:

```bash
.venv/bin/mcp run notifier/server.py
```

The process should start and remain running while waiting for client connections.

## 5. Add the server to Claude Desktop

Update your Claude Desktop MCP configuration file:

```json
{
  "mcpServers": {
    "notifier": {
      "command": "<path_to_repo>/.venv/bin/mcp",
      "args": [
        "run",
        "<path_to_repo>/notifier/server.py"
      ]
    }
  }
}
```

Example:

```json
{
  "mcpServers": {
    "notifier": {
      "command": "/Users/john/projects/samcpar/.venv/bin/mcp",
      "args": [
        "run",
        "/Users/john/projects/samcpar/notifier/server.py"
      ]
    }
  }
}
```

## 6. Restart Claude Desktop

After saving the configuration, completely quit and reopen Claude Desktop.

The Notifier MCP Server should now appear in the MCP tools list.
