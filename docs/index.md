# PyOCMF

[![PyPI version](https://img.shields.io/pypi/v/pyocmf)](https://pypi.org/project/pyocmf/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyocmf)](https://pypi.org/project/pyocmf/)
[![CI](https://github.com/paul-ww/pyocmf/actions/workflows/test.yml/badge.svg)](https://github.com/paul-ww/pyocmf/actions/workflows/test.yml)

Python library for parsing, validating, and verifying OCMF (Open Charge Metering Format) signatures from electric vehicle charging stations.

!!! tip "Try it in your browser"
    **[Launch the Browser Demo](demo/index.html)** - No installation required! Parse and validate OCMF data directly in your browser using Pyodide.

## Features

- Parse OCMF strings into validated Python objects
- Verify cryptographic signatures for data integrity
- Support for ECDSA with multiple curves (secp192r1, secp256r1, secp384r1, secp521r1, brainpool variants)
- Type-safe validation using Pydantic
- Eichrecht compliance validation for German calibration law requirements
- Command-line interface for validation and verification

## Installation

```bash
pip install pyocmf[all]
```

This installs the complete package with CLI tools and cryptographic signature verification.

??? info "Alternative installation options"
    ```bash
    # Minimal (parsing only, no CLI or crypto)
    pip install pyocmf

    # With CLI only
    pip install pyocmf[cli]

    # With crypto only
    pip install pyocmf[crypto]
    ```

## Quick Start

```python
from pyocmf import OCMF

# Parse an OCMF string
ocmf_string = 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'
ocmf = OCMF.from_string(ocmf_string)

# Access payload data
print(ocmf.payload.GI)  # Gateway ID: "KEBA_KCP30"
print(ocmf.payload.GS)  # Gateway serial number
print(ocmf.payload.RD)  # List of meter readings

# Verify signature (requires pyocmf[crypto])
is_valid = ocmf.verify_signature(public_key_hex)
```

## Command Line Interface

```bash
# Validate an OCMF string
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate and verify signature
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Validate from XML file (extracts public key automatically)
ocmf charging_session.xml
```

See the [CLI Reference](cli.md) for details.

## More Examples

??? example "Working with XML files"
    OCMF data is often distributed in XML format from CPO backends.

    ```python
    from pyocmf import OcmfContainer

    container = OcmfContainer.from_xml("charging_session.xml")

    for entry in container:
        print(f"Gateway: {entry.ocmf.payload.GI}")
        if entry.public_key:
            is_valid = entry.verify_signature()
            print(f"Signature: {'Valid' if is_valid else 'Invalid'}")
    ```

??? example "Eichrecht compliance checking"
    Validate German calibration law requirements for charging transactions.

    ```python
    from pyocmf import OCMF, check_eichrecht_transaction

    ocmf_begin = OCMF.from_string(begin_string)
    ocmf_end = OCMF.from_string(end_string)

    issues = check_eichrecht_transaction(ocmf_begin, ocmf_end)
    if not issues:
        print("Transaction is Eichrecht compliant")
    ```

    Checks include meter status, error flags, time sync, cable loss compensation, transaction consistency, and user identification.

??? example "Public key metadata"
    Extract structured metadata from public keys per OCMF spec Table 23.

    ```python
    from pyocmf import PublicKey

    public_key = PublicKey.from_string(public_key_hex)
    print(f"Curve: {public_key.curve}")
    print(f"Key Size: {public_key.key_size} bits")

    # Check if key matches signature algorithm
    matches = public_key.matches_signature_algorithm(ocmf.signature.SA)
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

## About OCMF

OCMF (Open Charge Metering Format) is a standardized format for metering data from electric vehicle charging stations. It ensures transparency and tamper-proof documentation of charging sessions, complying with legal requirements such as:

- EU Measuring Instruments Directive (MID)
- German Eichrecht (calibration law)

For more information about OCMF, visit [safe-ev.de](https://www.safe-ev.de/).
