/**
 * OCMF Bridge - JavaScript to Python communication layer
 * Provides a clean API for calling pyocmf functions from JavaScript
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
      // Verify pyocmf is available
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
   * Parse an OCMF string
   * @param {string} ocmfText - OCMF string in format "OCMF|{...}|{...}"
   * @returns {Object} Parsed result with success flag
   */
  async parseString(ocmfText) {
    this.checkInitialized();

    try {
      const result = await this.pyodide.runPythonAsync(`
        from pyocmf import OCMF
        import json

        try:
            ocmf = OCMF.from_string('''${ocmfText.replace(/'/g, "\\'")}''')
            result = {
                'success': True,
                'data': ocmf.model_dump(),
                'ocmf_string': ocmf.to_string(),
                'ocmf_hex': ocmf.to_hex()
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
   * Parse a hex-encoded OCMF string
   * @param {string} hexText - Hex-encoded OCMF string
   * @returns {Object} Parsed result with success flag
   */
  async parseHex(hexText) {
    this.checkInitialized();

    try {
      const result = await this.pyodide.runPythonAsync(`
        from pyocmf import OCMF
        import json

        try:
            ocmf = OCMF.from_hex('''${hexText.replace(/'/g, "\\'")}''')
            result = {
                'success': True,
                'data': ocmf.model_dump(),
                'ocmf_string': ocmf.to_string(),
                'ocmf_hex': ocmf.to_hex()
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
   * Parse XML content and extract OCMF data
   * @param {string} xmlContent - XML file content as string
   * @returns {Object} Result with entries array or error
   */
  async parseXML(xmlContent) {
    this.checkInitialized();

    try {
      // Escape the XML content for Python
      const escapedXml = xmlContent
        .replace(/\\/g, "\\\\")
        .replace(/'''/g, "\\'\\'\\'");

      const result = await this.pyodide.runPythonAsync(`
        from pyocmf import OCMF
        from pyocmf.utils.xml import _extract_from_signed_data, _extract_from_encoded_data, _extract_from_any_signed_data, _extract_public_key
        import xml.etree.ElementTree as ET
        import json

        try:
            root = ET.fromstring('''${escapedXml}''')
            results = []
            seen_strings = set()

            for value_elem in root.findall('value'):
                ocmf_str = (
                    _extract_from_signed_data(value_elem)
                    or _extract_from_encoded_data(value_elem)
                    or _extract_from_any_signed_data(value_elem)
                )

                if ocmf_str and ocmf_str not in seen_strings:
                    seen_strings.add(ocmf_str)
                    public_key = _extract_public_key(value_elem)
                    ocmf = OCMF.from_string(ocmf_str)

                    results.append({
                        'ocmf': ocmf.model_dump(),
                        'ocmf_string': ocmf_str,
                        'public_key_hex': public_key.key_hex if public_key else None,
                        'transaction_id': value_elem.get('transactionId'),
                        'context': value_elem.get('context')
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

  /**
   * Verify an OCMF signature
   * @param {string} ocmfString - OCMF string to verify
   * @param {string} publicKeyHex - Public key in hex format
   * @returns {Object} Verification result
   */
  async verifySignature(ocmfString, publicKeyHex) {
    this.checkInitialized();

    try {
      const result = await this.pyodide.runPythonAsync(`
        from pyocmf import OCMF
        import json

        try:
            ocmf = OCMF.from_string('''${ocmfString.replace(/'/g, "\\'")}''')
            is_valid = ocmf.verify_signature('''${publicKeyHex.replace(/'/g, "\\'")}''')
            result = {
                'success': True,
                'valid': is_valid,
                'algorithm': ocmf.signature.SA,
                'encoding': ocmf.signature.SE
            }
        except ImportError:
            result = {'success': False, 'error': 'Cryptography library not available', 'error_type': 'CryptoNotAvailable'}
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
