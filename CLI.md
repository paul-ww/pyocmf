# CLI Feature Documentation

## Overview

A command-line interface (CLI) has been added to pyocmf using Typer and Rich for validating OCMF strings and verifying cryptographic signatures.

## Installation

The CLI is included with the standard installation:

```bash
pip install pyocmf
```

For signature verification, install with the crypto extra:

```bash
pip install pyocmf[crypto]
```

## Usage

### Basic Command Structure

```bash
pyocmf <ocmf_string> [OPTIONS]
```

### Options

- `--public-key, -k <hex_key>`: Hex-encoded public key for signature verification
- `--hex`: Treat input as hex-encoded OCMF string
- `--verbose, -v`: Show detailed OCMF structure
- `--help`: Show help message

## Examples

### 1. Basic Validation

Validate an OCMF string:

```bash
pyocmf 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'
```

**Output:**
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed

ℹ Signature present but not verified (use --public-key to verify)
```

### 2. Verbose Output

Display detailed OCMF structure:

```bash
pyocmf 'OCMF|{...}|{...}' --verbose
```

**Output:**
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed

OCMF Structure:

Payload:
  Format Version:    1.0
  Gateway ID:        KEBA_KCP30
  Gateway Serial:    17619300
  Pagination:        T32

Readings: 2 reading(s)
╭───────────────── Reading 1 ─────────────────╮
│   Time:          2019-08-13T10:03:15,000…   │
│                  I                          │
│   Type:          B                          │
│   Value:         0.2596 kWh                 │
│   Identifier:    1-b:1.8.0                  │
│   Status:        G                          │
╰─────────────────────────────────────────────╯

Signature:
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
  Data:         304502200E2F107C987A300AC169…
```

### 3. Signature Verification

Validate and verify the cryptographic signature:

```bash
pyocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D020106082A8648CE3D...
```

**Output (valid signature):**
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

**Output (invalid signature):**
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✗ Signature verification: INVALID
⚠ The signature does not match the payload
```

### 4. Hex-Encoded OCMF

Validate hex-encoded OCMF strings:

```bash
pyocmf 4f434d467c7b224656223a22312e30222c... --hex
```

**Output:**
```
✓ Successfully parsed hex-encoded OCMF string
✓ OCMF validation passed
```

### 5. Error Handling

Invalid OCMF format:

```bash
pyocmf 'INVALID|data|here'
```

**Output:**
```
✗ OCMF validation failed: String does not match expected OCMF format 'OCMF|{payload}|{signature}'.
```

## Exit Codes

- `0`: Success - OCMF is valid and signature verification passed (if requested)
- `1`: Failure - Invalid OCMF format, validation error, or signature verification failed

## Features

### Validation

- Parses OCMF strings in standard or hex-encoded format
- Validates payload and signature JSON structure
- Validates against OCMF specification using Pydantic models
- Clear error messages for invalid data

### Signature Verification

- Verifies ECDSA signatures with provided public key
- Supports all OCMF signature algorithms:
  - secp192r1, secp256r1, secp384r1, secp521r1 (NIST curves)
  - secp192k1, secp256k1 (Koblitz curves)
  - brainpool256r1, brainpool384r1 (Brainpool curves)
- Validates key curve matches signature algorithm
- Detects tampered data

### Output

- Rich terminal output with colors and formatting
- Checkmarks (✓) for success, crosses (✗) for errors
- Info symbols (ℹ) for warnings and suggestions
- Formatted tables for detailed output
- Professional presentation using Rich library

## Implementation Details

### Files Added

- `src/pyocmf/cli.py`: CLI implementation using Typer
- `test/test_ocmf/test_cli.py`: Comprehensive CLI tests
- `examples/cli_usage.sh`: Example usage script

### Dependencies

- `typer>=0.20.0`: CLI framework
- `rich>=14.2.0`: Terminal formatting and output

### Entry Point

The CLI is registered as a console script in `pyproject.toml`:

```toml
[project.scripts]
pyocmf = "pyocmf.cli:main"
```

## Testing

The CLI includes comprehensive tests covering:

- Valid and invalid OCMF validation
- Verbose output display
- Hex-encoded OCMF parsing
- Signature verification (valid and invalid)
- Error handling and edge cases
- Real OCMF data from test files

Run tests:

```bash
uv run pytest test/test_ocmf/test_cli.py -v
```

## Development

### Code Quality

The CLI follows the project's code quality standards:

- Passes ruff linting and formatting checks
- Passes mypy type checking
- Comprehensive test coverage
- Follows project commenting guidelines

### Testing Locally

After making changes, test the CLI:

```bash
# Install in development mode
uv sync

# Test the CLI
uv run pyocmf 'OCMF|{...}|{...}'

# Run tests
uv run pytest test/test_ocmf/test_cli.py
```

## Future Enhancements

Potential improvements for the CLI:

1. **File input**: Accept OCMF data from files
2. **Batch processing**: Validate multiple OCMF strings at once
3. **JSON output**: Machine-readable output format
4. **Public key from file**: Load public keys from files
5. **XML parsing**: Direct support for Transparenzsoftware XML files
6. **Export functionality**: Convert between formats (string ↔ hex)
7. **Colorless output**: Option for plain text output in CI/CD
8. **Quiet mode**: Minimal output for scripting

## Support

For issues or questions about the CLI:

1. Check the help: `pyocmf --help`
2. Review examples: `examples/cli_usage.sh`
3. Run tests: `uv run pytest test/test_ocmf/test_cli.py`
4. Open an issue on GitHub