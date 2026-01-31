/**
 * OCMF Bridge - JavaScript to Python communication layer
 */

class OCMFBridge {
  constructor(pyodide) {
    this.pyodide = pyodide;
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) {
      return;
    }

    try {
      await this.pyodide.runPythonAsync(`
import pyocmf
print(f"PyOCMF v{pyocmf.__version__} loaded successfully")
      `);

      console.log("PyOCMF bridge initialized");
      this.isInitialized = true;
    } catch (error) {
      console.error("Failed to initialize OCMF bridge:", error);
      throw error;
    }
  }

  checkInitialized() {
    if (!this.isInitialized) {
      throw new Error("OCMF Bridge not initialized. Call initialize() first.");
    }
  }

  /**
   * Parse an OCMF string and optionally verify signature
   */
  async parseString(ocmfText, publicKeyHex = null) {
    this.checkInitialized();

    try {
      const escapedText = ocmfText.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
      const escapedKey = publicKeyHex
        ? publicKeyHex.replace(/\\/g, "\\\\").replace(/'/g, "\\'")
        : "";

      const result = await this.pyodide.runPythonAsync(`
from pyocmf import OCMF
import json

try:
    ocmf = OCMF.from_string('''${escapedText}''')

    # Check compliance
    issues = ocmf.check_eichrecht()
    compliance_issues = [
        {
            'code': issue.code.value,
            'message': issue.message,
            'severity': issue.severity.value,
            'field': issue.field
        }
        for issue in issues
    ]

    # Verify signature if public key provided
    signature_valid = None
    signature_error = None
    public_key_hex = '''${escapedKey}''' if '''${escapedKey}''' else None

    if public_key_hex:
        try:
            signature_valid = ocmf.verify_signature(public_key_hex)
        except Exception as e:
            signature_error = str(e)

    result = {
        'success': True,
        'data': ocmf.model_dump(mode='json'),
        'ocmf_string': ocmf.to_string(),
        'signature_valid': signature_valid,
        'signature_error': signature_error,
        'compliance_issues': compliance_issues,
        'is_compliant': ocmf.is_eichrecht_compliant
    }
except Exception as e:
    result = {
        'success': False,
        'error': str(e),
        'error_type': type(e).__name__
    }

json.dumps(result)
      `);

      return JSON.parse(result);
    } catch (error) {
      return {
        success: false,
        error: error.message,
        error_type: "JavaScriptError",
      };
    }
  }

  /**
   * Parse XML content and extract OCMF data with verification
   */
  async parseXML(xmlContent) {
    this.checkInitialized();

    try {
      const escapedXml = xmlContent
        .replace(/\\/g, "\\\\")
        .replace(/'''/g, "\\'\\'\\'");

      const result = await this.pyodide.runPythonAsync(`
from pyocmf import OcmfContainer
from pathlib import Path
import tempfile
import json
import os

try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
        tmp.write('''${escapedXml}''')
        tmp_path = tmp.name

    container = OcmfContainer.from_xml(Path(tmp_path))
    os.unlink(tmp_path)

    results = []
    for record in container:
        ocmf = record.ocmf

        # Check compliance
        issues = ocmf.check_eichrecht()
        compliance_issues = [
            {
                'code': issue.code.value,
                'message': issue.message,
                'severity': issue.severity.value,
                'field': issue.field
            }
            for issue in issues
        ]

        # Verify signature if public key available
        signature_valid = None
        signature_error = None

        if record.public_key:
            try:
                signature_valid = ocmf.verify_signature(record.public_key)
            except Exception as e:
                signature_error = str(e)

        results.append({
            'ocmf': ocmf.model_dump(mode='json'),
            'ocmf_string': ocmf.to_string(),
            'public_key_hex': record.public_key.key if record.public_key else None,
            'signature_valid': signature_valid,
            'signature_error': signature_error,
            'compliance_issues': compliance_issues,
            'is_compliant': ocmf.is_eichrecht_compliant
        })

    result = {'success': True, 'entries': results, 'count': len(results)}
except Exception as e:
    result = {'success': False, 'error': str(e), 'error_type': type(e).__name__}

json.dumps(result)
      `);

      return JSON.parse(result);
    } catch (error) {
      return {
        success: false,
        error: error.message,
        error_type: "JavaScriptError",
      };
    }
  }
}
