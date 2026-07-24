# gh CLI Device-Flow Auth (interactive, from a fresh box)

Use when there is **no** usable GitHub credential available and you must
authenticate the `gh` CLI interactively (web/device flow). This is the
fallback path — always try vault-based auth FIRST.

## Order of operations (do this first)

1. **Check the vault before anything interactive.** The `github-connect`
   skill expects an active PAT at `~/.hermes/vault.json` → `vault['github']['pat']`.
   If present and valid, you do NOT need device flow — export it and go:
   ```bash
   export GH_TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.hermes/vault.json')))['github']['pat'])")
   gh auth status
   ```
2. Only if there is no vault PAT / no `GH_TOKEN` / no `~/.config/gh/hosts.yml`,
   fall through to the device flow below.

## Installing gh (Debian/Ubuntu)

```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt-get update -qq && sudo apt-get install -y gh
```

## Driving the interactive prompt — the pattern that actually works

`gh auth login` opens with a Y/n prompt ("Authenticate Git with your GitHub
credentials?") BEFORE it prints the one-time code. Getting past that prompt
inside a background PTY is the sticking point.

**What failed this session:** starting the process, then sending `Y\n` after
the fact via `process(action=write)` / `process(action=submit)`. The prompt
did not advance — repeated writes left it stuck on the Y/n line.

**What worked:** pre-pipe the confirmation on stdin at launch so `gh` consumes
it immediately, and let the web/device flow print the code:

```bash
# background=true, pty=true, watch for the code / device URL
printf 'Y\n' | gh auth login \
  --hostname github.com --git-protocol https --web \
  --scopes "repo,read:org" --skip-ssh-key 2>&1
```

Watch patterns: `["one-time code", "device", "https://github.com/login/device"]`.

Then poll/log the process, read out the `XXXX-XXXX` code and the
`https://github.com/login/device` URL, and hand BOTH to Tanzim. The code
expires in a few minutes — if it lapses, kill and relaunch for a fresh one.

## Pitfalls

- **Don't rely on post-launch stdin writes to a PTY prompt.** Line-buffered
  `Y\n` writes via process-write may not land. Pipe the answer in at launch.
- **`--skip-ssh-key`** avoids an extra SSH-key upload prompt that otherwise
  adds another interactive step.
- **Device codes are short-lived.** Surface the code the moment it appears;
  don't sit on it. Relaunch to regenerate.
- This is the LAST resort. If the vault PAT exists, none of this is needed.
