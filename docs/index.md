# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- Parse OCMF strings into validated Python objects
- Verify cryptographic signatures for data integrity
- Support for ECDSA with multiple curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- Type-safe validation using Pydantic
- Eichrecht compliance validation for German calibration law requirements
- Command-line interface for validation and verification
- Browser demo with zero installation

## Installation

### Recommended (Full Installation)

```bash
pip install pyocmf[all]
```

This installs the complete package with CLI tools and cryptographic signature verification.

### Minimal Installation

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

### Python API

Parse and validate OCMF data:

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

Verify signatures (requires `pyocmf[crypto]`):

```python
# Verify signature with public key
public_key_hex = "3059301306072A8648CE3D020106082A8648CE3D03010703420004..."

try:
    is_valid = ocmf.verify_signature(public_key_hex)
    if is_valid:
        print("✓ Signature is valid")
    else:
        print("✗ Signature is invalid")
except ImportError:
    print("Install cryptography: pip install pyocmf[crypto]")
```

### Command Line Interface

Validate OCMF strings directly from the terminal (requires `pyocmf[cli]`):

```bash
# Validate an OCMF string
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate and verify signature
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Validate from XML file
ocmf charging_session.xml

# Show detailed output
ocmf 'OCMF|{...}|{...}' --verbose
```

See the [CLI Reference](cli.md) for details.

### Browser Demo

Try PyOCMF in your browser with the [interactive demo](demo.md).

## Regulatory Compliance Checking

PyOCMF includes validation for German Eichrecht (calibration law) requirements:

```python
from pyocmf import OCMF, check_eichrecht_transaction, check_eichrecht_reading

# Check a complete transaction (begin + end)
ocmf_begin = OCMF.from_string(begin_string)
ocmf_end = OCMF.from_string(end_string)

issues = check_eichrecht_transaction(ocmf_begin, ocmf_end)

if not issues:
    print("✓ Transaction is Eichrecht compliant")
else:
    print("✗ Compliance issues found:")
    for issue in issues:
        print(f"  - {issue}")

# Check a single reading
from pyocmf import Reading
reading = ocmf.payload.RD[0]
issues = check_eichrecht_reading(reading, is_begin=True)

if not issues:
    print("✓ Reading is compliant")
```

What is checked:
- Meter status must be 'G' (OK)
- No error flags present
- Time synchronization status
- Cable loss compensation (CL) validation
- Transaction begin/end consistency
- Meter serial number matching
- OBIS code and unit consistency
- Value progression (no regression)
- User identification requirements
- Pagination sequence

See the [API Reference](api.md#compliance-checking) for details.

## Working with XML Files

OCMF data is often distributed in XML format (e.g., from Transparenzsoftware):

```python
from pyocmf import OcmfContainer

# Parse OCMF entries from XML file
container = OcmfContainer.from_xml("charging_session.xml")

# Verify signatures using the public keys from XML
for entry in container:
    if entry.public_key:
        is_valid = entry.verify_signature()
        print(f"Session: {'Valid' if is_valid else 'Invalid'}")
```

## Input Formats

PyOCMF supports multiple input formats:

### Plain OCMF String

```python
ocmf = OCMF.from_string('OCMF|{"FV":"1.0",...}|{"SD":"3045..."}')

# Hex-encoded strings are automatically detected and decoded
ocmf = OCMF.from_string('4f434d467c7b2246563a22312e30222c...')
```

### From XML Files

```python
from pyocmf import OcmfContainer

container = OcmfContainer.from_xml("charging_session.xml")
ocmf = container[0].ocmf  # Access the first OCMF entry
```

## Supported Signature Algorithms

PyOCMF supports all ECDSA signature algorithms defined in the OCMF specification:

- **secp192k1**, **secp256k1** - Koblitz curves
- **secp192r1**, **secp256r1**, **secp384r1**, **secp521r1** - NIST curves  
- **brainpool256r1**, **brainpoolP256r1**, **brainpool384r1** - Brainpool curves
- **SHA256** and **SHA512** hash functions

## Public Key Handling

Per the OCMF specification, public keys must be transmitted out-of-band (separately from the OCMF data itself), typically via a central register. The library can extract and validate public key metadata:

```python
from pyocmf import PublicKey

# Parse public key (accepts hex or base64, auto-detected)
public_key = PublicKey.from_string(public_key_hex)

# Access metadata per OCMF spec Table 23
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

## About OCMF

OCMF (Open Charge Metering Format) is a standardized format for metering data from electric vehicle charging stations. It ensures transparency and tamper-proof documentation of charging sessions, complying with legal requirements such as:

- EU Measuring Instruments Directive (MID)
- German Eichrecht (calibration law)

For more information about OCMF, visit [safe-ev.de](https://www.safe-ev.de/).

## Next Steps

- [API Reference](api.md) - Complete API documentation
- [CLI Reference](cli.md) - Command-line interface guide
- [Browser Demo](demo.md) - Try PyOCMF in your browser
