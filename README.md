# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

> **Note**: This is an unofficial library that implements parts of the [OCMF specification](https://github.com/SAFE-eV/OCMF-Open-Charge-Metering-Format). It is not affiliated with or endorsed by [S.A.F.E. e.V.](https://www.safe-ev.de/). For official verification of charging session data, please use the [Transparenzsoftware](https://www.safe-ev.de/de/transparenzsoftware.php) provided by S.A.F.E. e.V. This library may be incomplete or contain discrepancies from the official specification.

## Features

- Parse OCMF strings into validated Python objects
- Verify cryptographic signatures for data integrity
- Support for ECDSA with multiple curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- Type-safe validation using Pydantic
- Eichrecht compliance validation for German calibration law requirements

## Installation

### Recommended (Full Installation)

```bash
pip install pyocmf[all]
```

This installs the complete package with CLI tools and cryptographic signature verification.

### Minimal Installation (parsing only)

```bash
pip install pyocmf
```

This installs only the core library for parsing and validating OCMF data (no CLI or crypto).

### Partial Installations

```bash
# With CLI only
pip install pyocmf[cli]

# With crypto only
pip install pyocmf[crypto]

# With both CLI and crypto
pip install pyocmf[cli,crypto]
```

## Quick Start

### Parsing OCMF Data

```python
from pyocmf import OCMF

# Parse an OCMF string
ocmf_string = 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'
ocmf = OCMF.from_string(ocmf_string)

# Hex-encoded strings are automatically detected and decoded
ocmf = OCMF.from_string('4f434d467c7b2246...')

# Access payload data
print(ocmf.payload.GI)  # Gateway ID: "KEBA_KCP30"
print(ocmf.payload.GS)  # Gateway serial number
print(ocmf.payload.RD)  # List of meter readings

# Serialize back to string
print(ocmf.to_string())           # Plain OCMF string
print(ocmf.to_string(hex=True))   # Hex-encoded
```

### Command Line Interface

PyOCMF includes a CLI for validation and signature verification.

Note: The CLI requires the `cli` extras. Install with `pip install pyocmf[cli]` or `pip install pyocmf[all]`.

```bash
# Validate an OCMF string
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate with detailed output
ocmf 'OCMF|{...}|{...}' --verbose

# Validate and verify signature
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Validate hex-encoded OCMF (auto-detected)
ocmf 4f434d467c7b...

# Validate from XML file (auto-detected, extracts public key for verification)
ocmf charging_session.xml

# Validate all OCMF entries in XML file
ocmf charging_session.xml --all

# Show help
ocmf --help
```

Example output:
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

### Verifying Signatures

Note: Signature verification requires the `crypto` extras. Install with `pip install pyocmf[crypto]` or `pip install pyocmf[all]`.

Important: Per the OCMF specification, public keys must be transmitted out-of-band (separately from the OCMF data itself), typically via a central register. The public key is never embedded in the OCMF string.

```python
from pyocmf import OCMF

# Parse OCMF data
ocmf = OCMF.from_string(ocmf_string)

# Verify signature with public key (obtained separately, e.g., from XML file or registry)
public_key_hex = "3059301306072A8648CE3D020106082A8648CE3D03010703420004..."

try:
    is_valid = ocmf.verify_signature(public_key_hex)
    if is_valid:
        print("✓ Signature is valid")
    else:
        print("✗ Signature is invalid")
except ImportError:
    print("Install cryptography package: pip install pyocmf[crypto]")
```

### Working with Public Key Metadata

The library can extract structured metadata from public keys per OCMF spec Table 23:

```python
from pyocmf import PublicKey

# Parse public key (accepts hex or base64 encoding, auto-detected)
public_key = PublicKey.from_string(public_key_hex)
print(f"Key Type: {public_key.key_type_identifier}")
print(f"Curve: {public_key.curve}")
print(f"Key Size: {public_key.key_size} bits")
print(f"Block Length: {public_key.block_length} bytes")

# Export key in different formats
print(public_key.to_string())             # hex (default)
print(public_key.to_string(base64=True))  # base64

# Validate key matches signature algorithm
from pyocmf import OCMF
ocmf = OCMF.from_string(ocmf_string)
matches = public_key.matches_signature_algorithm(ocmf.signature.SA)
print(f"Key matches algorithm: {matches}")
```

### Regulatory Compliance Checking

PyOCMF includes validation for German Eichrecht (calibration law) requirements:

```python
from pyocmf import OCMF, check_eichrecht_transaction

# Check a complete transaction (begin + end)
ocmf_begin = OCMF.from_string(begin_string)
ocmf_end = OCMF.from_string(end_string)

issues = check_eichrecht_transaction(ocmf_begin, ocmf_end)

if not issues:
    print("✓ Transaction is Eichrecht compliant")
else:
    for issue in issues:
        print(f"✗ {issue}")
```

Checks include meter status, error flags, time sync, cable loss compensation, transaction consistency, value progression, and user identification.

### Working with XML Files

OCMF data is often distributed in XML format (e.g. when downloading transaction data from a CPO backend). PyOCMF provides utilities to extract and verify OCMF data from these files.

```python
from pyocmf import OcmfContainer

# Parse all OCMF entries from XML file
container = OcmfContainer.from_xml("charging_session.xml")

# Iterate over entries and verify signatures
for entry in container:
    print(f"Gateway: {entry.ocmf.payload.GI}")
    
    # Public key is automatically extracted from XML if present
    if entry.public_key:
        is_valid = entry.verify_signature()
        print(f"Signature: {'Valid' if is_valid else 'Invalid'}")
```

## Supported Signature Algorithms

PyOCMF supports all ECDSA signature algorithms defined in the OCMF specification:

- **secp192k1**, **secp256k1** - Koblitz curves
- **secp192r1**, **secp256r1**, **secp384r1**, **secp521r1** - NIST curves  
- **brainpool256r1**, **brainpoolP256r1**, **brainpool384r1** - Brainpool curves
- **SHA256** and **SHA512** hash functions

## Error Handling

```python
from pyocmf import OCMF, SignatureVerificationError, OcmfFormatError

try:
    ocmf = OCMF.from_string(ocmf_string)
    is_valid = ocmf.verify_signature(public_key)
except OcmfFormatError as e:
    print(f"Invalid OCMF format: {e}")
except SignatureVerificationError as e:
    print(f"Signature verification error: {e}")
```

## Development

```bash
# Clone the repository
git clone https://github.com/paul-ww/pyocmf.git
cd pyocmf

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Run type checking
uv run ty check src test

# Run linting
uv run ruff check .
```

## Documentation

- [Full Documentation](https://paul-ww.github.io/pyocmf/) - Guide and API reference
- [Browser Demo](https://paul-ww.github.io/pyocmf/demo/) - Try PyOCMF in your browser

## License

See LICENSE file for details.

## About OCMF

OCMF (Open Charge Metering Format) is a standardized format for metering data from electric vehicle charging stations. It ensures transparency and tamper-proof documentation of charging sessions, complying with legal requirements such as the EU Measuring Instruments Directive (MID) and German Eichrecht.

For more information about OCMF, visit [safe-ev.de](https://www.safe-ev.de/).

---

<p align="center"><i>Vibe-engineered with <a href="https://claude.ai/code">Claude Code</a></i> 🤖</p>
