#!/bin/bash
# Example CLI usage for pyocmf

echo "=== PyOCMF CLI Examples ==="
echo ""

# Example OCMF string from KEBA charging station
OCMF_STRING='OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"","ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}'

PUBLIC_KEY="3059301306072A8648CE3D020106082A8648CE3D030107034200043AEEB45C392357820A58FDFB0857BD77ADA31585C61C430531DFA53B440AFBFDD95AC887C658EA55260F808F55CA948DF235C2108A0D6DC7D4AB1A5E1A7955BE"

echo "1. Basic validation:"
echo "   pyocmf 'OCMF|{...}|{...}'"
echo ""
pyocmf "$OCMF_STRING"
echo ""
echo ""

echo "2. Validation with verbose output:"
echo "   pyocmf 'OCMF|{...}|{...}' --verbose"
echo ""
pyocmf "$OCMF_STRING" --verbose
echo ""
echo ""

echo "3. Validation with signature verification:"
echo "   pyocmf 'OCMF|{...}|{...}' --public-key <hex_key>"
echo ""
pyocmf "$OCMF_STRING" --public-key "$PUBLIC_KEY"
echo ""
echo ""

echo "4. Validation of hex-encoded OCMF:"
echo "   pyocmf <hex_string> --hex"
echo ""
# Convert to hex for demonstration
HEX_OCMF=$(python3 -c "print('$OCMF_STRING'.encode('utf-8').hex())")
pyocmf "$HEX_OCMF" --hex
echo ""
echo ""

echo "5. Invalid OCMF (demonstrates error handling):"
echo "   pyocmf 'INVALID|data|here'"
echo ""
pyocmf "INVALID|data|here" || echo "Expected failure: Invalid OCMF format"
echo ""
echo ""

echo "=== Examples Complete ==="
