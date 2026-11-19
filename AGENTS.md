# AGENTS.md

Short guide for any agent (or person) writing a Builds post on vatsalmishra.org.
Longer version: `CONTRIBUTING.md`.

**This repo is public.** Anything you push, to any branch, drafts included, is readable by anyone.

## The 4 commands

```sh
python3 scripts/builds.py new <slug>                       # scaffold builds/<slug>/post.md (status: draft)
python3 scripts/builds.py images <slug> <files...> [--cover]  # strip metadata, resize, save WebP
python3 scripts/builds.py build                            # regenerate pages, index, feed, sitemap, homepage block
python3 scripts/builds.py check                            # must print OK before you push
```

Preview with drafts (writes to `.preview/` only, never the repo):
`python3 scripts/builds.py build --include-drafts && python3 scripts/builds.py serve --preview`

One-time setup per clone:

```sh
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
git config core.hooksPath .githooks        # pre-push runs builds.py check
```

Use `.venv/bin/python` in place of `python3` if the packages are only in the venv.

## Rules

- Work on a branch: `post/<slug>` for posts, `feat/`, `fix/`, `chore/<slug>` for the rest. Never push to `main`; never force-push. Merging to `main` is a production deploy and is not your call.
- Edit only `builds/<slug>/post.md` and images made by `builds.py images`. Never hand-edit generated files (`builds/**/index.html`, `builds/feed.xml`, `sitemap.xml`, `robots.txt`, or the `BUILDS:START/END` block in `index.html`). Run `build` instead.
- Never commit original photos. Only files produced by `builds.py images`.
- Keep `status: draft` until the owner says the post can go live.
- Run `build` then `check` before every push. Fix every `FAILED` line. Read every `WARNING`.

## Post format

Front matter keys: `title`, `slug` (= folder name), `date`, `summary` (50-160 chars), `tags` (1-5, kebab-case), `status` (`draft`|`published`), optional `updated`, `cover`, `cover_alt`, `cover_caption`, `drafted_by`, `video`.

Every post should leave the reader with something to use. These H2 headings get special styling when present, in this order:

| Heading | Use it for |
| --- | --- |
| `## Give this to your agent` | One or more prompt blocks. Shown as a highlighted panel with Copy buttons; the index shows an "includes prompt" badge |
| `## What you need` | Bullet list of tools, accounts and inputs (rendered as a checklist) |
| `## Steps` | Numbered list |
| `## What didn't work` | What failed and what fixed it (amber callout) |
| `## Result` | What you ended up with, with numbers |

Prompt blocks are fenced with `prompt` and an optional title:

````md
```prompt title="Set up the thing"
The exact prompt. Put anything the reader fills in as [YOUR THING]: it gets highlighted.
```
````

Write prompts that work pasted into Claude, ChatGPT, Codex or any coding agent: say the goal, the rules, the deliverables, and ask the agent to check before risky steps.

Code inside a numbered or bulleted list: indent it 8 spaces under the item. Fenced blocks inside lists are not supported, and `check` flags them.

Images: `![Alt text that describes the image](img/name.webp "Optional caption")`. Alt text is required.
Raw HTML is limited to `<figure>`, `<figcaption>`, `<video>`, `<kbd>`, `<details>`, `<summary>`. No scripts, iframes or embeds: link to YouTube/Instagram instead.

## Never publish

Secrets or tokens; private paths, hostnames, IPs or ports; anything that locates a home (address, building or street name, window views, the outside of a building, parcels, router stickers); other people's faces, names or messages without their OK; employer-internal material of any kind; financial or health data. `check` catches some of this automatically. It cannot see inside images: open every image at full size before pushing.
