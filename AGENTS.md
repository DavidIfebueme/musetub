# development rules

## documentation style

- all documentation in this repo is all lowercase. this includes readmes, comments, commit messages, pr titles, pr descriptions, issue text, and any other written material. no title case, no sentence case, no camel case headings. everything is lowercase.
- no emojis in commits, issues, pr comments, or code.
- no fluff or cheerful filler text. technical prose only, be direct.

## conversational style

- keep answers short and concise.
- when the user asks a question, answer it first before making edits or running implementation commands.
- when responding to user feedback or an analysis, explicitly say whether you agree or disagree before saying what you changed.

## code quality

- read files in full before wide-ranging changes, before editing files you have not fully inspected, and when asked to investigate or audit. do not rely on search snippets for broad changes.
- no `any` unless absolutely necessary.
- inline single-line helpers that have only one call site.
- check node_modules for external api types; don't guess.
- no inline imports (`await import()`, `import("pkg").Type`, dynamic type imports). top-level imports only.
- always ask before removing functionality or code that appears intentional.
- do not preserve backward compatibility unless the user asks for it.
- treat npm dep and lockfile changes as reviewed code. direct external deps stay pinned to exact versions.

## git

- never commit unless the user asks.
- only commit files you changed in this session.
- stage explicit paths (`git add <path1> <path2>`); never `git add -A` / `git add .`.
- before committing, run `git status` and verify you are only staging your files.
- message format: `{feat,fix,docs}: <commit message>` (optionally multiple lines). message is informative and concise. all lowercase.
- never run `git reset --hard`, `git checkout .`, `git clean -fd`, `git stash`, `git add -A`, `git add .`, `git commit --no-verify`.
- never force push.
- if rebase conflicts occur, resolve conflicts only in files you modified. if a conflict is in a file you did not modify, abort and ask the user.

## issues and prs

- when reviewing prs, do not run `gh pr checkout`, `git switch`, or otherwise move the worktree to the pr branch unless the user explicitly asks. use `gh pr view`, `gh pr diff`, `gh api`, and local `git show`/`git diff` against fetched refs to inspect without changing branches.
- when posting issue/pr comments, write the comment to a temp file and post with `gh issue/pr comment --body-file` (never multi-line markdown via `--body`).
- keep comments concise, technical, in the user's tone.
- all lowercase in comments, pr titles, and pr descriptions.

## strk20 build context

- this project builds on the strk20 privacy pool. the four installed skills live in `.agents/skills/`: strk20-privacy (concepts and route choice), strk20-wallet-api (private dapps), strk20-anonymizer-contracts (cairo helpers), strk20-privacy-sdk (wallets and key-holding backends). load the matching skill before doing strk20 work and open the reference pages in `references/` rather than recalling details.
- mainnet chain id is `sn_main`. rpc should come from an env var, never committed.
- `strk20.json` at the repo root holds the submission: mainnet transaction hashes that touched the pool, deployed contract addresses, the demo video, and the demo url. fill each field in as it comes to exist.

## user override

if the user's instructions conflict with any rule in this document, ask for explicit confirmation before overriding. only then execute their instructions.