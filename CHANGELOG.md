# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-30

Initial public release.

### Added

- **Core OCMF parsing**: Parse OCMF strings into validated Python objects with Pydantic
- **Automatic format detection**: Hex-encoded OCMF strings are automatically detected and decoded
- **Signature verification**: ECDSA signature verification with support for all OCMF-specified algorithms
  - Koblitz curves: secp192k1, secp256k1
  - NIST curves: secp192r1, secp256r1, secp384r1, secp521r1
  - Brainpool curves: brainpool256r1, brainpoolP256r1, brainpool384r1
  - Hash algorithms: SHA256, SHA512
- **Eichrecht compliance checking**: Validation for German calibration law requirements
  - Reading-level checks: meter status, error flags, time sync, cable loss
  - Transaction-level checks: begin/end consistency, value progression, user identification
- **Public key handling**: Parse and validate DER-encoded public keys with metadata extraction
- **XML file support**: Parse OCMF data from Transparenzsoftware XML format
- **OBIS code registry**: Lookup meter code information and billing relevance
- **Command-line interface**: Validate and verify OCMF data from the terminal
- **Browser demo**: Try PyOCMF in the browser via Pyodide
- **Optional dependencies**: Minimal install for parsing only, extras for CLI and crypto

### Technical Details

- Python 3.11+ required
- Pydantic v2 for data validation
- Optional `cryptography` package for signature verification
- Optional `typer` and `rich` packages for CLI

[0.2.0]: https://github.com/paul-ww/pyocmf/releases/tag/v0.2.0
