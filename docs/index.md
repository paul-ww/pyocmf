# PyOCMF

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

## Features

- 🔍 **Parse OCMF strings** - Convert OCMF strings into validated Python objects
- ✅ **Verify cryptographic signatures** - Ensure data integrity and authenticity  
- 🔐 **Support multiple algorithms** - ECDSA with various curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- 📝 **Type-safe** - Full Pydantic validation with comprehensive type hints
- 🖥️ **CLI tools** - Command-line interface for quick validation and verification
- 🌐 **Browser demo** - Try it in your browser with zero installation

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

# Access payload data
print(ocmf.payload.GI)  # Gateway ID: "KEBA_KCP30"
print(ocmf.payload.GS)  # Gateway serial number
print(ocmf.payload.RD)  # List of meter readings
```

Verify signatures (requires `pyocmf[crypto]`):

```python
# Verify signature with public key
public_key_hex = "3059301306072A8648CE3D020106082A8648CE3D03010703420004..."

try:
    is_valid = ocmf.verify_signature(public_key_hex)
    if is_valid:
        print("✓ Signature is valid - data is authentic")
    else:
        print("✗ Signature is invalid - data may be tampered")
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

See the [CLI Reference](cli.md) for complete documentation.

### Browser Demo

Try PyOCMF directly in your browser with our [interactive demo](demo.md) - no installation required!

## Working with XML Files

OCMF data is often distributed in XML format (e.g., from Transparenzsoftware):

```python
from pyocmf import parse_ocmf_with_key_from_xml

# Parse OCMF and public key from XML file
ocmf, public_key_hex = parse_ocmf_with_key_from_xml("charging_session.xml")

# Verify using the public key from XML
if public_key_hex:
    is_valid = ocmf.verify_signature(public_key_hex)
    print(f"Session: {'Valid' if is_valid else 'Invalid'}")
```

Extract all OCMF entries from XML:

```python
from pyocmf import extract_ocmf_data_from_file, OCMF

# Extract all OCMF data with public key metadata
ocmf_data_list = extract_ocmf_data_from_file("charging_session.xml")

for ocmf_data in ocmf_data_list:
    ocmf = OCMF.from_string(ocmf_data.ocmf_string)
    if ocmf_data.public_key:
        is_valid = ocmf.verify_signature(ocmf_data.public_key.key_hex)
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
from pyocmf import parse_ocmf_from_xml

ocmf = parse_ocmf_from_xml("charging_session.xml")
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
from pyocmf.types.public_key import PublicKey

# Parse public key
public_key = PublicKey.from_hex(public_key_hex)

# Access metadata per OCMF spec Table 23
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
