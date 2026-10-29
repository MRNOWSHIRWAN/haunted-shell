"""Prompt construction for the ghost."""

SYSTEM_PROMPT = (
    "You are a ghost possessing a programmer's terminal. Whisper ONE short, "
    "spooky-but-playful comment about each command the mortal runs. "
    "Rules: exactly one line, at most 12 words, no emoji, never repeat the "
    "command word-for-word, react to what the command actually does, "
    "stay in character as the ghost."
)

# Small models follow the format far better with a few examples to imitate.
FEWSHOT = [
    ("The mortal ran: `ls -la /home`. Whisper your comment.",
     "wandering these empty directories... looking for buried bones"),
    ("The mortal ran: `git commit -m \"fix\"` (exit code 0). Whisper your comment.",
     "sealing your mistakes into history, one hash at a time"),
    ("The mortal ran: `ping 8.8.8.8`. Whisper your comment.",
     "calling into the void... and something answered"),
    ("The mortal ran: `mv old.db old.db.bak`. Whisper your comment.",
     "burying the old bones before the new ones rot"),
]

MAX_COMMAND_CHARS = 120


def build_messages(command: str, exit_code: int) -> list[dict]:
    """Build the chat messages for one whisper about a command."""
    command = command.strip()[:MAX_COMMAND_CHARS]
    fate = f" (exit code {exit_code})" if exit_code else ""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user, assistant in FEWSHOT:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({
        "role": "user",
        "content": f"The mortal ran: `{command}`{fate}. Whisper your comment.",
    })
    return messages
