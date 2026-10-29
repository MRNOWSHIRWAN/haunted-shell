import os
from haunted_shell.cli import eligible, take_turn, format_whisper, main


def test_eligible_skips_boring():
    assert not eligible("ls -la")
    assert not eligible("cd /tmp")
    assert not eligible("   ")
    assert eligible("git push origin main")
    assert eligible("rm -rf ./build")


def test_take_turn_counts(tmp_path):
    d = str(tmp_path)
    assert take_turn(3, d) is False  # 1
    assert take_turn(3, d) is False  # 2
    assert take_turn(3, d) is True   # 3
    assert take_turn(1, d) is True   # every time


def test_format_whisper_single_line_dim():
    out = format_whisper("boo\nfrom the\nother side")
    assert "\n" not in out.strip()
    assert out.startswith("\033[3;90m")
    assert "👻" in out


def test_whisper_boring_command_is_silent(capsys):
    assert main(["whisper", "--", "ls", "0"]) == 0
    assert capsys.readouterr().out == ""


def test_whisper_survives_backend_failure(capsys):
    # no server anywhere -> the ghost must fail silently, exit 0
    assert main(["whisper", "--timeout", "0.2",
                 "--base-url", "http://127.0.0.1:9/v1",
                 "--", "git push", "0"]) == 0
    assert capsys.readouterr().out == ""


def test_install_hook_prints_snippet(capsys):
    assert main(["install-hook"]) == 0
    out = capsys.readouterr().out
    assert "PROMPT_COMMAND" in out
    assert "haunt whisper" in out


def test_backend_env_override(monkeypatch):
    monkeypatch.setenv("HAUNT_BACKEND", "local")
    monkeypatch.delenv("HAUNT_MODEL_PATH", raising=False)
    import pytest
    with pytest.raises(SystemExit):
        main(["whisper", "--force", "--", "git status", "0"])


def test_likely_secret_is_silent(capsys):
    # forced or not, secrets never reach the model
    for cmd in ["export AWS_SECRET_ACCESS_KEY=abc123",
                "curl -H 'Authorization: Bearer tok' x",
                "sshpass -p hunter2 ssh x",
                "cat ~/.ssh/id_rsa -----BEGIN"]:
        assert main(["whisper", "--force", "--", cmd, "0"]) == 0
    assert capsys.readouterr().out == ""


def test_secret_regex_specifics():
    from haunted_shell.cli import contains_likely_secret
    assert contains_likely_secret("export API_KEY=xyz")
    assert contains_likely_secret("mysql -u root -psecret")
    assert not contains_likely_secret("git push origin main")
    assert not contains_likely_secret("grep -r password_policy docs/")
