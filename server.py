#!/usr/bin/env python3
"""custodian-watch MCP server (dependency-free, stdio JSON-RPC).

Exposes one tool: custodian_prs - scan recent merged PRs in custodian/infra
repos for token-onboarding signals (the public-data listing-watch pattern).

No third-party packages: talks MCP over stdio and the public GitHub API.
"""
import json, sys, re, urllib.request, datetime

REPOS = ["BitGo/BitGoJS"]
PATTERN = re.compile(r"(add(ing)?\s(support\sfor\s)?[a-z0-9:_-]{2,}|client[- ]requested|new coin|ofc token|contract address|token config)", re.I)
TOKENISH = re.compile(r"\b(hoodeth|arb|sol|eth|base|poly|trx|xrp|sui|apt|near|doge|avax|ton|bsc)[:.-]([a-z0-9_-]{2,})\b", re.I)

def gh(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "custodian-watch-mcp/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def scan(hours=40):
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)).isoformat()
    leads = []
    for repo in REPOS:
        prs = gh(f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=50")
        for pr in prs:
            merged = pr.get("merged_at")
            if not merged or merged < since:
                continue
            text = f"{pr.get('title','')} {pr.get('body') or ''}"
            if not PATTERN.search(text):
                continue
            tokens = TOKENISH.findall(text)
            if not tokens and "add" not in pr["title"].lower():
                continue
            leads.append({
                "repo": repo, "pr": pr["number"], "merged_at": merged,
                "title": pr["title"], "url": pr["html_url"],
                "token_refs": [f"{c}:{t}" for c, t in tokens][:5],
            })
    return {"window_hours": hours, "leads": leads,
            "note": "Public PR data only. A token-onboarding PR is a research signal, not a buy recommendation."}

def reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n"); sys.stdout.flush()

TOOLS = [{"name": "custodian_prs",
          "description": "Scan recent merged PRs in custodian repos for token-onboarding signals.",
          "inputSchema": {"type": "object",
                          "properties": {"hours": {"type": "integer", "default": 40}},
                          "additionalProperties": False}}]

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid, method, params = req.get("id"), req.get("method"), req.get("params") or {}
        if method == "initialize":
            reply(rid, {"protocolVersion": params.get("protocolVersion", "2024-11-05"),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "custodian-watch", "version": "1.0.0"}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            reply(rid, {"tools": TOOLS})
        elif method == "tools/call":
            if params.get("name") != "custodian_prs":
                reply(rid, error={"code": -32602, "message": "unknown tool"})
                continue
            try:
                out = scan(int((params.get("arguments") or {}).get("hours", 40)))
                reply(rid, {"content": [{"type": "text", "text": json.dumps(out, indent=2)}]})
            except Exception as e:
                reply(rid, {"content": [{"type": "text", "text": f"scan failed: {e}"}], "isError": True})
        elif rid is not None:
            reply(rid, error={"code": -32601, "message": f"unknown method {method}"})

if __name__ == "__main__":
    main()
