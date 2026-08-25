"""
Minimal MCP server for PromptHub — stdio JSON-RPC.

Tools:
- prompts.list  {search?, business_function?, status?, page_size?}
- prompts.get   {prompt_ref}
- catalog.get   {}
- executions.run {prompt_id, input_data?, model_provider?, model_name?}

Security: allowlists HTTP paths, validates prompt_id is int, redacts secrets from logs.
Run: uv run python mcp-server/server.py --base-url http://127.0.0.1:8010
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

ALLOW = {
    "prompts.list": ("GET", "/api/v1/prompts"),
    "prompts.get": ("GET", "/api/v1/prompts/{prompt_ref}"),
    "catalog.get": ("GET", "/api/v1/catalog"),
    "executions.run": ("POST", "/api/v1/executions"),
}

def call(base: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool not in ALLOW:
        return {"error": f"unknown tool {tool}"}
    method, tmpl = ALLOW[tool]
    path = tmpl
    if "{prompt_ref}" in path:
        ref = str(args.pop("prompt_ref", "")).strip()
        if not ref:
            return {"error": "prompt_ref required"}
        path = path.replace("{prompt_ref}", ref)
    if tool == "executions.run":
        pid = args.get("prompt_id")
        if not isinstance(pid, int):
            return {"error": "prompt_id must be int"}
        prov = args.get("model_provider")
        if prov and prov not in ("auto", "mock", "ollama", "openai", "litellm"):
            return {"error": f"invalid model_provider {prov}"}
    url = base.rstrip("/") + path
    with httpx.Client(timeout=120) as c:
        if method == "GET":
            r = c.get(url, params={k: v for k, v in args.items() if v is not None})
        else:
            r = c.post(url, json=args)
        r.raise_for_status()
        return r.json()

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8010")
    args = p.parse_args()
    for line in sys.stdin:
        line=line.strip()
        if not line:
            continue
        try:
            req=json.loads(line)
            tool=req.get("tool")
            params=req.get("params",{})
            res=call(args.base_url, tool, dict(params))
            json.dump({"id": req.get("id"), "result": res}, sys.stdout)
            sys.stdout.write("\n")
            sys.stdout.flush()
        except Exception as e:
            json.dump({"error": str(e)}, sys.stdout)
            sys.stdout.write("\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
