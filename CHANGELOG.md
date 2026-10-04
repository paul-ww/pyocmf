# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-10-04

XML files are checked transaction by transaction, as the Transparenzsoftware does.

### Added

- **XML transaction checks**: `OcmfContainer.check_eichrecht()` pairs the records of an XML file
  by the `transactionId` and `context` attributes of their values. Records sharing a
  `transactionId` need exactly one `Transaction.Begin` and one `Transaction.End` record and are
  checked as a begin/end pair; other records are checked on their own. It returns one
  `EichrechtResult` per transaction or standalone record.
- `OcmfRecord.transaction_id` and `OcmfRecord.context`, and `OcmfContainer.transactions()`
- Docstrings for the public API in the reference documentation
- The browser demo is part of the documentation site and follows its light/dark theme

### Changed

- **CLI**: `ocmf check file.xml` and the default command check every transaction and standalone
  record of an XML file; the default command also verifies the signature of every record
- The browser demo pairs XML records by `transactionId` and `context` instead of by their readings
- `pyocmf.crypto.verification.verify_signature()` takes `public_key` instead of `public_key_hex`,
  as it accepts base64 keys too

### Fixed

- The CLI checked only the first record of an XML file, so a transaction whose end value was
  below its begin value was reported as compliant
- `ocmf --help` showed "requires pyocmf" instead of "requires pyocmf[crypto]" for `verify`
- The CLI reference documented `--all` for the default command, which only `verify` has

## [0.4.0] - 2026-10-04

The Transparenzsoftware is now the reference: pyocmf parses every record it accepts and
judges Eichrecht compliance the same way, reporting spec deviations as warnings.

### Added

- **Spec deviations as warnings**: Records the Transparenzsoftware accepts now parse even when
  they deviate from the OCMF specification (unknown codes, exceeded lengths, missing mandatory
  fields). Each deviation is reported as a `SpecWarning`; unknown code values are kept as strings.
- **Strict mode**: `OCMF.from_string(..., strict=True)`, `OcmfContainer.from_xml(..., strict=True)`
  and the CLI flag `--strict` reject spec deviations, raising the usual `OcmfPayloadError`,
  `OcmfSignatureError` or `OcmfFormatError` (via the new `SpecViolationError`)
- **Embedded public keys**: A key appended as fourth section (`OCMF|payload|signature|key`), as in
  QR codes for the Transparenzsoftware, is available as `OCMF.embedded_public_key`.
  `verify_signature()` and `verify()` use it when called without a key; XML records and the CLI
  fall back to it as well.
- **Single-record transaction checks**: `check_eichrecht_payload()` (used by
  `OCMF.check_eichrecht()`) checks a record holding both begin and end reading like a
  begin/end pair
- **Eichrecht rules from the Transparenzsoftware**: multiple begin or end readings
  (`MULTIPLE_BEGIN`, `MULTIPLE_END`), relative time at begin requiring relative time at end
- **OBIS parsing**: `parse_obis()` and `OBISGroups` parse codes into hex groups;
  `is_law_relevant()` and `is_loss_compensated()` classify registers like the Transparenzsoftware
- **Python 3.14** support
- **Browser demo**: redesigned around a signature / Eichrecht / OCMF Spec verdict, with QR code
  scanning (camera or image), strict mode, transaction checks for XML files and examples from the
  Transparenzsoftware test data. The demo now runs the current code instead of the latest release.
- **Parity tests** against the Transparenzsoftware's own tests and XML test data

### Changed

- **Reading selection**: Begin and end readings are chosen among law-relevant registers,
  preferring loss-compensated ones, instead of the first and last reading. Only these readings are
  checked for meter status, error flags and time synchronization.
- **Time error flag**: `EF="t"` is a warning; only `"E"` is an error
- **Pagination**: Gaps between begin and end are accepted (intermediate records consume numbers);
  an end counter not above the begin counter is a warning
