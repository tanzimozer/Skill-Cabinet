# Zero-to-One GitHub Project for an Absolute Beginner

Pattern for designing Tahmeed's **first GitHub project** — he has no coding background
and has never used Git/GitHub. Built and validated Jun 2026.

## Design principles
1. **Build only on what he has.** As of Jun 2026 he'd done the conceptual half of
   Claude 101 — prompting, the Description–Discernment loop, and artifacts. No Claude
   Code, no API, no terminal yet. The project must let **Claude write the code** while
   *he* learns the Git workflow. Don't require skills he hasn't earned.
2. **One new thing only.** The single new skill is GitHub: account → repo → commit →
   push → GitHub Pages. Everything else leans on what he already knows.
3. **End in a live, shareable artefact.** Nothing motivates a beginner like seeing
   their own thing on the public internet. A live URL he can send to Tanzim is the hook.
4. **The real lesson is the loop.** The core takeaway isn't the website — it's the
   *edit → git add → git commit → push → it's live* rhythm. Make that its own phase.

## The validated project: "My Claude Prompt Library"
A single-page HTML site listing his favourite prompts + why each works. He prompts
Claude to generate the `index.html` artifact, saves it, then ships it on GitHub Pages.

Phases (each with an explicit ✅ checkpoint):
- **0 — Accounts & tools:** GitHub account, install Git, `git --version`, `git config`.
- **1 — Build with Claude:** new Project, specific prompt, iterate via artifacts, save `index.html`.
- **2 — First repo:** `git init / add / commit -m / remote add origin / push`.
- **3 — Go live:** Settings → Pages → main/root → live URL.
- **4 — The change loop:** edit → add → commit → push → refresh → it's online. (The point.)
- **5 — README:** ask Claude to write `README.md`, commit, push.

Done = live link works + public repo with ≥3 commits + a README + he can explain
what `commit` and `push` do in his own words. Then 3 tracker reflections.

## Mentor notes that matter
- **Let him hit Git errors.** Resolving them *is* the learning. Don't pre-solve.
- **Most likely snag: first-`push` auth.** GitHub wants a Personal Access Token, not a
  password. GitHub Desktop is a gentler on-ramp (buttons not terminal) if the CLI
  frustrates him on day one — same concepts.
- **This is the bridge into Claude Code 101.** Getting comfortable in the terminal here
  sets up the next course naturally.

## Live mentoring over phone photos — failure modes (validated Jun 2026)

He works on the laptop but reports back via **photos of his screen taken on his phone**.
Read terminal state from those photos. The recurring snags below all surfaced in a single
Phase 1→2 session and will recur with any absolute beginner:

- **"GitHub gave me a bunch of codes" is NOT an error.** Beginners read the repo setup
  page (`git init / add / commit / remote add / push`) as an error dump. Reassure first:
  those are the commands to run, not a problem. He's on track.
- **Empty `$` prompt after install reads as "broken" to him.** A fresh Git Bash showing
  only `$` is success, not failure. Confirm with `git --version` → version number = good.
- **`git add .` in the HOME folder is the classic disaster.** If he runs the sequence in
  `~` instead of his project folder, Git tries to add all of `AppData/...` and throws
  `Permission denied` / `fatal: adding files failed`. **Always make him `cd` to the
  project folder FIRST** (`cd ~/Downloads` or wherever the file lives), and confirm he's
  there before any `git add`. Recovery: `rm -rf .git` (safe — only removes Git tracking,
  not his files), then restart the sequence in the right folder.
- **The `>` continuation-prompt trap.** When a line has an unclosed quote (e.g.
  `git commit -m "first commit` with a missing close-quote, or commands jammed together),
  Git Bash shows `>` and waits forever. Beginners think it's still running. Fix:
  **Ctrl + C** to cancel back to a clean `$`, then retype properly.
