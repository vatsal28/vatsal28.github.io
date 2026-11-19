"""Tests for scripts/builds.py. Run: python3 -m unittest discover scripts/tests"""

import contextlib
import html
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))

import builds  # noqa: E402
from PIL import Image  # noqa: E402

HOME = """<!DOCTYPE html>
<html lang="en"><head><style>
    :root {
      --ink: #101827;
      --window: #f8fafc;
    }
</style></head><body><main><h1>Home</h1>
      <!-- BUILDS:START -->
      <!-- BUILDS:END -->
<section id="contact"></section>
</main></body></html>
"""
CSS = ":root {\n  --ink: #101827;\n  --window: #f8fafc;\n}\nbody { margin: 0; }\n"

POST = """---
title: "{title}"
slug: {slug}
date: 2026-11-20
summary: "A perfectly ordinary summary that is comfortably longer than fifty characters."
tags: [agents, test]
status: {status}
---

Intro paragraph.

## Give this to your agent

```prompt title="Do the thing"
Build a thing for [YOUR CITY].
Use "quotes" & <angle> brackets.
```

## What you need

- A computer

## Steps

1. One
2. Two

## What didn't work

- Nothing

## Result

Done.
{extra}
"""


def quiet(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


class SiteCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="builds-test-"))
        (self.tmp / "assets" / "css").mkdir(parents=True)
        (self.tmp / "assets" / "js").mkdir(parents=True)
        (self.tmp / "assets" / "css" / "builds.css").write_text(CSS)
        (self.tmp / "assets" / "js" / "builds.js").write_text("// js\n")
        for icon in ("automation-gears", "cloidberg-agent", "vatsalos-mark", "start-button", "folder-document"):
            p = self.tmp / "assets" / "icons" / "w" / f"{icon}.webp"
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8)).save(p, "WEBP")
        (self.tmp / "assets" / "icons" / "favicon.png").write_bytes(b"x")
        (self.tmp / "assets" / "icons" / "apple-touch-icon.png").write_bytes(b"x")
        (self.tmp / "os").mkdir()
        (self.tmp / "os" / "index.html").write_text("<h1>os</h1>")
        (self.tmp / "index.html").write_text(HOME)
        (self.tmp / "builds").mkdir()
        self.env = dict(os.environ)
        os.environ.pop("PRIVACY_DENYLIST", None)
        os.environ["BUILDS_DENYLIST_FILE"] = str(self.tmp / "no-denylist.txt")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        shutil.rmtree(self.tmp)

    def add_post(self, slug="demo-post", status="published", title="A demo post title", extra="", raw=None):
        d = self.tmp / "builds" / slug
        (d / "img").mkdir(parents=True, exist_ok=True)
        text = raw if raw is not None else POST.format(slug=slug, status=status, title=title, extra=extra)
        (d / "post.md").write_bytes(text.encode("utf-8"))
        return d

    def build(self, **kw):
        rc, out = quiet(builds.cmd_build, self.tmp, kw.get("include_drafts", False), kw.get("out"))
        self.assertEqual(rc, 0, out)
        return out

    def check(self):
        problems = builds.run_checks(self.tmp)
        return problems.failures, problems.warnings


class TestFrontMatter(SiteCase):
    def assertFails(self, text_sub, needle, **kw):
        d = self.add_post(**kw)
        p = d / "post.md"
        old, new = text_sub
        p.write_text(p.read_text().replace(old, new, 1))
        failures, _ = self.check()
        self.assertTrue(any(needle in f for f in failures), failures)

    def test_valid_post_passes(self):
        self.add_post()
        self.build()
        failures, warnings = self.check()
        self.assertEqual(failures, [])
        self.assertTrue(any("denylist is NOT configured" in w for w in warnings))

    def test_unknown_key(self):
        self.assertFails(("status:", "staus: draft\nstatus:"), "unknown front matter key `staus`")

    def test_slug_must_match_folder(self):
        self.assertFails(("slug: demo-post", "slug: other-slug"), "must equal the folder name")

    def test_summary_length(self):
        self.assertFails(("A perfectly ordinary summary that is comfortably longer than fifty characters.", "Too short."), "summary must be 50-160")

    def test_bad_status(self):
        self.assertFails(("status: published", "status: live"), "status must be")

    def test_updated_before_date(self):
        self.assertFails(("date: 2026-11-20", "date: 2026-11-20\nupdated: 2026-11-01"), "`updated` must be on or after")

    def test_bad_tags(self):
        self.assertFails(("tags: [agents, test]", "tags: [Agents]"), "tags must be")

    def test_missing_cover_file(self):
        self.assertFails(("status:", "cover: img/nope.webp\ncover_alt: x\nstatus:"), "cover file `img/nope.webp` does not exist")

    def test_published_todo(self):
        self.assertFails(("Intro paragraph.", "TODO: write this"), "still contains TODO")


