"""Minimal stdio MCP client (JSON-RPC 2.0, newline-delimited). Stdlib only."""
import json
import os
import shlex
import shutil
import subprocess
import threading
import queue

# yargi-mcp 0.2.x breaks with fastmcp >= 3 / mcp 2.x, so pin fastmcp below 3.
DEFAULT_ARGS = ["--with", "fastmcp>=2.10.5,<3", "yargi-mcp"]


class McpError(RuntimeError):
    pass


def server_command():
    """YARGI_MCP_CMD overrides everything, e.g. 'yargi-mcp' or 'uvx yargi-mcp'."""
    override = os.environ.get("YARGI_MCP_CMD")
    if override:
        return shlex.split(override, posix=(os.name != "nt"))
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx] + DEFAULT_ARGS
    uv = shutil.which("uv")
    if uv:
        return [uv, "tool", "run"] + DEFAULT_ARGS
    raise McpError(
        "uv bulunamadı. Kurun: https://docs.astral.sh/uv/ "
        "(veya YARGI_MCP_CMD ortam değişkeniyle sunucu komutunu verin)."
    )


class McpClient:
    def __init__(self, timeout=180):
        self.timeout = timeout
        self._id = 0
        self._q = queue.Queue()
        self.proc = subprocess.Popen(
            server_command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        threading.Thread(target=self._reader, daemon=True).start()
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "yargi-cli", "version": "0.1.0"},
            },
        )
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _reader(self):
        for line in self.proc.stdout:
            try:
                self._q.put(json.loads(line))
            except ValueError:
                continue  # ignore non-JSON noise on stdout
        self._q.put(None)

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _request(self, method, params=None):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        while True:
            try:
                msg = self._q.get(timeout=self.timeout)
            except queue.Empty:
                raise McpError("Sunucu zaman aşımına uğradı.")
            if msg is None:
                raise McpError("Sunucu beklenmedik şekilde kapandı.")
            if msg.get("id") == rid:
                if "error" in msg:
                    raise McpError(msg["error"].get("message", str(msg["error"])))
                return msg["result"]

    def list_tools(self):
        return self._request("tools/list")["tools"]

    def call(self, name, arguments):
        res = self._request("tools/call", {"name": name, "arguments": arguments})
        if res.get("isError"):
            text = "".join(c.get("text", "") for c in res.get("content", []))
            raise McpError(text or "Araç hata döndürdü.")
        if res.get("structuredContent") is not None:
            return res["structuredContent"]
        text = "".join(c.get("text", "") for c in res.get("content", []))
        try:
            return json.loads(text)
        except ValueError:
            return text

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