- **Commands get jammed/concatenated when typed fast.** Saw `git add.` (missing space),
  `gitgit remote add` (doubled), and commit+branch lines run onto one line. **Mandate
  one command, Enter, wait, read the output, then the next.** Never let him paste or type
  the whole block at once. Ask for a photo after pivotal single lines (e.g. after `cd`)
  to verify state before proceeding.
- **"Can I scroll / write sideways?"** Beginners don't know a terminal scrolls with
  mouse/PageUp and that old output above is harmless. You don't scroll to run a command —
  you type at the `$` and press Enter. Old output is just history; ignore it.
- **Identity setup runs once, ever.** `git config --global user.email` /
  `user.name` — if `git commit` says "Author identity unknown", that's the fix. Watch for
  typos like `user.namw`.
- **Repo name typos are permanent until renamed.** His repo was `promt-library` (not
  `prompt-library`). Always use the exact `remote add origin` URL GitHub shows on HIS
  page, not the idealised name from the curriculum doc.

**Mentoring cadence that works:** diagnose from the photo → name what went wrong in one
plain sentence → give the clean corrected sequence in a code block → tell him to run it
ONE line at a time → ask him to report back the output of the single pivotal line. Calm,
reassuring, never make him feel he broke something.

## Second live session — Windows / cmd.exe failure modes (validated Jun 2026)

He switched to **Command Prompt (cmd.exe)**, not Git Bash, and worked on Windows. Git
works fine in cmd — don't insist on Git Bash. New snags that surfaced, all classic and
all will recur:

- **THE BIG ONE — file and Git repo in two different folders.** He created the Git repo
  in `OneDrive\my-project` but his HTML file was in `Desktop\my project`. So `git add`
  saw nothing, the push uploaded an empty repo, and **GitHub Pages refused to give a
  link** ("you must first add content to your repository"). Diagnosis chain: no Pages
  link → repo is empty → file never got committed → file isn't in the Git folder.
  **Always confirm the file and the `.git` folder are in the SAME directory before
  pushing.** Make him `dir` to see the file with your own eyes.
- **The "no Pages link" symptom = empty repo, 95% of the time.** When GitHub Pages won't
  generate a URL and shows "add content to your repository before you can publish", the
  fix is upstream: he hasn't successfully committed + pushed a file yet. Don't fiddle with
  the Pages settings — go back and verify the file actually reached GitHub.
- **Open the terminal IN the right folder — the cleanest Windows fix.** Type `cmd` into
  **File Explorer's address bar** (over the folder path) and press Enter. A fresh Command
  Prompt opens already `cd`'d into that exact folder. This sidesteps every wrong-folder
  bug. Use it whenever he's lost in the wrong directory.
- **`C:\Windows\System32>` is the wrong-folder trap on cmd.** Opening Command Prompt from
  the Start menu lands in System32. `git init` there throws `Permission denied`, and every
  later command fails with `not a git repository`. Don't debug the commands — get him into
  the project folder first (address-bar `cmd` trick above).