class TestRender(SiteCase):
    def test_prompt_block_exact_text(self):
        self.add_post()
        self.build()
        page = (self.tmp / "builds" / "demo-post" / "index.html").read_text()
        m = re.search(r'<pre class="prompt-text" id="prompt-1" tabindex="0"><code>(.*?)</code></pre>', page, re.S)
        self.assertIsNotNone(m)
        text = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
        self.assertEqual(text, 'Build a thing for [YOUR CITY].\nUse "quotes" & <angle> brackets.')
        self.assertIn('<mark class="slot">[YOUR CITY]</mark>', page)
        self.assertIn('data-copy="prompt-1"', page)

    def test_known_sections_wrapped(self):
        self.add_post()
        self.build()
        page = (self.tmp / "builds" / "demo-post" / "index.html").read_text()
        for kind in ("agent", "needs", "steps", "gotchas", "result"):
            self.assertIn(f'class="part part-{kind}"', page)
        self.assertIn("Get the prompt", page)
        self.assertIn("min read", page)

    def test_toc_only_on_long_posts(self):
        self.add_post()
        self.build()
        page = (self.tmp / "builds" / "demo-post" / "index.html").read_text()
        self.assertIn('class="toc-side"', page)
        self.assertIn('class="toc-mobile"', page)
        raw = POST.format(slug="short-post", status="published", title="Short one here", extra="")
        raw = raw.split("## Give this")[0]
        self.add_post(slug="short-post", raw=raw)
        self.build()
        short = (self.tmp / "builds" / "short-post" / "index.html").read_text()
        self.assertNotIn('class="toc-side"', short)

    def test_index_badge_feed_sitemap(self):
        self.add_post()
        self.build()
        index = (self.tmp / "builds" / "index.html").read_text()
        self.assertIn("includes prompt", index)
        self.assertNotIn('name="robots" content="noindex"', index)
        self.assertIn("https://vatsalmishra.org/builds/demo-post/", (self.tmp / "builds" / "feed.xml").read_text())
        self.assertIn("https://vatsalmishra.org/builds/demo-post/", (self.tmp / "sitemap.xml").read_text())
        self.assertIn("builds/demo-post/", (self.tmp / "index.html").read_text())

    def test_empty_state(self):
        self.build()
        index = (self.tmp / "builds" / "index.html").read_text()
        self.assertIn("First build coming soon", index)
        self.assertIn('name="robots" content="noindex"', index)
        self.assertNotIn("/builds/", (self.tmp / "sitemap.xml").read_text())
        self.assertIn("First build coming soon", (self.tmp / "index.html").read_text())
        self.assertEqual(self.check()[0], [])

    def test_draft_excluded_everywhere(self):
        self.add_post(status="draft")
        self.build()
        self.assertFalse((self.tmp / "builds" / "demo-post" / "index.html").exists())
        for rel in ("builds/index.html", "builds/feed.xml", "sitemap.xml", "index.html"):
            self.assertNotIn("demo-post", (self.tmp / rel).read_text(), rel)
        self.assertEqual(self.check()[0], [])

    def test_include_drafts_writes_to_preview_only(self):
        self.add_post(status="draft")
        self.build()
        before = {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()}
        out = self.tmp / ".preview"
        self.build(include_drafts=True, out=out)
        after = {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file() and ".preview" not in p.parts}
        self.assertEqual(before, after)
        page = (out / "builds" / "demo-post" / "index.html").read_text()
        self.assertIn("Draft preview", page)
        self.assertIn('content="noindex"', page)
        self.assertIn("demo-post", (out / "builds" / "index.html").read_text())
        self.assertNotIn("demo-post", (out / "builds" / "feed.xml").read_text())
        self.assertNotIn("demo-post", (out / "sitemap.xml").read_text())

    def test_publish_then_draft_removes_page(self):
        d = self.add_post()
        self.build()
        self.assertTrue((d / "index.html").exists())
        p = d / "post.md"
        p.write_text(p.read_text().replace("status: published", "status: draft"))
        failures, _ = self.check()
        self.assertTrue(any("generated page for a draft" in f for f in failures), failures)
        self.build()
        self.assertFalse((d / "index.html").exists())

    def test_deterministic_and_idempotent(self):
        self.add_post()
        self.build()
        first = {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()}
        out = self.build()
        self.assertNotIn("wrote", out)
        self.assertEqual(first, {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()})

    def test_crlf_source_gives_identical_output(self):
        self.add_post()
        self.build()
        lf = (self.tmp / "builds" / "demo-post" / "index.html").read_bytes()
        p = self.tmp / "builds" / "demo-post" / "post.md"
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        self.build()
        self.assertEqual(lf, (self.tmp / "builds" / "demo-post" / "index.html").read_bytes())
        self.assertNotIn(b"\r", lf)

    def test_homepage_bytes_outside_markers_untouched(self):
        self.add_post()
        before = (self.tmp / "index.html").read_text()
        self.build()
        after = (self.tmp / "index.html").read_text()
        s0, e0 = before.index(builds.MARK_START), before.index(builds.MARK_END)
        s1, e1 = after.index(builds.MARK_START), after.index(builds.MARK_END)
        self.assertEqual(before[:s0], after[:s1])
        self.assertEqual(before[e0:], after[e1:])
        self.assertNotEqual(before, after)

    def test_hand_edit_detected(self):
        self.add_post()
        self.build()
        f = self.tmp / "builds" / "demo-post" / "index.html"
        f.write_text(f.read_text().replace("Intro paragraph.", "Edited by hand."))
        failures, _ = self.check()
        self.assertTrue(any("out of date or hand-edited" in x for x in failures), failures)

    def test_figure_dimensions_and_caption(self):
        d = self.add_post(extra='\n![A red square](img/sq.webp "The caption")\n')
        Image.new("RGB", (40, 30), "red").save(d / "img" / "sq.webp", "WEBP")
        self.build()
        page = (d / "index.html").read_text()
        self.assertRegex(page, r'<figure><img alt="A red square" decoding="async" height="30" loading="lazy" src="img/sq.webp" width="40"\s*/?><figcaption>The caption</figcaption></figure>')
        self.assertEqual(self.check()[0], [])


