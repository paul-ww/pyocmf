from __future__ import annotations


class PyOCMFError(Exception):
    pass


class XmlParsingError(PyOCMFError):
    pass


class DataNotFoundError(PyOCMFError):
    pass


class OcmfFormatError(PyOCMFError):
    pass


class OcmfPayloadError(PyOCMFError):
    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.details = details


class OcmfSignatureError(PyOCMFError):
    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.details = details


class EncodingError(PyOCMFError, ValueError):
    def __init__(self, message: str, *, value: str | None = None) -> None:
        super().__init__(message)
        self.value = value


class HexDecodingError(EncodingError):
    pass


class Base64DecodingError(EncodingError):
    pass


class EncodingTypeError(PyOCMFError, TypeError):
    def __init__(
        self,
        message: str,
        *,
        value: object = None,
        expected_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.value = value
        self.expected_type = expected_type


class ValidationError(PyOCMFError, ValueError):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class CryptoError(PyOCMFError):
    pass


class PublicKeyError(CryptoError):
    def __init__(self, message: str, *, key_data: str | None = None) -> None:
        super().__init__(message)
        self.key_data = key_data


class SignatureVerificationError(CryptoError):
    def __init__(self, message: str, *, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason
