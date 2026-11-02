import pytest

from url2md.cli import main


def test_prints_markdown_with_absolute_links(server, capsys):
    assert main([f"{server}/links/page.html"]) == 0
    out = capsys.readouterr().out
    assert "# Title" in out
    assert f"[Guide]({server}/docs/guide)" in out
    assert f"![logo]({server}/links/img/logo.png)" in out


def test_base_href_is_used_for_relative_links(server, capsys):
    assert main([f"{server}/base.html"]) == 0
    assert "[File](https://cdn.example/assets/file.pdf)" in capsys.readouterr().out


@pytest.mark.parametrize("path", ["/latin1-header.html", "/latin1-meta.html"])
def test_declared_charset_is_honoured(server, capsys, path):
    assert main([f"{server}{path}"]) == 0
    assert "Éléphant à côté" in capsys.readouterr().out


@pytest.mark.parametrize("flag", [None, "-o"])
def test_writes_output_file(server, tmp_path, flag):
    target = tmp_path / "page.md"
    args = [f"{server}/links/page.html", *([flag] if flag else []), str(target)]
    assert main(args) == 0
    assert target.read_text(encoding="utf-8").startswith("# Title")


def test_http_error_fails_and_leaves_existing_file_untouched(server, tmp_path, capsys):
    target = tmp_path / "page.md"
    target.write_text("precious", encoding="utf-8")
    assert main([f"{server}/missing.html", str(target)]) == 1
    assert "404" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "precious"


def test_unreachable_host_fails(capsys):
    assert main(["http://127.0.0.1:9/"]) == 1
    assert capsys.readouterr().err.startswith("url2md: ")


def test_redirect_to_another_page_warns_but_still_outputs(server, capsys):
    assert main([f"{server}/to-login"]) == 0
    captured = capsys.readouterr()
    assert f"url2md: redirected to {server}/login" in captured.err
    assert "# Log in" in captured.out


def test_harmless_redirect_does_not_warn(server, capsys):
    assert main([f"{server}/trailing"]) == 0
    assert capsys.readouterr().err == ""


def test_empty_page_suggests_js(server, capsys):
    assert main([f"{server}/js.html"]) == 1
    assert "try -j" in capsys.readouterr().err


def test_output_argument_and_option_conflict(server):
    with pytest.raises(SystemExit) as exit_info:
        main([f"{server}/links/page.html", "a.md", "-o", "b.md"])
    assert exit_info.value.code == 2


@pytest.mark.browser
def test_js_flag_renders_javascript(server, capsys):
    assert main([f"{server}/js.html", "-j"]) == 0
    assert "# Rendered by JS" in capsys.readouterr().out


@pytest.mark.browser
def test_js_flag_reports_http_errors(server, capsys):
    assert main(["-j", f"{server}/missing.html"]) == 1
    assert "404" in capsys.readouterr().err
