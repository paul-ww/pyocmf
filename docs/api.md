# API Reference

## Core Classes

### OCMF

The main class for parsing, validating, and verifying OCMF data.

::: pyocmf.core.ocmf.OCMF

### Payload

The payload section containing meter readings and metadata.

::: pyocmf.core.payload.Payload

### Reading

Individual meter reading data.

::: pyocmf.core.reading.Reading

### Signature

Cryptographic signature data and verification.

::: pyocmf.core.signature.Signature

## Compliance Checking

### Eichrecht Compliance

Functions for validating OCMF data against German Eichrecht (calibration law) requirements.

::: pyocmf.compliance.check_eichrecht_reading

::: pyocmf.compliance.check_eichrecht_transaction

::: pyocmf.compliance.validate_transaction_pair

### Compliance Models

::: pyocmf.compliance.models.EichrechtIssue

::: pyocmf.compliance.models.IssueCode

::: pyocmf.compliance.models.IssueSeverity

## Data Models

### PublicKey

Public key metadata and validation per OCMF specification.

::: pyocmf.models.public_key.PublicKey

### OBIS

OBIS code model for meter reading identifiers.

::: pyocmf.models.obis.OBIS

### OCMFTimestamp

Timestamp with time synchronization status.

::: pyocmf.models.timestamp.OCMFTimestamp

### CableLossCompensation

Cable loss compensation data.

::: pyocmf.models.cable_loss.CableLossCompensation

## Registries

### OBIS Code Registry

Utilities for working with OBIS codes.

::: pyocmf.registries.obis.get_obis_info

::: pyocmf.registries.obis.is_billing_relevant

::: pyocmf.registries.obis.is_accumulation_register

::: pyocmf.registries.obis.is_transaction_register

::: pyocmf.registries.obis.OBISInfo

## XML Utilities

### OcmfContainer

Container for parsing OCMF data from XML transaction files.

::: pyocmf.utils.xml.OcmfContainer

### OcmfRecord

A single OCMF record with its associated public key.

::: pyocmf.utils.xml.OcmfRecord

## Exceptions

All exceptions inherit from `PyOCMFError`.

::: pyocmf.exceptions.PyOCMFError

### OCMF Parsing Errors

::: pyocmf.exceptions.OcmfFormatError

::: pyocmf.exceptions.OcmfPayloadError

::: pyocmf.exceptions.OcmfSignatureError

### Validation Errors

::: pyocmf.exceptions.ValidationError

### Encoding Errors

::: pyocmf.exceptions.EncodingError

::: pyocmf.exceptions.EncodingTypeError

::: pyocmf.exceptions.HexDecodingError

::: pyocmf.exceptions.Base64DecodingError

### Cryptography Errors

::: pyocmf.exceptions.CryptoError

::: pyocmf.exceptions.SignatureVerificationError

::: pyocmf.exceptions.PublicKeyError

### Data Errors

::: pyocmf.exceptions.DataNotFoundError

::: pyocmf.exceptions.XmlParsingError
