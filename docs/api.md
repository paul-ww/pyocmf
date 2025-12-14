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

### OcmfXmlData

Container for OCMF data extracted from XML files.

::: pyocmf.utils.xml.OcmfXmlData

### XML Functions

Helper functions for extracting OCMF data from Transparenzsoftware XML files.

::: pyocmf.utils.xml.parse_ocmf_from_xml

::: pyocmf.utils.xml.parse_ocmf_with_key_from_xml

::: pyocmf.utils.xml.parse_all_ocmf_from_xml

::: pyocmf.utils.xml.extract_ocmf_data_from_file

::: pyocmf.utils.xml.extract_ocmf_strings_from_file

## Public Key

### PublicKey

Public key metadata and validation per OCMF specification.

::: pyocmf.types.public_key.PublicKey

## Exceptions

All exceptions inherit from `PyOCMFError`.

::: pyocmf.exceptions.PyOCMFError

::: pyocmf.exceptions.OcmfFormatError

::: pyocmf.exceptions.OcmfPayloadError

::: pyocmf.exceptions.OcmfSignatureError

::: pyocmf.exceptions.ValidationError

::: pyocmf.exceptions.EncodingError

::: pyocmf.exceptions.HexDecodingError

::: pyocmf.exceptions.Base64DecodingError

::: pyocmf.exceptions.SignatureVerificationError

::: pyocmf.exceptions.PublicKeyError

::: pyocmf.exceptions.DataNotFoundError

::: pyocmf.exceptions.XmlParsingError
