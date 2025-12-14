# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- 🔍 **Parse OCMF strings** - Convert OCMF strings into validated Python objects
- ✅ **Verify cryptographic signatures** - Ensure data integrity and authenticity  
- 🔐 **Support multiple algorithms** - ECDSA with various curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- 📝 **Type-safe** - Full Pydantic validation with comprehensive type hints
- 📦 **Parse XML containers** - Extract OCMF from Transparenzsoftware XML files

## Installation

```bash
pip install pyocmf
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

### Verifying Signatures

```python
from pyocmf import OCMF

# Parse OCMF data
ocmf = OCMF.from_string(ocmf_string)

# Verify signature with public key
public_key_hex = "3059301306072A8648CE3D020106082A8648CE3D03010703420004..."
is_valid = ocmf.verify_signature(public_key_hex)

if is_valid:
    print("✓ Signature is valid - data is authentic and untampered")
else:
    print("✗ Signature is invalid - data may have been modified")
```

### Using Embedded Public Keys

Some OCMF data includes the public key in the signature section:

```python
from pyocmf import OCMF

# OCMF with embedded public key
ocmf = OCMF.from_string(ocmf_with_embedded_key)

# Verify using the embedded public key
is_valid = ocmf.verify_signature()  # Automatically uses signature.PK
```

### Working with Transparenzsoftware XML Files

```python
from pyocmf.utils.xml import parse_ocmf_from_xml, extract_ocmf_strings_from_file

# Parse OCMF from XML file
ocmf = parse_ocmf_from_xml("charging_session.xml")

# Or extract all OCMF strings from XML
ocmf_strings = extract_ocmf_strings_from_file("charging_session.xml")
for ocmf_str in ocmf_strings:
    ocmf = OCMF.from_string(ocmf_str)
    print(f"Session {ocmf.payload.PG}: {ocmf.verify_signature(public_key)}")
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
