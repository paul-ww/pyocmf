"""Tests for optional cryptography dependency behavior."""

import pytest

from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE


@pytest.mark.skipif(
    CRYPTOGRAPHY_AVAILABLE, reason="Test only runs when cryptography is NOT installed"
)
def test_helpful_error_when_cryptography_not_installed() -> None:
    """Test that a helpful error is raised when cryptography is not installed.

    This test only runs when cryptography is not installed.
    To test manually: pip uninstall cryptography && pytest test/test_ocmf/test_optional_crypto.py
    """
    from pyocmf.ocmf import OCMF

    ocmf_string = (
        'OCMF|{"FV":"1.0","GI":"Test","GS":"123","GV":"1.0","PG":"T1",'
        '"IS":false,"IL":"NONE","RD":[{"TM":"2022-01-01T12:00:00,000+0000 S",'
        '"TX":"B","RV":0.0,"RI":"1-b:1.8.0","RU":"kWh","ST":"G"}]}|'
        '{"SA":"ECDSA-secp256r1-SHA256","SD":"3046022100abcd1234"}'
    )

    ocmf = OCMF.from_string(ocmf_string)

    with pytest.raises(ImportError, match="pip install pyocmf\\[crypto\\]"):
        ocmf.verify_signature("deadbeef")