class TestChecks(SiteCase):
    def failures_for(self, extra):
        self.add_post(extra=extra)
        self.build()
        return self.check()[0]

    def test_private_path(self):
        self.assertTrue(any("private path" in f for f in self.failures_for("\nSee /home/someone/notes.\n")))

    def test_ip_address(self):
        self.assertTrue(any("IP address 192.168.1.20" in f for f in self.failures_for("\nServer at 192.168.1.20.\n")))

    def test_localhost_ip_allowed(self):
        self.assertEqual(self.failures_for("\nServe on 127.0.0.1:8000.\n"), [])

    def test_private_hostname(self):
        self.assertTrue(any("private hostname" in f for f in self.failures_for("\nOpen box.tail1234.ts.net\n")))

    def test_token(self):
        self.assertTrue(any("GitHub token" in f for f in self.failures_for("\nghp_" + "a1B2" * 9 + "\n")))

    def test_email(self):
        self.assertTrue(any("email address" in f for f in self.failures_for("\nMail someone@example.com\n")))

    def test_employer_flags(self):
        f = self.failures_for("\nSee go/some-link and b/123456789.\n")
        self.assertTrue(any("go/ link" in x for x in f), f)
        self.assertTrue(any("bug ID" in x for x in f), f)

    def test_raw_html_rejected(self):
        f = self.failures_for('\n<script>alert(1)</script>\n<div onclick="x">hi</div>\n')
        self.assertTrue(any("raw HTML <script>" in x for x in f), f)
        self.assertTrue(any("raw HTML <div>" in x for x in f), f)
        self.assertTrue(any("<script> is not allowed" in x for x in f), f)

    def test_allowed_raw_html_and_code_ignored(self):
        f = self.failures_for("\n<details><summary>More</summary>\n\nHidden text.\n\n</details>\n\n`<div>` in code is fine.\n")
        self.assertEqual(f, [])

    def test_fence_inside_list_flagged(self):
        f = self.failures_for("\n1. Step\n\n   ```bash\n   echo hi\n   ```\n")
        self.assertTrue(any("fenced code inside a list" in x for x in f), f)

    def test_missing_alt(self):
        d = self.tmp / "builds" / "demo-post"
        f = self.failures_for('\n<figure><img src="img/x.webp"></figure>\n')
        self.assertTrue(any("missing alt" in x for x in f), f)

    def test_broken_link(self):
        f = self.failures_for("\n[gone](/nowhere/) and [anchor](#no-such-heading)\n")
        self.assertTrue(any("broken link `/nowhere/`" in x for x in f), f)
        self.assertTrue(any("missing #no-such-heading" in x for x in f), f)

    def test_denylist_env_and_file(self):
        self.add_post(extra="\nWe live near Fakestreet Gardens.\n")
        self.build()
        os.environ["PRIVACY_DENYLIST"] = "fakestreet gardens\nother place"
        failures, warnings = self.check()
        self.assertTrue(any("private denylist term #1" in f for f in failures), failures)
        self.assertFalse(any("Fakestreet" in f or "fakestreet" in f for f in failures), "term must not be printed")
        self.assertFalse(any("denylist is NOT configured" in w for w in warnings))
        del os.environ["PRIVACY_DENYLIST"]
        dl = self.tmp / "denylist.txt"
        dl.write_text("# comment\nFakestreet\n")
        os.environ["BUILDS_DENYLIST_FILE"] = str(dl)
        failures, _ = self.check()
        self.assertTrue(any("private denylist term #1" in f for f in failures), failures)

    def test_image_with_exif_fails_and_images_cmd_strips_it(self):
        d = self.add_post()
        src = self.tmp / "photo.jpg"
        im = Image.new("RGB", (2400, 1600), "blue")
        exif = Image.Exif()
        exif[0x010F] = "PhoneMaker"  # Make
        exif[0x8825] = {2: (53.0, 20.0, 0.0)}  # GPSInfo
        im.save(src, "JPEG", exif=exif.tobytes())
        shutil.copy(src, d / "img" / "raw.jpg")
        self.build()
        failures, _ = self.check()
        self.assertTrue(any("metadata (EXIF" in f for f in failures), failures)
        (d / "img" / "raw.jpg").unlink()
        rc, out = quiet(builds.cmd_images, self.tmp, "demo-post", [str(src)], True)
        self.assertEqual(rc, 0, out)
        with Image.open(d / "img" / "cover.webp") as im2:
            self.assertEqual(im2.width, 1600)
            self.assertEqual(builds.image_metadata(im2), [])
        with Image.open(d / "img" / "og.jpg") as og:
            self.assertEqual(og.size, (1200, 630))
            self.assertEqual(builds.image_metadata(og), [])
        self.build()  # og.jpg now exists, so the page's og:image changes
        self.assertEqual(self.check()[0], [])

    def test_video_and_stray_files_rejected(self):
        d = self.add_post()
        (d / "img" / "clip.mp4").write_bytes(b"0" * 10)
        (d / "notes.txt").write_text("x")
        self.build()
        f = self.check()[0]
        self.assertTrue(any("video/GIF" in x for x in f), f)
        self.assertTrue(any("unexpected file" in x for x in f), f)

    def test_skin_drift(self):
        self.add_post()
        self.build()
        css = self.tmp / "assets" / "css" / "builds.css"
        css.write_text(css.read_text().replace("#101827", "#000000"))
        self.build()
        self.assertTrue(any("skin drift" in f for f in self.check()[0]))

    def test_new_scaffold_is_valid_draft(self):
        rc, out = quiet(builds.cmd_new, self.tmp, "fresh-post")
        self.assertEqual(rc, 0, out)
        self.build()
        self.assertEqual(self.check()[0], [])
        rc, out = quiet(builds.cmd_new, self.tmp, "fresh-post")
        self.assertEqual(rc, 1)
        rc, out = quiet(builds.cmd_new, self.tmp, "Bad_Slug")
        self.assertEqual(rc, 1)


class TestRealRepo(unittest.TestCase):
    """The committed site must be built and pass its own check."""

    def test_repo_check_passes(self):
        problems = builds.run_checks(REPO)
        self.assertEqual(problems.failures, [])

    def test_nojekyll_present(self):
        self.assertTrue((REPO / ".nojekyll").is_file())


if __name__ == "__main__":
    unittest.main()
