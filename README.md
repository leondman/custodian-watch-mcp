# custodian-watch-mcp

A small, dependency-free MCP server with one tool, `custodian_prs(hours=40)`.

It scans recently merged pull requests in custodian repositories (default:
BitGo/BitGoJS) for token-onboarding patterns and returns chain / token / PR /
merge-time / URL leads. It uses the public GitHub API: no authentication, no
dependencies, standard library only.

A token-onboarding PR is a research signal, not a buy recommendation.

## Run with Claude Desktop or any MCP client

```json
{
  "mcpServers": {
    "custodian-watch": {
      "command": "python3",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## Quick test (no client needed)

```sh
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"custodian_prs","arguments":{"hours":168}}}' \
 | python3 server.py
```

## Licence

MIT
