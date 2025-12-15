# API Reference

## Core Classes

### OCMF

The main class for parsing, validating, and verifying OCMF data.

::: pyocmf.ocmf.OCMF

### Payload

The payload section containing meter readings and metadata.

::: pyocmf.sections.payload.Payload

### Reading

Individual meter reading data.

::: pyocmf.sections.reading.Reading

### Signature

Cryptographic signature data and verification.

::: pyocmf.sections.signature.Signature

## XML Utilities

### OcmfContainer

Container for parsing OCMF data from XML transaction files.

::: pyocmf.utils.xml.OcmfContainer

### OcmfRecord

A single OCMF record with its associated public key.

::: pyocmf.utils.xml.OcmfRecord

## Public Key

### PublicKey

Public key metadata and validation per OCMF specification.

::: pyocmf.types.public_key.PublicKey

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
