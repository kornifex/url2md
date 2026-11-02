import contextlib
import io
import subprocess
import sys
from email.message import Message
from typing import NamedTuple
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from markitdown import MarkItDown, StreamInfo

# Some sites turn away clients that don't look like a browser
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
TIMEOUT_S = 30
# Lets JavaScript-built pages load their data without hanging on pages that keep a
# connection open (analytics, long polling)
NETWORK_IDLE_TIMEOUT_MS = 5000


class Url2mdError(Exception):
    """A page could not be retrieved."""


class Page(NamedTuple):
    html: str
    url: str
    """Final URL, after redirects."""


def fetch(url: str) -> Page:
    """Download a page over HTTP, without running its JavaScript."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
        response.raise_for_status()
    except requests.RequestException as error:
        raise Url2mdError(str(error)) from error
    # The HTTP header's charset wins over the meta tag; without it, BeautifulSoup reads the
    # meta tag and then guesses. requests would assume ISO-8859-1 for any text/html.
    header = Message()
    header["content-type"] = response.headers.get("content-type", "")
    charset = header.get_content_charset()
    soup = BeautifulSoup(response.content, "html.parser", from_encoding=charset)
    return Page(str(soup), response.url)


def render(url: str) -> Page:
    """Load a page in headless Chromium and return the DOM once its JavaScript has run."""
    from playwright.sync_api import Error

    try:
        try:
            return _render(url)
        except Error as error:
            if "Executable doesn't exist" not in str(error):
                raise
        # First run on this machine: Playwright doesn't have its Chromium yet
        print("url2md: installing Chromium for Playwright…", file=sys.stderr)
        # On stderr, so that `url2md -j … > page.md` stays clean
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            stdout=sys.stderr,
        )
        return _render(url)
    except Error as error:
        raise Url2mdError(str(error).splitlines()[0]) from error


def _render(url: str) -> Page:
    from playwright.sync_api import TimeoutError, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            response = page.goto(url, timeout=TIMEOUT_S * 1000)
            if response is not None and not response.ok:
                raise Url2mdError(f"{response.status} {response.status_text} for url: {url}")
            with contextlib.suppress(TimeoutError):
                page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
            return Page(page.content(), page.url)
        finally:
            browser.close()


def same_page(requested: str, final: str) -> bool:
    """Whether a redirect is harmless (http → https, www., trailing slash, query string)."""

    def key(url: str) -> tuple[str, str]:
        parts = urlsplit(url)
        return parts.netloc.removeprefix("www."), parts.path.rstrip("/")

    return key(requested) == key(final)


def absolutize_links(page: Page) -> Page:
    """Relative links would lead nowhere once the page is saved as a .md file."""
    soup = BeautifulSoup(page.html, "html.parser")
    base = page.url
    if (tag := soup.find("base", href=True)) is not None:
        base = urljoin(page.url, tag["href"])
    for attribute in ("href", "src"):
        for element in soup.find_all(attrs={attribute: True}):
            element[attribute] = urljoin(base, element[attribute])
    return page._replace(html=str(soup))


def to_markdown(page: Page) -> str:
    # The URL lets markitdown pick its dedicated converters (Wikipedia, YouTube…)
    info = StreamInfo(mimetype="text/html", extension=".html", charset="utf-8", url=page.url)
    result = MarkItDown().convert_stream(io.BytesIO(page.html.encode("utf-8")), stream_info=info)
    return result.markdown
