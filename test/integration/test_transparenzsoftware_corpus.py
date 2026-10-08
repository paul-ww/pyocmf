"""Signature verification parity with the Transparenzsoftware XML test corpus.

Expected outcomes mirror what the Transparenzsoftware reports for the same files
(OCMFVerifierTest, AppOCMFTest, AppOCMFebeeTest, AppVW_OCMFTest).
"""

from __future__ import annotations

import pathlib
import warnings
from dataclasses import dataclass

import pytest

from pyocmf.exceptions import PyOCMFError, SignatureVerificationError
from pyocmf.utils.xml import OcmfContainer

try:
    from pyocmf.crypto.availability import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed"
)


@dataclass(frozen=True)
class SignatureOutcome:
    valid: int
    invalid: int = 0
    rejected: int = 0


EXPECTED_SIGNATURES: dict[str, SignatureOutcome] = {
    "20211007-device-with-evt-ocmf-sss-ses.xml": SignatureOutcome(valid=2),
    "OCMF_Test_Data_00.xml": SignatureOutcome(valid=2),
    "Ocmf_Example_OBIS_98.8.0_2.8.0.xml": SignatureOutcome(valid=1),
    "VW_OCMF_load.xml": SignatureOutcome(valid=1),
    "brainpoolP256r1.xml": SignatureOutcome(valid=2),
    "chargepoint_3.xml": SignatureOutcome(valid=1),
    "keba_test.xml": SignatureOutcome(valid=100),
    "keba_test_txn.xml": SignatureOutcome(valid=100),
    "measurements.xml": SignatureOutcome(valid=21),
    "nistP384_0Wh.xml": SignatureOutcome(valid=2),
    "ocmf_sec.xml": SignatureOutcome(valid=2),
    "ocmf_tariff_1.xml": SignatureOutcome(valid=1),
    # End record ships a secp256r1 key for a secp256k1 signature
    "second_key_fail_ocmf.xml": SignatureOutcome(valid=1, rejected=1),
    "test_ocmf_ebee_01.xml": SignatureOutcome(valid=2),
    "test_ocmf_ebee_02.xml": SignatureOutcome(valid=1, invalid=1),
    "test_ocmf_keba_kcp30.xml": SignatureOutcome(valid=1),
    "test_ocmf_keba_kcp30_fail.xml": SignatureOutcome(valid=0, invalid=1),
    # secp192k1, verified with the ecdsa fallback (OCMFVerifierTest)
    "test_ocmf_transaction_two_values.xml": SignatureOutcome(valid=2),
}


def _verify_all(xml_path: pathlib.Path) -> SignatureOutcome:
    valid = invalid = rejected = 0
    for record in OcmfContainer.from_xml(xml_path):
        try:
            if record.verify_signature():
                valid += 1
            else:
                invalid += 1
        except SignatureVerificationError:
            rejected += 1
    return SignatureOutcome(valid=valid, invalid=invalid, rejected=rejected)


@pytest.mark.parametrize(("xml_file", "expected"), EXPECTED_SIGNATURES.items())
def test_signature_outcomes_match_transparenzsoftware(
    transparency_xml_dir: pathlib.Path, xml_file: str, expected: SignatureOutcome
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        assert _verify_all(transparency_xml_dir / xml_file) == expected


def test_every_corpus_file_with_keys_has_expectation(
    transparency_xml_files: list[pathlib.Path],
) -> None:
    """Fail when a submodule update adds verifiable files without expected outcomes."""
    unclassified = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        for xml_path in transparency_xml_files:
            try:
                container = OcmfContainer.from_xml(xml_path)
            except PyOCMFError:
                continue
            has_key = any(record.public_key is not None for record in container)
            if has_key and xml_path.name not in EXPECTED_SIGNATURES:
                unclassified.append(xml_path.name)
    assert not unclassified, f"Add expected signature outcomes for: {unclassified}"
