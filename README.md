# haunted-shell 👻

A tiny ghost possesses your terminal and whispers eerie, one-line comments
about the commands you run. All commentary is generated **locally** by a
small open-weight model - your commands never leave your machine.

It is the Halloween sibling of
[lazycommit](https://github.com/MRNOWSHIRWAN/lazycommit). The tiny 0.5B
coder model that writes my commit messages turned out to be a terrible
ghost (too literal), so the ghost moved into Qwen2.5 1.5B Instruct -
still a ~1 GB open-weight model that runs fine on a laptop CPU.

```console
$ git push origin main
👻 pushing souls into the remote void... they may never return
$ rm -rf build/
👻 deleting evidence, mortal? the ghost remembers everything
```

## Why local

A ghost that phones home is just spyware with a costume. haunted-shell talks
to an open-weight model running on your own machine (Ollama or any
OpenAI-compatible server), so after the one-time install and model download
it is:

- **Private**: by default, whispers are generated on loopback only. The tool
  refuses non-loopback endpoints (deliberate override: `HAUNT_ALLOW_REMOTE=1`)
  and does not follow HTTP redirects. The tool itself never writes command
  text to disk - your shell's own history behaves exactly as it always has.
  Commands that look like they contain credentials are skipped entirely.
  Local processing is not secret-proof, so treat the secret filter as a
  seatbelt, not a vault.
- **Free**: no API key, no subscription for the tool itself.
- **Offline**: after install + model download, whispers need no network.

## Setup

**1. Install the CLI**

```console
$ pip install git+https://github.com/MRNOWSHIRWAN/haunted-shell.git
```

**2. Run a model server** (same one lazycommit uses)

```console
$ ollama pull qwen2.5:1.5b-instruct
$ ollama serve   # http://localhost:11434/v1, the default
```

No Ollama? `pip install 'haunted-shell[local]'` and pass
`--backend local --model-path /path/to/model.gguf` to run the model
in-process instead.

**3. Haunt your shell**

```console
$ haunt install-hook >> ~/.bashrc   # or ~/.zshrc
$ exec $SHELL
```

The hook runs the ghost in the background after each command, so your prompt
never waits. Tune how chatty it is with `--every N` (default hook: every
3rd eligible command). Boring commands (`ls`, `cd`, ...) are ignored.

## Safety

The ghost only *comments*. It never edits, intercepts, or blocks your
commands, and if anything goes wrong it fails silently - a ghost must never
break a shell.

## License

MIT
