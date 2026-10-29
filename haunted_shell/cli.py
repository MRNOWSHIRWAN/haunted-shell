"""haunt - the haunted terminal CLI."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

from .prompt import build_messages

import re

# Commands too boring (or too common) to deserve a whisper.
SKIP_COMMANDS = {"ls", "ll", "cd", "pwd", "clear", "exit", "history"}

# Anything that smells like a credential: the ghost stays quiet. Local
# processing is not secret-proof, so likely secrets never reach the model.
_SECRET_RE = re.compile(
    r"(?i)(passw(or)?d\s*[=:]"       # password= / password:
    r"|-p(?!\d+\b)\S+"             # inline -psecret (but not ssh -p2222)
    r"|secret|token|api[_-]?key|credential"
    r"|private[_ -]?key|BEGIN [A-Z ]*PRIVATE KEY"
    r"|\b\w*(KEY|TOKEN|SECRET|PASS|PWD)\w*=\S+)"
)


def contains_likely_secret(command: str) -> bool:
    return bool(_SECRET_RE.search(command))

HOOK_SNIPPET = r"""
# haunted-shell: let the ghost watch over this shell
_haunt_whisper() {
    local exit_code=$?
    local last_cmd
    last_cmd=$(fc -ln -1 2>/dev/null || history 1)
    # background + disown: the ghost never blocks your prompt.
    # flock: only one ghost at a time, fast typists don't stack whispers.
    mkdir -p ~/.local/state/haunted-shell
    ( flock -n ~/.local/state/haunted-shell/lock \
        haunt whisper --every "${HAUNT_EVERY:-3}" -- "$last_cmd" "$exit_code" & ) 2>/dev/null
    return $exit_code
}
case "$PROMPT_COMMAND" in
    *_haunt_whisper*) ;;
    *) PROMPT_COMMAND="_haunt_whisper${PROMPT_COMMAND:+;$PROMPT_COMMAND}" ;;
esac
""".strip()

DEFAULT_EVERY = 3  # whisper about every Nth eligible command
STATE_DIR = os.path.expanduser("~/.local/state/haunted-shell")


def eligible(command: str) -> bool:
    """Only whisper about commands worth a comment."""
    cmd = command.strip()
    if not cmd:
        return False
    first = cmd.split()[0]
    return first not in SKIP_COMMANDS


def take_turn(every: int = DEFAULT_EVERY, state_dir: str = STATE_DIR) -> bool:
    """Return True on every Nth call, tracked in a tiny state file."""
    if every <= 1:
        return True
    os.makedirs(state_dir, exist_ok=True)
    counter_path = os.path.join(state_dir, "counter")
    try:
        with open(counter_path) as f:
            n = int(f.read().strip())
    except (OSError, ValueError):
        n = 0
    n += 1
    with open(counter_path, "w") as f:
        f.write(str(n))
    return n % every == 0


def format_whisper(text: str) -> str:
    """Dim, italic, ghost-prefixed one-liner for the terminal."""
    one_line = " ".join(text.split())
    return f"\033[3;90m👻 {one_line}\033[0m"


def make_backend(args):
    backend = os.environ.get("HAUNT_BACKEND", args.backend)
    if backend == "local":
        from .backend import LocalBackend
        model_path = args.model_path or os.environ.get("HAUNT_MODEL_PATH")
        if not model_path:
            raise SystemExit("haunt: --backend local needs --model-path or HAUNT_MODEL_PATH")
        return LocalBackend(model_path)
    from .backend import OllamaBackend
    return OllamaBackend(
        base_url=os.environ.get("HAUNT_BASE_URL", args.base_url),
        model=os.environ.get("HAUNT_MODEL", args.model),
        timeout=args.timeout)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="haunt",
        description="A tiny local ghost that comments on your shell commands.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_hook = sub.add_parser("install-hook", help="print the shell hook snippet")

    p_w = sub.add_parser("whisper", help="whisper about one command")
    p_w.add_argument("command", help="the command the mortal ran")
    p_w.add_argument("exit_code", nargs="?", type=int, default=0)
    p_w.add_argument("--backend", choices=["ollama", "local"], default="ollama")
    p_w.add_argument("--base-url", default="http://localhost:11434/v1")
    p_w.add_argument("--model", default="qwen2.5:1.5b-instruct")
    p_w.add_argument("--model-path", default=None)
    p_w.add_argument("--timeout", type=float, default=8.0)
    p_w.add_argument("--every", type=int, default=1,
                     help="only whisper every Nth call (default: always)")
    p_w.add_argument("--force", action="store_true",
                     help="whisper even for boring commands")

    args = parser.parse_args(argv)

    if args.cmd == "install-hook":
        print(HOOK_SNIPPET)
        return 0

    if not args.force and not eligible(args.command):
        return 0
    if contains_likely_secret(args.command):
        return 0
    if not take_turn(args.every):
        return 0

    try:
        backend = make_backend(args)
        text = backend.whisper(build_messages(args.command, args.exit_code))
    except Exception:
        return 0  # a ghost must never break a shell
    if text:
        print(format_whisper(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
