### How to connect to the server 

## (1) Clone the repo samcpar

## (2) Create a local venv
python -m venv .venv

## (3) Install requirements
pip install -r requirements.txt

## (4) Add the MCP Server to the json config file
"mcpServers": {
    "notifier": {
      "command": "<path_to_venv_mcp>"
      "args": [
        "run",
        "<path_to_local_repo>/notifier/server.py"
      ]
    }
  }