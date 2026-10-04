"""Main CLI application."""

from __future__ import annotations

import sys
import warnings
from typing import TextIO

import typer

from pyocmf.cli import commands
from pyocmf.cli.display import console

CMD = "ocmf"

app = typer.Typer(
    name=CMD,
    help="Verify OCMF signatures and check regulatory compliance",
    add_completion=False,
    no_args_is_help=True,
)

app.command(name="all")(commands.all_checks)
app.command()(commands.verify)
app.command()(commands.check)
app.command()(commands.inspect)


def _print_warning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: TextIO | None = None,
    line: str | None = None,
) -> None:
    console.print(f"[yellow]⚠[/yellow] {message}")


def main() -> None:
    """Run the CLI with default command handling."""
    # ty treats module functions as non-assignable even with a matching signature
    warnings.showwarning = _print_warning  # ty: ignore[invalid-assignment]
    if len(sys.argv) == 1:
        app(["--help"])
    elif (
        len(sys.argv) >= 2
        and not sys.argv[1].startswith("-")
        and sys.argv[1] not in ["verify", "check", "inspect", "all"]
    ):
        sys.argv.insert(1, "all")

    app()


if __name__ == "__main__":
    main()
