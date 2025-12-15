# Command Line Interface

PyOCMF includes a powerful CLI for quick validation and signature verification.

!!! note "Installation Required"
    The CLI requires the `cli` extras. Install with:
    ```bash
    pip install pyocmf[cli]
    # or
    pip install pyocmf[all]
    ```

## Basic Usage

```bash
# Validate an OCMF string
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}'

# Validate with verbose output
ocmf 'OCMF|{...}|{...}' --verbose

# Validate and verify signature
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...
```

## Input Formats

The CLI automatically detects the input format - no flags needed:

### OCMF String

```bash
ocmf 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'
```

### Hex-Encoded OCMF

Hex-encoded strings are automatically detected and decoded:

```bash
ocmf 4f434d467c7b2246563a22312e30222c...
```

### XML File

XML files are automatically detected. The CLI extracts OCMF data and public keys for verification:

```bash
# Validate first entry
ocmf charging_session.xml

# Validate all entries
ocmf charging_session.xml --all
```

## Options

### `--public-key` / `-k`

Provide a hex-encoded public key for signature verification:

```bash
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D020106082A8648CE3D03010703420004...
```

!!! note "Cryptography Required"
    Signature verification requires the `crypto` extras:
    ```bash
    pip install pyocmf[crypto]
    # or
    pip install pyocmf[all]
    ```

### `--verbose` / `-v`

Show detailed OCMF structure including payload fields, readings, and signature information:

```bash
ocmf 'OCMF|{...}|{...}' --verbose
```

### `--all`

Process all OCMF entries in an XML file (default: first only):

```bash
ocmf charging_session.xml --all
```

## Output Examples

### Successful Validation

```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

### Validation with Details

Using `--verbose` shows the complete OCMF structure:

```
✓ Successfully parsed OCMF string
✓ OCMF validation passed

OCMF Structure:

Payload:
  Format Version:  1.0
  Gateway ID:      KEBA_KCP30
  Gateway Serial:  12345678
  Pagination:      T1234

Readings: 2 reading(s)

╭─ Reading 1 ─────────────────────────╮
│ Time:        2024-01-15T10:30:00Z   │
│ Type:        Transaction.Begin      │
│ Value:       0.0 kWh                │
│ Identifier:  RFID_12345             │
│ Status:      G                      │
╰─────────────────────────────────────╯

Signature:
  Algorithm:  ECDSA-secp256r1-SHA256
  Encoding:   hex
  Data:       3045022100...
```

### XML File Processing

```
✓ Found 2 OCMF entry(ies) in XML file

Entry 1/2:
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex

Entry 2/2:
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

## Error Handling

The CLI provides clear error messages for validation failures:

```
✗ OCMF validation failed: Invalid signature encoding: invalid_encoding
```

```
✗ Signature verification: INVALID
⚠ The signature does not match the payload
```

## Help

View all available options:

```bash
ocmf --help
```
