"""Parsing tests for other_examples XML files."""

import pathlib

import pytest

from pyocmf.sections.payload import Payload
from pyocmf.sections.signature import Signature
from pyocmf.types.identifiers import IdentificationType
from pyocmf.utils.xml import OcmfContainer

# Check if cryptography is available
try:
    from pyocmf.verification import CRYPTOGRAPHY_AVAILABLE
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


@pytest.fixture
def other_examples_dir() -> pathlib.Path:
    """Return the path to the other_examples resource directory."""
    return pathlib.Path(__file__).parent.parent / "resources" / "other_examples"


def test_other_examples_base64_ocmf(other_examples_dir: pathlib.Path) -> None:
    """Test OCMF parsing for base64_ocmf.xml.

    This file contains OCMF records with ID fields using LOCAL identification
    type, which per OCMF spec has no exact format defined and can contain any
    string value (e.g., UUIDs, arbitrary hex strings, etc.).
    """
    xml_file = other_examples_dir / "base64_ocmf.xml"

    # Parse the XML file
    container = OcmfContainer.from_xml(xml_file)
    assert len(container) > 0, "Expected OCMF data in base64_ocmf.xml"

    # Verify entry
    entry = container[0]
    ocmf_model = entry.ocmf

    # Check OCMF structure
    assert ocmf_model.header == "OCMF"
    assert isinstance(ocmf_model.payload, Payload)
    assert isinstance(ocmf_model.signature, Signature)

    # Check payload has expected fields
    assert ocmf_model.payload.FV == "1.0"
    assert ocmf_model.payload.RD is not None
    assert len(ocmf_model.payload.RD) > 0

    # Check identification type is LOCAL
    assert isinstance(ocmf_model.payload.IT, IdentificationType)
    assert ocmf_model.payload.IT.value == "LOCAL"
    assert ocmf_model.payload.ID == "231443392c0cf905fffa33f763d17dff"

    # Check signature
    assert ocmf_model.signature.SD is not None

    # Check if public key was extracted
    assert entry.public_key is not None
    # public_key is a PublicKey object, verify it has the key data
    assert entry.public_key.key is not None
    assert len(entry.public_key.key) > 0


@pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
def test_other_examples_base64_ocmf_signature_verification(
    other_examples_dir: pathlib.Path,
) -> None:
    """Test signature verification for base64_ocmf.xml.

    Verifies that the OCMF record can be successfully verified with its
    embedded public key.
    """
    xml_file = other_examples_dir / "base64_ocmf.xml"

    # Parse the XML file
    container = OcmfContainer.from_xml(xml_file)
    entry = container[0]

    # Verify signature is valid
    assert entry.public_key is not None, "Public key should be extracted from XML"
    assert entry.verify_signature() is True, "Signature should be valid"


def test_other_examples_working_ocmf(other_examples_dir: pathlib.Path) -> None:
    """Test OCMF parsing for working_ocmf.xml.

    This file contains OCMF records with ID fields using LOCAL identification
    type, which per OCMF spec has no exact format defined and can contain any
    string value (e.g., UUIDs, arbitrary hex strings, etc.).
    """
    xml_file = other_examples_dir / "working_ocmf.xml"

    # Parse the XML file
    container = OcmfContainer.from_xml(xml_file)
    assert len(container) > 0, "Expected OCMF data in working_ocmf.xml"

    # Verify entry
    entry = container[0]
    ocmf_model = entry.ocmf

    # Check OCMF structure
    assert ocmf_model.header == "OCMF"
    assert isinstance(ocmf_model.payload, Payload)
    assert isinstance(ocmf_model.signature, Signature)

    # Check payload has expected fields
    assert ocmf_model.payload.FV == "1.0"
    assert ocmf_model.payload.RD is not None
    assert len(ocmf_model.payload.RD) == 4  # Four readings in this file

    # Check identification type is LOCAL
    assert isinstance(ocmf_model.payload.IT, IdentificationType)
    assert ocmf_model.payload.IT.value == "LOCAL"
    assert ocmf_model.payload.ID == "23141b6bbb1707a53ac3428c8006e60b"

    # Check signature
    assert ocmf_model.signature.SD is not None

    # Check if public key was extracted
    assert entry.public_key is not None
    # public_key is a PublicKey object, verify it has the key data
    assert entry.public_key.key is not None
    assert len(entry.public_key.key) > 0


@pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not installed")
def test_other_examples_working_ocmf_signature_verification(
    other_examples_dir: pathlib.Path,
) -> None:
    """Test signature verification for working_ocmf.xml.

    Verifies that the OCMF record can be successfully verified with its
    embedded public key.
    """
    xml_file = other_examples_dir / "working_ocmf.xml"

    # Parse the XML file
    container = OcmfContainer.from_xml(xml_file)
    entry = container[0]

    # Verify signature is valid
    assert entry.public_key is not None, "Public key should be extracted from XML"
    assert entry.verify_signature() is True, "Signature should be valid"
