from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.check_rendered_site import audit_rendered_site


SITE = "https://jonathandeamer.com"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


HOME_HEAD = f"""
<title>Jonathan Deamer</title>
<meta name="description" content="Places you can find Jonathan Deamer online, and ways to get in touch.">
<meta name="theme-color" content="#203125">
<link rel="canonical" href="{SITE}/">
<link rel="me" href="https://tilde.zone/@JonathanDeamer">
<meta property="og:title" content="Jonathan Deamer">
<meta property="og:description" content="Places you can find Jonathan Deamer online, and ways to get in touch.">
<meta property="og:url" content="{SITE}/">
<meta name="twitter:card" content="summary_large_image">
"""


NOT_FOUND_HEAD = f"""
<title>404 — Jonathan Deamer</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="404 error">
<meta name="theme-color" content="#203125">
<link rel="canonical" href="{SITE}/404.html">
<link rel="me" href="https://tilde.zone/@JonathanDeamer">
<meta property="og:title" content="404 — Jonathan Deamer">
<meta property="og:description" content="404 error">
<meta property="og:url" content="{SITE}/404.html">
<meta name="twitter:card" content="summary">
"""


def page(head: str, body: str = "<h1>Jonathan Deamer</h1>") -> str:
    return f"<!doctype html><html lang='en-gb'><head>{head}</head><body>{body}</body></html>"


class RenderedSiteAuditTests(TestCase):
    def test_accepts_valid_rendered_site(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", f"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>{SITE}/</loc></url></urlset>")
            write(root / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

            self.assertEqual(audit_rendered_site(root), [])

    def test_reports_missing_files_and_unwanted_feeds(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "feed.xml", "<rss></rss>")
            write(root / "index.xml", "<rss></rss>")

            self.assertEqual(
                audit_rendered_site(root),
                [
                    "index.html: missing file",
                    "404.html: missing file",
                    "feed.xml: RSS/feed output must not be generated",
                    "index.xml: RSS/feed output must not be generated",
                    "sitemap.xml: missing file",
                    "robots.txt: missing file",
                ],
            )

    def test_reports_missing_home_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page("<title></title>"))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", "<?xml version='1.0'?><urlset></urlset>")
            write(root / "robots.txt", "User-agent: *\n")

            self.assertIn("index.html: missing non-empty canonical link", audit_rendered_site(root))
            self.assertIn("index.html: missing rel=me link", audit_rendered_site(root))

    def test_reports_canonical_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong_canonical = HOME_HEAD.replace(f'href="{SITE}/"', 'href="https://example.com/"')
            write(root / "index.html", page(wrong_canonical))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", f"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>{SITE}/</loc></url></urlset>")
            write(root / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

            self.assertIn(
                f"index.html: canonical 'https://example.com/' does not match expected '{SITE}/'",
                audit_rendered_site(root),
            )
