# Command Line Interface

PyOCMF includes a CLI for signature verification, Eichrecht compliance checking, and
inspecting OCMF records.

!!! note "Installation Required"
    The CLI requires the `cli` extras, and signature verification the `crypto` extras.
    Install both with:
    ```bash
    pip install pyocmf[all]
    ```

## Basic Usage

```bash
# Verify the signature and check Eichrecht compliance (default command)
ocmf 'OCMF|{"FV":"1.0",...}|{"SD":"3045..."}' --public-key 3059301306072A8648CE3D...

# Verify the signature only
ocmf verify 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Check Eichrecht compliance only, for one record or a begin and end record
ocmf check 'OCMF|{...}|{...}'
ocmf check begin.xml end.xml

# Show the parsed record
ocmf inspect 'OCMF|{...}|{...}'
```

## Input Formats

Every command detects the input format, so no flags are needed:

- **OCMF string**: `ocmf 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30",...}|{"SD":"3045..."}'`
- **Hex-encoded OCMF string**: `ocmf 4f434d467c7b2246563a22312e30222c...`
- **Transparenzsoftware XML file**: `ocmf charging_session.xml`. The public keys stored in
  the file are used for verification.

An XML file can hold several records. `ocmf` verifies the signature of every record, and
`ocmf` and `ocmf check` check Eichrecht compliance per transaction (see
[XML Transactions](#xml-transactions)). `ocmf verify` verifies the first record, or all of
them with `--all`, and `ocmf inspect` shows all of them.

## Public Keys

The OCMF spec requires public keys to be transmitted separately from the record. Pass one
with `--public-key` / `-k`, as hex or base64 DER. Without it, the CLI uses the key stored
in the XML file, or a key appended to the OCMF string as a fourth section
(`OCMF|{...}|{...}|key`), as QR codes for the Transparenzsoftware often carry it. Without
any key, the signature is not verified.

## Commands

### Default Command

`ocmf <input>` is short for `ocmf all <input>`. It verifies the signature and then checks
Eichrecht compliance. For an XML file, it verifies every record and checks each transaction:

```bash
ocmf 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...
```

| Option | Description |
|---|---|
| `--public-key`, `-k` | Public key, hex or base64 |
| `--verbose`, `-v` | Also show compliance warnings and the parsed record |
| `--strict` | Reject input that deviates from the OCMF spec |

### `verify` - Signature Verification Only

```bash
ocmf verify 'OCMF|{...}|{...}' --public-key 3059301306072A8648CE3D...

# Verify every record in an XML file
ocmf verify charging_session.xml --all
```

| Option | Description |
|---|---|
| `--public-key`, `-k` | Public key, hex or base64 |
| `--verbose`, `-v` | Also show the parsed record |
| `--all` | Verify all records in an XML file, not only the first |
| `--strict` | Reject input that deviates from the OCMF spec |

### `check` - Eichrecht Compliance Only

```bash
# A single record; transaction checks run if it holds both the begin and the end reading
ocmf check 'OCMF|{...}|{...}'

# A begin and an end record, as OCMF strings or XML files
ocmf check 'OCMF|{...begin...}|{...}' 'OCMF|{...end...}|{...}'

# Every transaction and standalone record of an XML file
ocmf check charging_session.xml

# Show warnings in addition to errors
ocmf check 'OCMF|{...}|{...}' --verbose
```

| Option | Description |
|---|---|
| `--verbose`, `-v` | Show warnings in addition to errors |
| `--strict` | Reject input that deviates from the OCMF spec |

The checks follow the Transparenzsoftware and use the law-relevant readings, preferring
loss-compensated registers. Errors (the record cannot be billed):

- Meter status other than 'G' (OK)
- Energy error flag ('E')
- No readings, or not exactly one begin and one end reading
- Mismatching meter serial numbers, OBIS codes or units
- Decreasing reading values or timestamps
- Relative time ('R') at the begin but not at the end
- Invalid identification level
- Begin and end in different pagination contexts

Warnings:

- Time not synchronized (status other than 'S'), or a time error flag ('t')
- Cable loss compensation (CL) rules, which the Transparenzsoftware ignores
- Mismatching identification data
- An end pagination counter not above the begin counter

#### XML Transactions

Like the Transparenzsoftware, the CLI pairs the records of an XML file by the
`transactionId` and `context` attributes of their `<value>` elements:

```xml
<value transactionId="15060" context="Transaction.Begin">...</value>
<value transactionId="15060" context="Transaction.End">...</value>
```

Records sharing a `transactionId` form a transaction. It needs exactly one record with the
context `Transaction.Begin` and one with `Transaction.End`; otherwise the transaction is not
compliant. Records without a `transactionId`, or alone in their transaction, are checked on
their own. When two files are given, the first record of each is used.

### `inspect` - Show the Parsed Record

```bash
ocmf inspect 'OCMF|{...}|{...}'
```

| Option | Description |
|---|---|
| `--strict` | Reject input that deviates from the OCMF spec |

## Spec Deviations

Input that deviates from the OCMF specification is accepted by default, as by the
Transparenzsoftware, and each deviation is printed as a warning. With `--strict`, it is
rejected instead:

```bash
ocmf inspect transaction.xml --strict
```

## Exit Codes

The CLI exits with `1` if the input cannot be parsed, the signature is invalid or cannot
be checked, or a record or transaction is not Eichrecht compliant. Otherwise it exits with `0`;
compliance warnings do not change the exit code.

## Output Examples

### Signature and Compliance

```
✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex

✓ Eichrecht compliance: COMPLIANT
```

### Compliance Issues

With `--verbose`, warnings are listed as well:

```
✗ Eichrecht compliance: NOT COMPLIANT

Errors:
  [ST] Meter status must be 'G' (OK) for billing-relevant readings, got 'N' (METER_STATUS)
  [EF] Energy error flag ('E') set on billing-relevant reading: 'E' (ERROR_FLAGS)

Warnings:
  [TM] Time should be synchronized (status 'S') for billing, got 'I' (TIME_SYNC)
  [TM] Time should be synchronized (status 'S') for billing, got 'R' (TIME_SYNC)
```

A record with warnings only is reported as `COMPLIANT WITH WARNINGS`.

### XML Transaction

```
Transaction 15060 (2 records)

✗ Eichrecht compliance: NOT COMPLIANT

Errors:
  [RV] End value (7753) must be >= begin value (7763) (VALUE_REGRESSION)
```

### Invalid Signature

```
✗ Signature verification: INVALID
⚠ The signature does not match the payload
```

### All Records of an XML File

```
✓ Found 2 OCMF record(s) in XML file

Entry 1/2:

✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex

Entry 2/2:

✓ Signature verification: VALID
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
```

### Parsed Record

```
OCMF Structure:

Payload:
  Format Version:    1.0
  Gateway ID:        KEBA_KCP30
  Gateway Serial:    17619300
  Pagination:        T32

Readings: 2 reading(s)
╭──────────────────── Reading 1 ─────────────────────╮
│   Time:          2019-08-13T10:03:15,000+0000 I    │
│   Type:          B                                 │
│   Value:         0.2596 kWh                        │
│   Identifier:    1-b:1.8.0                         │
│   Status:        G                                 │
╰────────────────────────────────────────────────────╯
╭──────────────────── Reading 2 ─────────────────────╮
│   Time:          2019-08-13T10:03:36,000+0000 R    │
│   Type:          E                                 │
│   Value:         0.2597 kWh                        │
│   Identifier:    1-b:1.8.0                         │
│   Status:        G                                 │
╰────────────────────────────────────────────────────╯

Signature:
  Algorithm:    ECDSA-secp256r1-SHA256
  Encoding:     hex
  Data:         304502200E2F107C987A300AC1695CA8...
```

### Unreadable Input

```
✗ OCMF parsing failed: Invalid OCMF string: must start with 'OCMF|' or be valid hex-encoded.
```

## Help

```bash
ocmf --help
ocmf check --help
```
