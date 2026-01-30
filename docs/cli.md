# Command Line Interface

PyOCMF includes a CLI for validation, signature verification, and regulatory compliance checking.

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

# Check Eichrecht compliance
ocmf check 'OCMF|{...}|{...}'

# Check transaction pair compliance (begin + end)
ocmf check begin.txt end.txt
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

## Commands

### Default Command (Validation + Compliance)

The default command performs both signature verification and Eichrecht compliance checking:

```bash
# Parse, verify signature, and check compliance
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Check compliance without signature verification
ocmf 'OCMF|{...}|{...}'
```

### `verify` - Signature Verification Only

Verify cryptographic signatures without compliance checking:

```bash
# Verify signature for a single OCMF string
ocmf verify 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Verify all entries in XML file
ocmf verify charging_session.xml --all
```

### `check` - Eichrecht Compliance Only

Check regulatory compliance against German Eichrecht (calibration law) requirements:

```bash
# Check single reading
ocmf check 'OCMF|{...}|{...}'

# Check transaction pair (begin + end)
ocmf check begin_reading.txt end_reading.txt

# Show warnings in addition to errors
ocmf check 'OCMF|{...}|{...}' --verbose
```

What is checked:
- Meter status must be 'G' (OK)
- No error flags present
- Time synchronization status
- Cable loss compensation (CL) validation
- Transaction begin/end consistency (when checking pairs)
- Meter serial number matching
- OBIS code and unit consistency
- Value progression (no regression)
- User identification requirements
- Pagination sequence

## Output Examples

### Successful Validation

```
✓ Successfully parsed OCMF string
✓ OCMF validation passed
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

### Compliance Check Results

```
✓ Eichrecht compliance check passed
  No issues found
```

Or when issues are detected:

```
✗ Eichrecht compliance check failed

Errors (2):
  [ST] Meter status must be 'G' (OK) for billing-relevant readings, got 'N' (METER_STATUS)
  [EF] Error flags must be empty for billing-relevant readings, got 'E01' (ERROR_FLAGS)

Warnings (1):
  [TM] Time should be synchronized (status 'S') for billing, got 'U' (TIME_SYNC)
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
