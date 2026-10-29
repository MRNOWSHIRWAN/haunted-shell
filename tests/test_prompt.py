from haunted_shell.prompt import build_messages, SYSTEM_PROMPT, MAX_COMMAND_CHARS


def test_messages_shape():
    msgs = build_messages("git status", 0)
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == SYSTEM_PROMPT
    assert msgs[-1]["role"] == "user"
    assert "git status" in msgs[-1]["content"]


def test_fewshot_examples_present():
    msgs = build_messages("make", 0)
    roles = [m["role"] for m in msgs]
    assert roles.count("assistant") >= 3  # examples for the small model to imitate


def test_command_truncated():
    long_cmd = "x" * (MAX_COMMAND_CHARS + 50)
    msgs = build_messages(long_cmd, 0)
    assert ("x" * (MAX_COMMAND_CHARS + 1)) not in msgs[-1]["content"]


def test_exit_code_mentioned_only_on_failure():
    assert "exit code" not in build_messages("make", 0)[-1]["content"]
    assert "exit code 2" in build_messages("make", 2)[-1]["content"]
