"""CLI commands for pyocmf."""

from __future__ import annotations

import contextlib
import sys
from typing import TYPE_CHECKING, Annotated

import typer

from pyocmf.compliance import IssueSeverity
from pyocmf.core.ocmf import OCMF
from pyocmf.exceptions import PyOCMFError

from .display import console, display_compliance_result, display_ocmf_structure, verify_signature
from .utils import (
    InputType,
    detect_input_type,
    load_ocmf,
    load_xml_container,
    parse_ocmf_string,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from pyocmf.utils.xml import OcmfRecord


StrictOption = Annotated[
    bool,
    typer.Option("--strict", help="Reject input that deviates from the OCMF spec"),
]


@contextlib.contextmanager
def _exit_on_error() -> Generator[None]:
    try:
        yield
    except PyOCMFError as e:
        console.print(f"[red]✗[/red] OCMF parsing failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)


def _resolve_public_key(record: OcmfRecord, public_key: str | None) -> str | None:
    if public_key:
        return public_key
    if record.public_key:
        return record.public_key.key
    return record.ocmf.embedded_public_key


def all_checks(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    public_key: Annotated[
        str | None,
        typer.Option("--public-key", "-k", help="Public key, hex or base64"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed OCMF structure and warnings"),
    ] = False,
    strict: StrictOption = False,
) -> None:
    """Run both signature verification and compliance check (default command)."""
    with _exit_on_error():
        input_type = detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            container = load_xml_container(ocmf_input, strict=strict)
            record = container[0]
            ocmf = record.ocmf
            key_to_use = _resolve_public_key(record, public_key)
        else:
            ocmf = parse_ocmf_string(ocmf_input, strict=strict)
            key_to_use = public_key or ocmf.embedded_public_key

        if key_to_use:
            verify_signature(ocmf, key_to_use)
        else:
            console.print(
                "[yellow]⚠[/yellow] No public key available - skipping signature verification"
            )

        console.print()
        issues = ocmf.check_eichrecht(errors_only=not verbose)
        display_compliance_result(issues, ocmf.is_eichrecht_compliant)

        if verbose:
            display_ocmf_structure(ocmf)


# Typer renders docstrings as Rich markup; the backslash keeps [crypto] from vanishing
def verify(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    public_key: Annotated[
        str | None,
        typer.Option("--public-key", "-k", help="Public key, hex or base64"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed OCMF structure"),
    ] = False,
    all_entries: Annotated[
        bool,
        typer.Option("--all", help="Process all entries in XML file"),
    ] = False,
    strict: StrictOption = False,
) -> None:
    r"""Verify cryptographic signature only (requires pyocmf\[crypto])."""
    with _exit_on_error():
        input_type = detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _verify_from_xml(ocmf_input, verbose, all_entries, public_key, strict=strict)
        else:
            ocmf = parse_ocmf_string(ocmf_input, strict=strict)
            _verify_single_ocmf(ocmf, verbose, public_key or ocmf.embedded_public_key)


def check(
    input1: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    input2: Annotated[
        str | None,
        typer.Argument(help="Second OCMF for transaction pair (optional)"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show warnings in addition to errors"),
    ] = False,
    strict: StrictOption = False,
) -> None:
    """Check Eichrecht regulatory compliance.

    Transaction checks need a begin and an end reading, either within one record or
    as a begin and an end record.
    """
    with _exit_on_error():
        ocmf1 = load_ocmf(input1, strict=strict)

        if input2:
            ocmf2 = load_ocmf(input2, strict=strict)
            issues = ocmf1.check_eichrecht(other=ocmf2, errors_only=not verbose)
            is_compliant = not any(i.severity == IssueSeverity.ERROR for i in issues)
            label = "transaction pair"
        else:
            console.print(
                "[yellow]ℹ[/yellow] Single OCMF record: transaction checks only run if it "  # ruff: ignore[ambiguous-unicode-character-string]
                "holds both the begin and the end reading. Otherwise pass both records:"
            )
            console.print("  [dim]ocmf check <begin-ocmf> <end-ocmf>[/dim]\n")
            issues = ocmf1.check_eichrecht(errors_only=not verbose)
            is_compliant = ocmf1.is_eichrecht_compliant
            label = None

        display_compliance_result(issues, is_compliant, label)


def inspect(
    ocmf_input: Annotated[
        str,
        typer.Argument(help="OCMF string, hex-encoded string, or path to XML file"),
    ],
    strict: StrictOption = False,
) -> None:
    """Display parsed OCMF structure."""
    with _exit_on_error():
        input_type = detect_input_type(ocmf_input)

        if input_type == InputType.XML:
            _inspect_from_xml(ocmf_input, strict=strict)
        else:
            display_ocmf_structure(parse_ocmf_string(ocmf_input, strict=strict))


def _verify_single_ocmf(ocmf: OCMF, verbose: bool, public_key: str | None) -> None:
    if not public_key:
        console.print("[yellow]⚠[/yellow] No public key provided")
        if ocmf.signature.SA:
            console.print("[yellow]ℹ[/yellow] Signature present but not verified")  # ruff: ignore[ambiguous-unicode-character-string]
        if verbose:
            display_ocmf_structure(ocmf)
        return

    verify_signature(ocmf, public_key)

    if verbose:
        display_ocmf_structure(ocmf)


def _verify_from_xml(
    xml_path: str, verbose: bool, all_entries: bool, public_key: str | None, *, strict: bool
) -> None:
    container = load_xml_container(xml_path, strict=strict)
    records_to_process = container.entries if all_entries else [container[0]]

    console.print(f"[green]✓[/green] Found {len(container)} OCMF record(s) in XML file")

    for i, record in enumerate(records_to_process, 1):
        if len(records_to_process) > 1:
            console.print(f"\n[bold cyan]Entry {i}/{len(records_to_process)}:[/bold cyan]")

        key_to_use = _resolve_public_key(record, public_key)
        _verify_single_ocmf(record.ocmf, verbose, key_to_use)


def _inspect_from_xml(xml_path: str, *, strict: bool) -> None:
    container = load_xml_container(xml_path, strict=strict)
    console.print(f"Found {len(container)} OCMF record(s) in XML file\n")

    for i, record in enumerate(container.entries, 1):
        if i > 1:
            console.print()
        if len(container) > 1:
            console.print(f"[bold cyan]Entry {i}/{len(container)}:[/bold cyan]")
        display_ocmf_structure(record.ocmf)
