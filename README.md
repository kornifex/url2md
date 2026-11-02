# url2md

Convert a web page to Markdown from the command line.

```sh
url2md https://example.com/article            # print Markdown to stdout
url2md https://example.com/article page.md    # write it to page.md
url2md -j https://app.example.com/dashboard   # render JavaScript first
```

url2md downloads the page and converts it with [markitdown](https://github.com/microsoft/markitdown). With `-j`, it loads the page in headless Chromium ([Playwright](https://playwright.dev/python/)) and converts the DOM once the JavaScript has run, for sites that build their content client-side.

## Install

With [uv](https://docs.astral.sh/uv/):

```sh
uv tool install git+https://github.com/kornifex/url2md
```

Upgrade with `uv tool upgrade url2md`.

The first `-j` run downloads Playwright's Chromium (about 150 MB) into Playwright's cache. Its progress goes to stderr.

## Usage

```
url2md [-h] [-o FILE] [-j] url [output]
```

| Option | Effect |
|---|---|
| `output`, `-o FILE` | Write the Markdown to a file instead of stdout |
| `-j`, `--js` | Render the page in headless Chromium before converting it |

Options can come before or after the URL, and `https://` is added when the URL has no scheme.

### What it does on top of markitdown

- **Absolute links.** Relative links and image sources are resolved against the page URL (or its `<base href>`), so they still work once the page is saved as a `.md` file.
- **Charset.** The charset from the `Content-Type` header wins over the `<meta>` tag, as browsers do.
- **Failures are visible.** An HTTP error or a network failure exits with status 1 and a message on stderr. The output file is written only once the conversion succeeded, so a failure never empties an existing file.
- **Redirects are reported.** When the site redirects to another page, such as a login wall, url2md prints `url2md: redirected to …` on stderr and still outputs the Markdown of that page. Harmless redirects (http → https, `www.`, trailing slash, query string) are not reported.
- **Empty pages.** When nothing could be extracted, url2md exits with status 1 and suggests `-j`.

### Limits

url2md doesn't log in: pages behind a login wall give the Markdown of the login page, with a redirect warning. For finer control (a CSS selector, a longer wait, an authenticated session), render the page with [shot-scraper](https://shot-scraper.datasette.io/) and pipe it to markitdown:

```sh
uvx shot-scraper html https://example.com -s main --wait 2000 | uvx markitdown -x html
```

## Development

```sh
uv sync
uv run pytest                          # fast tests, local HTTP server only
uv run pytest -m browser               # tests that need Chromium
uv run ruff check && uv run ruff format --check
```

## Credits

url2md was built with the help of [Claude](https://claude.ai), Anthropic's AI assistant.

## License

[MIT](LICENSE)
