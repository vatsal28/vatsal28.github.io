# Contributing a Builds post

The Builds section (`/builds/`) holds "how I built X" write-ups. Each post lives in its own folder,
`builds/<slug>/`, as Markdown with YAML front matter. `scripts/builds.py` turns that into static HTML,
which is committed. There is no build step on the hosts: Vercel and GitHub Pages serve the repo as is.

The quick, machine-facing version is `AGENTS.md`. This file adds the why.

## Flow

1. Branch: `git checkout -b post/<slug>`.
2. `python3 scripts/builds.py new <slug>` and write `builds/<slug>/post.md`. Keep the section headings that apply and delete the rest.
3. `python3 scripts/builds.py images <slug> <files...>` (add `--cover` with the cover image first; it also writes the 1200x630 share image). Originals stay on your machine.
4. `python3 scripts/builds.py build && python3 scripts/builds.py check`.
5. Look at it on a phone width (390px) and a desktop width (1440px):
   `python3 scripts/builds.py build --include-drafts && python3 scripts/builds.py serve --preview`, then open http://127.0.0.1:8000/builds/
6. Push the branch and open a PR. CI (`builds-check`) rebuilds, diffs, checks and runs the tests.
7. The site owner reviews, flips `status: published` (or asks you to), and merges. Merging to `main` deploys.

## What makes a good post

- **A takeaway.** Lead with the result. Give the reader something to use: prompts in a `## Give this to your agent` section, what they need, the steps, what didn't work.
- **Prompts that travel.** They should work in any capable agent. State the goal, constraints and deliverables. Mark fill-ins as `[LIKE THIS]`.
- **Plain writing.** Short sentences, active voice, real numbers. Dates as "19 Nov 2026".
- **Disclosure.** If an agent drafted it, set `drafted_by`.

## Privacy guardrails

The repo is public, so a pushed draft is a published draft as far as privacy goes. `builds.py check` scans
`post.md` files and generated pages for tokens, private paths, IPs, private hostnames, email addresses,
Eircodes, employer-internal markers, and a private denylist of location terms. The denylist is never in the repo:

- locally it is read from `~/.config/vatsalmishra-builds/denylist.txt` (one term per line),
- in CI from the `PRIVACY_DENYLIST` Actions secret.

If neither is set, `check` prints a WARNING and skips that part. Images are checked for size and metadata
(EXIF/GPS/XMP), but no script can tell you a photo shows a street sign. Look at each one.

See `AGENTS.md` for the "never publish" list and the allowed Markdown.

## Checks in detail

`check` fails on: invalid or unknown front matter keys; generated files missing, stale or hand-edited;
broken local links or `#anchors`; pages without exactly one `<h1>` or with skipped heading levels; images
without alt text or dimensions; disallowed raw HTML; images over 400 KB or 2000px, over 4 MB per post, or with
metadata; video files; any privacy match; and drift between the `:root` design tokens in `index.html` and
`assets/css/builds.css`.
