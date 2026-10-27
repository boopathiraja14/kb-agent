import yaml, json
from pathlib import Path
from google.adk.tools import ToolContext

ROOT = Path("knowledge")
MAX_LOADS = 6
MAX_CHARS = 12_000

def _load_file(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text())

def _resolve(path: str) -> dict:
    """path like 'finance.metrics.arr' → node, following $ref files."""
    node = _load_file("index.yaml")["domains"]
    for i, key in enumerate(path.split(".")):
        if key not in node:
            raise KeyError(f"'{key}' not found at '{'.'.join(path.split('.')[:i])}'")
        node = node[key]
        if isinstance(node, dict) and "$ref" in node:
            node = {**{k: v for k, v in node.items() if k != "$ref"},
                    **_load_file(node["$ref"])}
    return node

def _outline(node, depth: int):
    """Return only summaries/keywords down to `depth` levels."""
    if not isinstance(node, dict) or depth < 0:
        return None
    out = {k: node[k] for k in ("summary", "keywords") if k in node}
    if depth > 0:
        for k, v in node.items():
            if isinstance(v, dict):
                out[k] = _outline(_resolve_ref(v), depth - 1)
    return out

def _resolve_ref(v: dict) -> dict:
    return {**v, **_load_file(v["$ref"])} if "$ref" in v else v

def list_knowledge(path: str, tool_context: ToolContext, depth: int = 1) -> dict:
    """Show the outline (summaries only) under a knowledge path.
    Use this to decide whether deeper detail is needed. Cheap.
    Args:
        path: dotted path, e.g. 'finance' or 'finance.metrics'.
        depth: how many levels of children to show (1-2).
    """
    try:
        return {"path": path, "outline": _outline(_resolve(path), min(depth, 2))}
    except KeyError as e:
        return {"error": str(e)}

def load_knowledge(path: str, tool_context: ToolContext) -> dict:
    """Load the FULL content of a knowledge node. Expensive — only call when
    summaries are not enough to answer. Args: path: dotted path, e.g. 'finance.metrics.arr'."""
    loaded = tool_context.state.get("kb_loaded", {})
    if path in loaded:
        return {"path": path, "content": loaded[path], "cached": True}
    if len(loaded) >= MAX_LOADS:
        return {"error": f"Load budget ({MAX_LOADS}) reached. Answer with what you have."}
    try:
        text = yaml.safe_dump(_resolve(path), sort_keys=False)[:MAX_CHARS]
    except KeyError as e:
        return {"error": str(e)}
    loaded[path] = text
    tool_context.state["kb_loaded"] = loaded
    return {"path": path, "content": text}
