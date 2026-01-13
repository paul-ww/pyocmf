"""Display functions for CLI output."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyocmf.compliance import EichrechtIssue, IssueSeverity
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import SignatureVerificationError

console = Console()


def verify_signature(ocmf: OCMF, public_key: str) -> None:
    """Verify signature and display results."""
    try:
        is_valid = ocmf.verify_signature(public_key)

        if is_valid:
            console.print(
                "\n[green]✓[/green] Signature verification: [bold green]VALID[/bold green]"
            )

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_row("Algorithm:", ocmf.signature.SA or "N/A")
            table.add_row("Encoding:", ocmf.signature.SE or "hex")

            console.print(table)
        else:
            console.print("\n[red]✗[/red] Signature verification: [bold red]INVALID[/bold red]")
            console.print("[yellow]⚠[/yellow] The signature does not match the payload")
            sys.exit(1)

    except SignatureVerificationError as e:
        console.print(f"\n[red]✗[/red] Signature verification failed: {e}")
        sys.exit(1)
    except ImportError as e:
        console.print(f"\n[red]✗[/red] {e}")
        console.print("[yellow]ℹ[/yellow] Install with: pip install pyocmf[crypto]")
        sys.exit(1)


def display_compliance_result(
    issues: list[EichrechtIssue], is_compliant: bool, label: str | None = None
) -> None:
    """Display compliance check results."""
    label_str = f" {label}" if label else ""

    if not issues:
        console.print(
            f"\n[green]✓[/green] Eichrecht compliance: "
            f"[bold green]COMPLIANT{label_str}[/bold green]"
        )
        return

    errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
    warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]

    if errors:
        console.print(
            f"\n[red]✗[/red] Eichrecht compliance: [bold red]NOT COMPLIANT{label_str}[/bold red]"
        )
    else:
        console.print(
            f"\n[yellow]⚠[/yellow] Eichrecht compliance: "
            f"[bold yellow]COMPLIANT WITH WARNINGS{label_str}[/bold yellow]"
        )

    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for issue in errors:
            _display_issue(issue)

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for issue in warnings:
            _display_issue(issue)

    if not is_compliant:
        sys.exit(1)


def _display_issue(issue: EichrechtIssue) -> None:
    """Display a single compliance issue."""
    field_str = f"[{issue.field}] " if issue.field else ""
    console.print(f"  {field_str}{issue.message} ({issue.code.value})")


def display_ocmf_structure(ocmf: OCMF) -> None:
    """Display the parsed OCMF structure."""
    console.print("\n[bold]OCMF Structure:[/bold]")

    console.print("\n[bold cyan]Payload:[/bold cyan]")
    payload_table = Table(show_header=False, box=None, padding=(0, 2))
    payload_table.add_row("Format Version:", ocmf.payload.FV)
    payload_table.add_row("Gateway ID:", ocmf.payload.GI)
    payload_table.add_row("Gateway Serial:", ocmf.payload.GS)
    payload_table.add_row("Pagination:", ocmf.payload.PG)
    console.print(payload_table)

    if ocmf.payload.RD:
        console.print(f"\n[bold cyan]Readings:[/bold cyan] {len(ocmf.payload.RD)} reading(s)")
        for i, reading in enumerate(ocmf.payload.RD, 1):
            reading_table = Table(show_header=False, box=None, padding=(0, 2))
            reading_table.add_row("Time:", str(reading.TM))
            reading_table.add_row("Type:", reading.TX)
            reading_table.add_row("Value:", f"{reading.RV} {reading.RU}")
            reading_table.add_row("Identifier:", str(reading.RI) if reading.RI else "N/A")
            reading_table.add_row("Status:", reading.ST)
            console.print(Panel(reading_table, title=f"Reading {i}", border_style="cyan"))

    console.print("\n[bold cyan]Signature:[/bold cyan]")
    sig_table = Table(show_header=False, box=None, padding=(0, 2))
    sig_table.add_row("Algorithm:", ocmf.signature.SA or "N/A")
    sig_table.add_row("Encoding:", ocmf.signature.SE or "hex")
    sig_table.add_row(
        "Data:",
        f"{ocmf.signature.SD[:32]}..." if len(ocmf.signature.SD) > 32 else ocmf.signature.SD,
    )
    console.print(sig_table)
