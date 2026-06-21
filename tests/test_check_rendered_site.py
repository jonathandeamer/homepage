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
<meta name="description" content="Places you can find me online, and ways to get in touch.">
<meta name="theme-color" content="#203125">
<link rel="canonical" href="{SITE}/">
<link rel="me" href="https://tilde.zone/@JonathanDeamer">
<meta property="og:title" content="Jonathan Deamer">
<meta property="og:description" content="Places you can find me online, and ways to get in touch.">
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


LLMS_TXT = f"""# Jonathan Deamer

> Personal homepage for Jonathan Deamer, with links to places he can be found online and ways to get in touch.

## Key Pages

- [Homepage]({SITE}/): Personal calling-card homepage.

## Contact

- [Email](mailto:jonathandeamer@gmail.com): Direct contact.

## Professional

- [LinkedIn](https://www.linkedin.com/in/jonathandeamer/): Work history and professional background.

## Elsewhere

- [Wikipedia](https://en.wikipedia.org/wiki/User:Jonathan_Deamer): Wikipedia user page.
- [Strava](https://www.strava.com/athletes/18361576): Cycling and running activity.
- [GitHub](https://github.com/jonathandeamer): Software projects and code.

## Social

- [Bluesky](https://bsky.app/profile/jonathandeamer.bsky.social): Social posts.
- [Mastodon](https://tilde.zone/@JonathanDeamer): Fediverse account verified from this site.
- [Threads](https://www.threads.net/@jonathandeamer): Social posts.
- [Twitter](https://twitter.com/JonathanDeamer): Older social account.

## Related

- [Small Observations](https://smallobservations.net/): Jonathan's notebook of street art photography.
- [Homepage source](https://github.com/jonathandeamer/homepage): Source code for this website.
- [Portrait photo](https://www.flickr.com/photos/jonathandeamer/50782596227/): Source photo used on the homepage.
- [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/): Content licence unless otherwise stated.
"""

GITHUB_URL = "https://github.com/jonathandeamer"
BLUESKY_URL = "https://bsky.app/profile/jonathandeamer.bsky.social"

HOME_BODY = f"""
<article class="card h-card">
  <h1 class="p-name">Jonathan Deamer</h1>
  <p class="intro p-note">Places you can find me online.</p>
  <a class="u-email" href="mailto:jonathandeamer@gmail.com">Email</a>
  <a href="{GITHUB_URL}" rel="me">GitHub</a>
  <a href="{BLUESKY_URL}" rel="me">Bluesky</a>
  <a href="https://tilde.zone/@JonathanDeamer" rel="me">Mastodon</a>
  <img class="u-photo" src="/img/portrait.png" alt="Photo of Jonathan Deamer">
  <data class="u-url u-uid" value="{SITE}/"></data>
</article>
"""


def page(head: str, body: str = "<h1>Jonathan Deamer</h1>") -> str:
    return f"<!doctype html><html lang='en-gb'><head>{head}</head><body>{body}</body></html>"


class RenderedSiteAuditTests(TestCase):
    def test_accepts_valid_rendered_site(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY))
            write(root / "404.html", page(NOT_FOUND_HEAD, "<h1>404: there's nothing here</h1>"))
            write(root / "sitemap.xml", f"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>{SITE}/</loc></url></urlset>")
            write(root / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
            write(root / "llms.txt", LLMS_TXT)

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
                    "llms.txt: missing file",
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

    def test_accepts_valid_h_card(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY))
            self.assertEqual(audit_home_card(root / "index.html"), [])

    def test_reports_missing_h_card_root(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace("card h-card", "card")))
            self.assertIn("index.html: missing h-card root", audit_home_card(root / "index.html"))

    def test_reports_missing_h_card_property(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace('class="u-photo"', 'class="portrait"')))
            self.assertIn("index.html: missing u-photo in h-card", audit_home_card(root / "index.html"))

    def test_reports_self_url_not_apex(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace(f'value="{SITE}/"', 'value="https://example.com/"')))
            self.assertIn(f"index.html: missing u-url/u-uid resolving to {SITE}/", audit_home_card(root / "index.html"))

    def test_accepts_anchor_self_url(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = HOME_BODY.replace(
                f'<data class="u-url u-uid" value="{SITE}/"></data>',
                f'<a class="u-url u-uid" href="{SITE}/"></a>',
            )
            write(root / "index.html", page(HOME_HEAD, body))
            self.assertEqual(audit_home_card(root / "index.html"), [])

    def test_reports_missing_rel_me_profile(self) -> None:
        from scripts.check_rendered_site import audit_home_card
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "index.html", page(HOME_HEAD, HOME_BODY.replace(f'href="{GITHUB_URL}" rel="me"', f'href="{GITHUB_URL}"')))
            self.assertIn("index.html: missing rel=me for GitHub", audit_home_card(root / "index.html"))
