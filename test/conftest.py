import pathlib

import pytest

from pyocmf.core import OCMF, Payload
from pyocmf.core.reading import Reading

from .helpers import create_test_ocmf, create_test_payload, create_test_reading

# Shared test data: KEBA KCP30 public key (secp256r1)
KEBA_PUBLIC_KEY = (
    "3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB"
    "0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C2"
    "108A0D6DC7D4AB1A5E1A7955BE"
)

# Shared test data: Valid KEBA OCMF string with matching signature
KEBA_OCMF_STRING = (
    'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
    '"PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
    '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
    '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
    '"ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},'
    '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"",'
    '"ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
    '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
    '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
)

# Shared test data: Tampered OCMF string (RV changed from 0.2596 to 999.9999)
KEBA_OCMF_STRING_TAMPERED = (
    'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5",'
    '"PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE",'
    '"ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"",'
    '"RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"",'
    '"ST":"G","RV":999.9999,"RI":"1-b:1.8.0","RU":"kWh"},'
    '{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"",'
    '"ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|'
    '{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9'
    '022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'
)


@pytest.fixture
def test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "resources" / "transparenzsoftware"


@pytest.fixture
def transparency_xml_dir(test_data_dir: pathlib.Path) -> pathlib.Path:
    return test_data_dir / "src" / "test" / "resources" / "xml"


@pytest.fixture
def transparency_xml_files(transparency_xml_dir: pathlib.Path) -> list[pathlib.Path]:
    return sorted([f for f in transparency_xml_dir.rglob("*.xml") if f.is_file()])


@pytest.fixture
def test_reading() -> Reading:
    return create_test_reading()


@pytest.fixture
def test_payload() -> Payload:
    return create_test_payload()


@pytest.fixture
def test_ocmf() -> OCMF:
    return create_test_ocmf()


@pytest.fixture
def keba_public_key() -> str:
    return KEBA_PUBLIC_KEY


@pytest.fixture
def keba_ocmf_string() -> str:
    return KEBA_OCMF_STRING


@pytest.fixture
def keba_ocmf_string_tampered() -> str:
    return KEBA_OCMF_STRING_TAMPERED
