"""Basic tests for autopage."""

from autopage import __version__
from autopage.cli import main


def test_version():
    """Version string is set."""
    assert __version__ == "0.1.0"


def test_cli_help(capsys):
    """CLI prints help when no arguments given."""
    rc = main([])
    assert rc == 1
    captured = capsys.readouterr()
    assert "autopage" in captured.out


def test_cli_version(capsys):
    """CLI --version flag works."""
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out
