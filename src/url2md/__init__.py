"""Convert a web page to Markdown."""

from url2md.core import Page, Url2mdError, absolutize_links, fetch, render, same_page, to_markdown

__all__ = ["Page", "Url2mdError", "absolutize_links", "fetch", "render", "same_page", "to_markdown"]