- **Cumulated loss (CL)**: Spec rules are compliance warnings (`CL_BEGIN`, `CL_NEGATIVE`, new
  `CL_REGISTER`) instead of parse errors
- **Identification data**: A mismatch with the format of the identification type is a warning
  for all types
- **EVCCID**: Up to 12 hexadecimal characters (6 bytes per ISO 15118-2)
- **OBIS classification**: Alternative notations such as `1-0:1.8.0`, `01-00:01.08.00.FF` and
  `1-0:98.8.0.FF` are recognised as billing-relevant
- `check_eichrecht_reading()` no longer takes `is_begin`
- `Reading` keeps unknown fields and re-validates on assignment
- The project is marked as alpha; license metadata uses an SPDX expression (PEP 639)
- Dependencies updated

### Removed

- `pyocmf.ValidationError` (no longer raised)
- `pyocmf.models.OCMFTimeFormat` (unused)

### Fixed

- Verifying with a base64-encoded public key raised `ValueError`
- Parsing validated the payload twice and reported every spec deviation twice
- Comparing timestamps with and without UTC offset raised `TypeError`
- `ocmf check` parsed its input twice
- Broken examples in the README

## [0.3.0] - 2026-06-10

### Changed

- **Spec-compliant serialization**: Numeric fields are kept as exact decimals and written as JSON
  numbers with their original decimal places, `RI` is written as a string, and timestamps use a
  colon-free UTC offset
- `RT` (reading current type) is parsed, and extension fields in the signature section survive
  parsing and serialization
- Omitted reading fields are inherited from the previous reading
- Stronger round-trip tests over the Transparenzsoftware test data
- Dependencies updated

## [0.2.3] - 2026-02-11

### Fixed

- Broken browser demo

### Changed

- Improved README and documentation
- Dependencies updated

## [0.2.2] - 2026-01-30

### Fixed

- Demo link

### Changed

- Removed the `ciso8601` dependency; type checking uses ty instead of mypy
- Dependencies updated

## [0.2.0] - 2026-01-30

Initial public release.

### Added

- **Core OCMF parsing**: Parse OCMF strings into validated Python objects with Pydantic
- **Automatic format detection**: Hex-encoded OCMF strings are automatically detected and decoded
- **Signature verification**: ECDSA signature verification with support for all OCMF-specified algorithms
  - Koblitz curves: secp192k1, secp256k1
  - NIST curves: secp192r1, secp256r1, secp384r1, secp521r1
  - Brainpool curves: brainpool256r1, brainpoolP256r1, brainpool384r1
  - Hash algorithms: SHA256, SHA512
- **Eichrecht compliance checking**: Validation for German calibration law requirements
  - Reading-level checks: meter status, error flags, time sync, cable loss
  - Transaction-level checks: begin/end consistency, value progression, user identification
- **Public key handling**: Parse and validate DER-encoded public keys with metadata extraction
- **XML file support**: Parse OCMF data from Transparenzsoftware XML format
- **OBIS code registry**: Lookup meter code information and billing relevance
- **Command-line interface**: Validate and verify OCMF data from the terminal
- **Browser demo**: Try PyOCMF in the browser via Pyodide
- **Optional dependencies**: Minimal install for parsing only, extras for CLI and crypto

### Technical Details

- Python 3.11+ required
- Pydantic v2 for data validation
- Optional `cryptography` package for signature verification
- Optional `typer` and `rich` packages for CLI

[0.5.0]: https://github.com/paul-ww/pyocmf/releases/tag/v0.5.0
[0.4.0]: https://github.com/paul-ww/pyocmf/releases/tag/v0.4.0
[0.3.0]: https://github.com/paul-ww/pyocmf/releases/tag/v0.3.0
[0.2.3]: https://github.com/paul-ww/pyocmf/releases/tag/v0.2.3
[0.2.2]: https://github.com/paul-ww/pyocmf/releases/tag/v0.2.2
[0.2.0]: https://github.com/paul-ww/pyocmf/releases/tag/v0.2.0