- **Windows path slash-drop.** `cd %USERPROFILE%Downloads` fails ("system cannot find the
  path") because the backslash got eaten — must be `cd %USERPROFILE%\Downloads`. Watch for
  missing backslashes in any path he types.
- **Multi-line paste jams on cmd too.** Pasting the whole command block at once makes cmd
  run them as one mangled line (`git init git add git commit -m "..."` → `error: unknown
  switch 'm'`), or splits a quoted command across two lines. This hits `ren` as well:
  `ren "my project.html"` and `index.html` landed on separate lines and failed. **One
  line, Enter, wait — every time.** If paste keeps breaking it, tell him to TYPE it by hand.
- **Rename to `index.html` is mandatory before push.** GitHub Pages only serves a file
  named exactly `index.html`. His was `my project.html`. Command (one line):
  `ren "my project.html" index.html` — quotes required because of the space. Verify with
  `dir` afterwards before touching Git.
- **`dir` is your eyes — use it at every checkpoint.** Before any `git add`/push, have him
  run `dir` and send the photo. It confirms (a) he's in the right folder and (b) the file's
  exact name. Reading the prompt path line in the photo (`...\Desktop\my project>`) also
  tells you instantly whether the `cd` worked — different prompt = he moved.

**Recovery for the two-folders mess:** don't try to move the repo. Just start clean in the
folder that has the file — open `cmd` there via the address-bar trick, rename to
`index.html`, then run the full `git init → add → commit → remote add origin <HIS exact
repo URL> → branch -M main → push -u origin main` sequence, one line at a time, in THAT
folder.

## Rename + push failure modes (validated Jun 2026, same session continued)

The rename-to-`index.html` and push steps generated a whole second wave of beginner snags.
All recur — diagnose them fast from the photo:

- **He renames the FOLDER, not the file.** Asked to make `index.html`, he renamed the
  `my project` *folder* to `index.html` while the file inside stayed `prompt library-2.html`.
  Tell from the `dir` output: prompt path ends `...\index.html>` (folder) but the listed file
  still has the old name. Fix: just `ren` the actual file inside; the stray folder name is harmless.
- **Double extension `index.html.html`.** Windows File Explorer (and sometimes `ren`) auto-appends
  `.html` when the extension is already shown, so typing `index.html` produces `index.html.html`.
  Spot it in `dir`. Fix (one line): `ren index.html.html index.html`. When renaming via Explorer,
  warn him the file may already show its extension — type just `index` if extensions are visible,
  or the full `index.html` if they're hidden.
- **Right-click → Rename in File Explorer is the escape hatch** when cmd `ren` keeps splitting
  across two lines. Right-click the file → Rename → type `index.html` → Enter → click **Yes** on
  the extension-change warning. Cleaner than fighting the paste-split in the terminal.
- **`git add .` can silently fail to stage.** He thought he ran it, but the next `git commit`
  said `nothing added to commit but untracked files present` and listed `index.html` in RED
  (untracked). The add never took. Fix: just re-run `git add .` then `git commit` — this time the
  commit reports `1 file changed, N insertions`. Red filename in commit output = not staged yet.
- **`push` fails with `URL rejected: Bad hostname`.** A stray/invisible character crept into the
  pasted `remote add origin` URL. Fix: `git remote remove origin`, then re-add by **typing the URL
  by hand** (not pasting): `git remote add origin <HIS exact repo URL>`, then push again.
- **Auth success ≠ push success — VERIFY the repo, not the login.** The browser showed
  "Authentication Succeeded", but the push had failed earlier on the bad URL, so the repo was still
  empty and Pages still gave no link. Login succeeding only means credentials are saved — it does
  NOT confirm the file reached GitHub. **Always confirm by opening the repo's main page:** if it
  shows the "Quick setup" screen (`git init / add / commit...` instructions), the repo is EMPTY and
  nothing pushed. A real repo shows the file list. Re-run the push and watch for the actual upload
  output before declaring victory.
- **Beginners land on the wrong GitHub page constantly.** He sent the GitHub *home/dashboard*,
  then the Pages *settings*, when asked to check the *repo*. Walk him explicitly: click the repo
  name in the left list → that's the repo page → look for the file list vs the empty "Quick setup"
  screen. Don't assume "I'm on GitHub" means he's on the right page.

## Remote-URL correction + auth + Pages failure modes (validated Jun 2026, same session continued)

The push-and-go-live tail produced a third wave of snags. All recur:

- **Wrong repo-name in the remote sticks across remove/re-add churn.** The URL kept reading
  `prompt-library` when the repo was `promt-library`. Repeatedly `remote remove` + `remote add`
  also kept jamming (the URL merged onto the remove line: `git remote remove originhttps://...`).
  **Cleanest fix: `git remote set-url origin <HIS exact URL>`** — one command, no remove dance.
- **ALWAYS read the URL back with `git remote -v` before pushing.** This is the single check that
  catches the `promt`/`prompt` typo. Make him run it and send the photo; you read both the (fetch)
  and (push) lines and confirm the exact repo name character-for-character before he pushes. This
  one habit would have saved ~6 round-trips.
- **`git remote-v` (missing space) is a new command-jam variant.** Git says `'remote-v' is not a
  git command... most similar is remote-fd`. Same lesson: it needs a space — `git remote -v`.
  `-V` uppercase also fails (`unknown switch 'V'`) — the verbose flag is lowercase `-v`.
- **First push pops the \"Connect to GitHub\" dialog — click \"Sign in with your browser.\"** Git
  Credential Manager offers Browser/Device and Token tabs. The orange **\"Sign in with your browser\"**
  button is the easy path for a beginner — it opens the browser, he approves, done. No PAT to paste.
- **The `127.0.0.1:59299/?code=...` blank white page is NOT a glitch — it's auth success.** After
  approving in-browser, the OAuth callback lands on a localhost page showing a `code=` URL and a
  blank/white body. Beginners ask \"is it a glitch?\" Reassure: that's GitHub confirming login worked.
  Tell him to go back to the terminal — the push has completed.
- **Two different \"main\"s in Settings — don't confuse them.** Settings → **General** shows
  \"Default branch: main\" (NOT what sets up Pages). Settings → **Pages** (left sidebar, under
  \"Code and automation\") is where the branch dropdown publishes the site. When he says \"it says
  main\", confirm WHICH screen he's on before celebrating.
- **Pages branch dropdown only offers \"None\" while the repo is empty.** If main isn't selectable in
  Pages, the repo has no content yet — same empty-repo diagnosis as the missing-link symptom. Once a
  file is actually pushed, `main` appears in the dropdown.
- **After clicking Save in Pages, the live link does NOT appear instantly.** GitHub *builds* the site
  first (1–2 min on first publish). Saving is confirmed by the **Custom domain + Enforce HTTPS**
  options appearing below. Tell him to wait ~2 min, then **refresh (F5)** — the green \"Your site is
  live at https://USER.github.io/REPO/\" banner appears at the top. Don't let \"there's no link\" right
  after Save read as failure.

## Phase 4 edit-loop failure modes (validated Jun 2026, same session continued)

Phase 4 (edit → add → commit → push → it's live) generated its own wave of beginner snags
once he opened `index.html` in an editor. All recur:

- **The editor's \"Open\" dialog hides the .html file behind a `.txt` filter.** Opening
  Notepad/Notepad++ then File → Open shows \"No items match your search\" because the file-type
  dropdown defaults to **Text documents (*.txt)**. Fix: change the dropdown (bottom-right of the
  Open dialog) to **All files (*.\\*)** and `index.html` appears. Easier path: right-click the file
  in Explorer → **Open with → Notepad/Notepad++** so you never touch the filtered dialog.
- **Don't double-click the html file to edit it — that opens it in the browser (view only).** A
  beginner double-clicks expecting to edit and gets Chrome rendering the page. Editing needs an
  *editor* (right-click → Open with → Notepad++), not a browser.
- **Tell him to edit ONLY the text between `>` and `<`.** He worried about line 1 (`<!DOCTYPE html>`)
  and the `<title>` tags. Guide: use **Ctrl+F** to jump to the exact words (e.g. `Claude Prompt
  Library`), change only the words, never the surrounding `<` `>` tags. Line 1 must stay untouched.
- **THE NEW BIG ONE — saving in the editor RE-ADDS `.html`, recreating `index.html.html`.** Even
  after the file was correctly named, committed, and pushed, saving his edit in Notepad++ produced
  `index.html.html` again. The next commit caught it as `rename index.html => index.html.html` and
  the push silently broke the live site (Pages can't serve the doubled name). **After ANY editor
  save, re-check the filename.** If it doubled: `ren index.html.html index.html`, then
  `git add . → git commit -m \"fix filename\" → git push`. Watch the commit's `rename` line — it tells
  you instantly whether the name is right.
- **He drifts out of the project folder between sessions — `git push` lands in `C:\\Users\\nj893>`.**
  After reopening cmd (or it reopening at HOME), the add/commit/push ran in the home folder, giving
  `nothing added to commit` and then `fatal: The current branch main has no upstream branch`.
  Diagnosis: read the prompt path — if it's not `...\\Desktop\\my project>`, he's in the wrong place.
  Fix: `cd \"OneDrive\\Desktop\\my project\"` (quotes for the space), confirm the prompt changed, then
  redo add/commit/push there. The `no upstream branch` error specifically = pushing from a folder
  whose repo was never connected to origin.
- **For repeat pushes after the first, plain `git push` is enough** (upstream already set by the
  initial `git push -u origin main`). If he gets `no upstream branch`, he's either in the wrong
  folder or pushing a fresh repo — not a Phase 4 problem with the loop itself.
- **LinkedIn (or any link-validator) saying \"please enter a valid link\" ≠ his site is broken.** When
  he tried to post the github.io URL to LinkedIn and it rejected the link, the cause is usually that
  Pages hasn't finished building (returns 404), not a bad URL. **Verify the site itself first** —
  open `https://USER.github.io/REPO/` in a fresh tab and check it loads vs 404 — before debugging the
  third-party validator.

## Phase 5 README failure modes (validated Jun 2026, same session continued)

Phase 5 (write a `README.md`, commit, push) produced its own wave. All recur:

- **Phase 5 step 2 is \"ask Claude to write it\" — beginners miss that it's a Claude step,
  not a terminal step.** The curriculum doc reads \"Ask Claude: *****\" with a blank, then
  step 3 is the `git add/commit/push` loop. He thought the whole phase was terminal work.
  Spell it out: step 2 = paste a prompt into Claude (e.g. \"Write a short README.md for my
  project — a Claude prompt library website built with HTML, hosted on GitHub Pages. Live
  link: <URL>\"), step 3 = paste the result into the file and ship it. Don't let \"create a
  file README.md\" read as a single terminal command.
- **`.md`, not `.html`.** The README must be `README.md` (Markdown). Same double-extension
  and `.txt`-filter gremlins as `index.html` — when saving via Notepad++ \"Save As\", set
  \"Save as type\" to **All files** so it doesn't become `README.md.txt`.
- **THE NEW BIG ONE — README saved as a FOLDER, not a file (`README.md/README.md`).**
  Saving created a *directory* named `README.md` with the actual file nested inside it. Two
  tells: (a) File Explorer lists `README.md` with Type = **File folder**, not a Markdown
  file; (b) after commit, the output reads `create mode 100644 README.md/README.md` and
  `dir` shows `README.md` as `<DIR>` (no size) instead of a file with a byte count. GitHub
  then won't render it as the repo's front page because it's buried in a subfolder.
- **README (like any project file) must live IN the project folder, not on the Desktop.**
  He created `README.md` on the Desktop; Git only tracks files inside the repo folder. Cut
  it and paste it into `my project` first, then `dir` to confirm `index.html` and
  `README.md` sit together before pushing.
- **Recovery for the nested-folder README — flatten it.** Don't delete and retype; pull the
  real file out. One line at a time:
  `move \"README.md\\README.md\" README-temp.md` → `rmdir \"README.md\"` →
  `ren README-temp.md README.md` → `dir` (confirm `README.md` now shows a SIZE, not `<DIR>`).
- **If `move` fails with \"system cannot find the file specified\", the nested file isn't
  named what you assumed.** The file inside the `README.md` folder may have a different name.
  Run `dir \"README.md\"` first to list the folder's actual contents and read the real
  filename before moving it. Never guess the inner filename — `dir` the folder.

## Full ready-to-hand brief
The complete formatted brief (all phases, exact commands, checkpoints) was authored to
`/tmp/tahmeed_project_brief.md` in-session — regenerate from the structure above if needed.
