# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- **Parse OCMF strings** - Convert OCMF strings into validated Python objects
- **Verify cryptographic signatures** - Ensure data integrity and authenticity
- **Support multiple algorithms** - ECDSA with various curves (secp192r1, secp256r1, secp384r1, etc.)
- **Type-safe** - Full Pydantic validation with type hints

## Installation

### Basic Installation (parsing only)

```bash
pip install pyocmf
```

### With Signature Verification

```bash
pip install pyocmf[crypto]
```

The `crypto` extra includes the `cryptography` package for verifying ECDSA signatures.

## Quick Examples

### Parsing OCMF Data

```python
from pyocmf import OCMF

# Parse an OCMF string
ocmf_string = "OCMF|{...}|{...}"
ocmf = OCMF.from_string(ocmf_string)

# Access payload data
print(ocmf.payload.GI)  # Gateway ID
print(ocmf.payload.RD)  # Readings
```

### Verifying Signatures

```python
from pyocmf import OCMF

# Parse OCMF data
ocmf = OCMF.from_string(ocmf_string)

# Verify signature with external public key
public_key_hex = "3059301306072A8648CE3D..."
is_valid = ocmf.verify_signature(public_key_hex)

if is_valid:
    print("Signature is valid - data is authentic")
else:
    print("Signature is invalid - data may be tampered")
```

### Using Embedded Public Keys

```python
from pyocmf import OCMF

# OCMF data with embedded public key in signature section
ocmf = OCMF.from_string(ocmf_with_pk)

# Verify using embedded public key
is_valid = ocmf.verify_signature()  # Uses signature.PK
```

### Working with XML Files

```python
from pyocmf.utils.xml import parse_ocmf_from_xml

# Parse OCMF from Transparenzsoftware XML file
ocmf = parse_ocmf_from_xml("charging_session.xml")
is_valid = ocmf.verify_signature(public_key_hex)
```

## Documentation

See the [API Reference](api.md) for detailed documentation.
