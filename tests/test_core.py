import pytest

from url2md import same_page


@pytest.mark.parametrize(
    ("requested", "final"),
    [
        ("http://example.com/a", "https://example.com/a"),
        ("https://example.com/a", "https://www.example.com/a"),
        ("https://example.com/a", "https://example.com/a/"),
        ("https://example.com/a", "https://example.com/a?ref=1"),
    ],
)
def test_harmless_redirects_are_the_same_page(requested, final):
    assert same_page(requested, final)


@pytest.mark.parametrize(
    ("requested", "final"),
    [
        ("https://old.example.com/post/1", "https://old.example.com/login/?dest=post"),
        ("https://example.com/a", "https://other.example/a"),
    ],
)
def test_other_pages_are_not_the_same_page(requested, final):
    assert not same_page(requested, final)
