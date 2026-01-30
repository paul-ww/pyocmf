"""Main CLI application."""

from __future__ import annotations

import sys

import typer

from pyocmf.cli import commands

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


def main() -> None:
    """Run the CLI with default command handling."""
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
