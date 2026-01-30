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
      const escapedText = ocmfText.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
      const result = await this.pyodide.runPythonAsync(`
from pyocmf import OCMF
import json

try:
    ocmf = OCMF.from_string('''${escapedText}''')
    result = {
        'success': True,
        'data': ocmf.model_dump(),
        'ocmf_string': ocmf.to_string(),
        'ocmf_hex': ocmf.to_string(hex=True)
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
      const escapedHex = hexText.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
      const result = await this.pyodide.runPythonAsync(`
from pyocmf import OCMF
import json

try:
    ocmf = OCMF.from_string('''${escapedHex}''')
    result = {
        'success': True,
        'data': ocmf.model_dump(),
        'ocmf_string': ocmf.to_string(),
        'ocmf_hex': ocmf.to_string(hex=True)
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
   * Parse XML content and extract OCMF data using the public OcmfContainer API
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
from pyocmf import OcmfContainer
from pathlib import Path
import tempfile
import json
import os

try:
    # Write XML to temporary file (OcmfContainer.from_xml expects a file path)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
        tmp.write('''${escapedXml}''')
        tmp_path = tmp.name

    # Parse using the public API
    container = OcmfContainer.from_xml(Path(tmp_path))

    # Clean up temp file
    os.unlink(tmp_path)

    results = []
    for record in container:
        results.append({
            'ocmf': record.ocmf.model_dump(),
            'ocmf_string': record.ocmf.to_string(),
            'public_key_hex': record.public_key.key if record.public_key else None,
            'has_public_key': record.public_key is not None
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
      const escapedOcmf = ocmfString
        .replace(/\\/g, "\\\\")
        .replace(/'/g, "\\'");
      const escapedKey = publicKeyHex
        .replace(/\\/g, "\\\\")
        .replace(/'/g, "\\'");
      const result = await this.pyodide.runPythonAsync(`
from pyocmf import OCMF
import json

try:
    ocmf = OCMF.from_string('''${escapedOcmf}''')
    is_valid = ocmf.verify_signature('''${escapedKey}''')
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
