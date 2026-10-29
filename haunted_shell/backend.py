"""Model backends. Default: any OpenAI-compatible local server (Ollama)."""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.parse import urlparse

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:1.5b-instruct"
DEFAULT_TIMEOUT = 8.0

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: a local server must not bounce us to a remote one."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _check_loopback(base_url: str) -> None:
    host = urlparse(base_url).hostname or ""
    if host.lower() in LOOPBACK_HOSTS:
        return
    if os.environ.get("HAUNT_ALLOW_REMOTE") == "1":
        return
    raise SystemExit(
        f"haunt: refusing non-loopback endpoint {base_url!r}. "
        "The ghost is a local tool; set HAUNT_ALLOW_REMOTE=1 only if you "
        "really mean to send commands to another machine."
    )


class OllamaBackend:
    """Talks to an OpenAI-compatible chat endpoint (Ollama, llama.cpp server)."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL,
                 model: str = DEFAULT_MODEL,
                 timeout: float = DEFAULT_TIMEOUT):
        _check_loopback(base_url)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect)

    def whisper(self, messages: list[dict], max_tokens: int = 60) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self._opener.open(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()


class LocalBackend:
    """Runs a GGUF model in-process via llama-cpp-python (optional extra)."""

    def __init__(self, model_path: str, n_ctx: int = 1024):
        from llama_cpp import Llama  # optional dependency
        self._llm = Llama(model_path=model_path, n_ctx=n_ctx, verbose=False)

    def whisper(self, messages: list[dict], max_tokens: int = 60) -> str:
        out = self._llm.create_chat_completion(
            messages=messages, max_tokens=max_tokens, temperature=0.7,
        )
        return out["choices"][0]["message"]["content"].strip()
