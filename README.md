# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- 🔍 **Parse OCMF strings** - Convert OCMF strings into validated Python objects
- ✅ **Verify cryptographic signatures** - Ensure data integrity and authenticity  
- 🔐 **Support multiple algorithms** - ECDSA with various curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- 📝 **Type-safe** - Full Pydantic validation with comprehensive type hints

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

# Access payload data
print(ocmf.payload.GI)  # Gateway ID: "KEBA_KCP30"
print(ocmf.payload.GS)  # Gateway serial number
print(ocmf.payload.RD)  # List of meter readings
```

### Command Line Interface

PyOCMF includes a powerful CLI for quick validation and signature verification.

**Note:** The CLI requires the `cli` extras. Install with `pip install pyocmf[cli]` or `pip install pyocmf[all]`.

```bash
# Validate an OCMF string
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate with detailed output
ocmf 'OCMF|{...}|{...}' --verbose

# Validate and verify signature
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Validate hex-encoded OCMF
ocmf 4f434d467c7b... --hex

# Validate from XML file (auto-extracts public key for verification)
ocmf charging_session.xml --xml

# Validate all OCMF entries in XML file
ocmf charging_session.xml --xml --all

# Show help
ocmf --help
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

**Note:** Signature verification requires the `crypto` extras. Install with `pip install pyocmf[crypto]` or `pip install pyocmf[all]`.

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

### Working with XML Files

OCMF data is often distributed in XML format (e.g., from Transparenzsoftware). PyOCMF provides utilities to extract and verify OCMF data from these files.

```python
from pyocmf import parse_ocmf_with_key_from_xml, extract_ocmf_data_from_file

# Parse OCMF and public key from XML file
ocmf, public_key_hex = parse_ocmf_with_key_from_xml("charging_session.xml")

# Verify using the public key from XML
if public_key_hex:
    is_valid = ocmf.verify_signature(public_key_hex)
    print(f"Session: {'Valid' if is_valid else 'Invalid'}")

# Or extract all OCMF data with public key metadata
ocmf_data_list = extract_ocmf_data_from_file("charging_session.xml")
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

- **[Full Documentation](https://paul-ww.github.io/pyocmf/)** - Complete guide and API reference
- **[Browser Demo](https://paul-ww.github.io/pyocmf/demo/)** - Try PyOCMF in your browser

## License

See LICENSE file for details.

## About OCMF

OCMF (Open Charge Metering Format) is a standardized format for metering data from electric vehicle charging stations. It ensures transparency and tamper-proof documentation of charging sessions, complying with legal requirements such as the EU Measuring Instruments Directive (MID) and German Eichrecht.

For more information about OCMF, visit [safe-ev.de](https://www.safe-ev.de/).
