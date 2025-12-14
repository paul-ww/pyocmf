# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- 🔍 **Parse OCMF strings** - Convert OCMF strings into validated Python objects
- ✅ **Verify cryptographic signatures** - Ensure data integrity and authenticity  
- 🔐 **Support multiple algorithms** - ECDSA with various curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- 📝 **Type-safe** - Full Pydantic validation with comprehensive type hints

## Installation

### Basic Installation (parsing only)

```bash
pip install pyocmf
```

This installs the core library for parsing and validating OCMF data.

### With CLI Tools

```bash
pip install pyocmf[cli]
```

This includes the command-line interface with `rich` and `typer` for interactive validation.

### With Signature Verification

```bash
pip install pyocmf[crypto]
```

This includes the `cryptography` package for verifying ECDSA signatures.

### Full Installation (CLI + Crypto)

```bash
pip install pyocmf[cli,crypto]
```

This includes both the CLI tools and cryptography support.

## Quick Start

### Parsing OCMF Data

```python
from pyocmf import OCMF

# Parse an OCMF string
ocmf_string = 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'
ocmf = OCMF.from_string(ocmf_string)

# Access payload data
print(ocmf.payload.GI)  # Gateway ID: "KEBA_KCP30"
print(ocmf.payload.GS)  # Gateway serial number
print(ocmf.payload.RD)  # List of meter readings
```

### Command Line Interface

PyOCMF includes an optional CLI for quick validation and signature verification.

**Note:** The CLI requires the optional `cli` dependency group. Install with `pip install pyocmf[cli]`.

```bash
# Validate an OCMF string
pyocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate with detailed output
pyocmf 'OCMF|{...}|{...}' --verbose

# Validate and verify signature
pyocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Validate hex-encoded OCMF
pyocmf 4f434d467c7b... --hex

# Show help
pyocmf --help
```

**Example output:**
```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

### Verifying Signatures

**Note:** Signature verification requires the `cryptography` package. Install with `pip install pyocmf[crypto]`.

**Important:** Per the OCMF specification, public keys must be transmitted out-of-band (separately from the OCMF data itself), typically via a central register. The public key is never embedded in the OCMF string.

```python
from pyocmf import OCMF

# Parse OCMF data
ocmf = OCMF.from_string(ocmf_string)

# Verify signature with public key (obtained separately, e.g., from XML file or registry)
public_key_hex = "3059301306072A8648CE3D020106082A8648CE3D03010703420004..."

try:
    is_valid = ocmf.verify_signature(public_key_hex)
    if is_valid:
        print("✓ Signature is valid - data is authentic and untampered")
    else:
        print("✗ Signature is invalid - data may have been modified")
except ImportError:
    print("Install cryptography package: pip install pyocmf[crypto]")
```

### Working with Public Key Metadata

The library can extract structured metadata from public keys per OCMF spec Table 23:

```python
from pyocmf.types.public_key import PublicKey

# Parse public key directly
public_key = PublicKey.from_hex(public_key_hex)
print(f"Key Type: {public_key.key_type_identifier}")
print(f"Curve: {public_key.curve}")
print(f"Key Size: {public_key.key_size} bits")
print(f"Block Length: {public_key.block_length} bytes")

# Validate key matches signature algorithm
from pyocmf import OCMF
ocmf = OCMF.from_string(ocmf_string)
matches = public_key.matches_signature_algorithm(ocmf.signature.SA)
print(f"Key matches algorithm: {matches}")
```

### Working with XML Test Files (For Testing)

**Note:** XML parsing utilities use stdlib and are primarily for testing. They are not part of the public API.

```python
# These imports are NOT part of the public API
from pyocmf.utils.xml import parse_ocmf_with_key_from_xml, extract_ocmf_data_from_file

# Parse OCMF and public key from Transparenzsoftware XML file
ocmf, public_key_hex = parse_ocmf_with_key_from_xml("test_file.xml")

# Verify using the public key from XML
is_valid = ocmf.verify_signature(public_key_hex)
print(f"Session: {'Valid' if is_valid else 'Invalid'}")

# Or extract all OCMF data with public key metadata
ocmf_data_list = extract_ocmf_data_from_file("test_file.xml")
for ocmf_data in ocmf_data_list:
    ocmf = OCMF.from_string(ocmf_data.ocmf_string)
    if ocmf_data.public_key:
        is_valid = ocmf.verify_signature(ocmf_data.public_key.key_hex)
        print(f"Session: {'Valid' if is_valid else 'Invalid'}")
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
git clone https://github.com/yourusername/pyocmf.git
cd pyocmf

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Run type checking
uv run mypy src/

# Run linting
uv run ruff check src/
```

## Documentation

For detailed API documentation, visit [the docs](https://pyocmf.readthedocs.io/) or see the `docs/` directory.

## License

See LICENSE file for details.

## About OCMF

OCMF (Open Charge Metering Format) is a standardized format for metering data from electric vehicle charging stations. It ensures transparency and tamper-proof documentation of charging sessions, complying with legal requirements such as the EU Measuring Instruments Directive (MID) and German Eichrecht.

For more information about OCMF, visit [safe-ev.de](https://www.safe-ev.de/).
