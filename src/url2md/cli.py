import argparse
import sys
from pathlib import Path

from url2md.core import Url2mdError, absolutize_links, fetch, render, same_page, to_markdown


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="url2md",
        description="Convert a web page to Markdown.",
    )
    parser.add_argument("url", help="page address (https:// is added when missing)")
    parser.add_argument("output", nargs="?", type=Path, help="Markdown file (default: stdout)")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_option",
        type=Path,
        metavar="FILE",
        help="Markdown file, same as the output argument",
    )
    parser.add_argument(
        "-j",
        "--js",
        action="store_true",
        help="render the page in headless Chromium, for sites built with JavaScript",
    )
    args = parser.parse_args(argv)
    if args.output and args.output_option:
        parser.error("give a single output file: either output or -o")
    args.output = args.output or args.output_option
    if "://" not in args.url:
        args.url = f"https://{args.url}"
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        page = (render if args.js else fetch)(args.url)
        markdown = to_markdown(absolutize_links(page))
    except Url2mdError as error:
        print(f"url2md: {error}", file=sys.stderr)
        return 1

    # A redirect to another page (login wall, home page) yields Markdown that isn't the
    # requested page: say so, without blocking the output
    if not same_page(args.url, page.url):
        print(f"url2md: redirected to {page.url}", file=sys.stderr)

    if not markdown.strip():
        hint = "" if args.js else "; if the site is built with JavaScript, try -j"
        print(f"url2md: no content extracted{hint}", file=sys.stderr)
        return 1

    # Written only once the conversion succeeded: a failure leaves an existing file untouched
    markdown = markdown.strip() + "\n"
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0
