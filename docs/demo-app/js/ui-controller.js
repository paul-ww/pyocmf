/**
 * UI Controller - Handles all DOM manipulation and user interactions
 */

class UIController {
    constructor(ocmfBridge) {
        this.bridge = ocmfBridge;
        this.currentData = null;
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Parse button
        const parseBtn = document.getElementById('parseBtn');
        if (parseBtn) {
            parseBtn.addEventListener('click', () => this.handleParse());
        }

        // File upload
        const fileInput = document.getElementById('xmlFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Format toggle
        const formatSelect = document.getElementById('inputFormat');
        if (formatSelect) {
            formatSelect.addEventListener('change', (e) => this.handleFormatChange(e));
        }

        // Example loader
        const loadExampleBtn = document.getElementById('loadExampleBtn');
        if (loadExampleBtn) {
            loadExampleBtn.addEventListener('click', () => this.loadExample());
        }

        // Copy buttons
        document.querySelectorAll('[data-copy]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleCopy(e));
        });

        // Verify signature button
        const verifyBtn = document.getElementById('verifyBtn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => this.handleVerifySignature());
        }
    }

    /**
     * Update loading progress
     */
    updateProgress(stage, percent, message) {
        const progressBar = document.getElementById('loadingProgress');
        const progressText = document.getElementById('loadingText');

        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
        }

        if (progressText) {
            progressText.textContent = message;
        }
    }

    /**
     * Show/hide sections
     */
    showSection(sectionId) {
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('hidden');
        });

        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
        }
    }

    /**
     * Handle parse button click
     */
    async handleParse() {
        const inputText = document.getElementById('ocmfInput').value.trim();
        const inputFormat = document.getElementById('inputFormat').value;

        if (!inputText) {
            this.showError('Please enter OCMF data');
            return;
        }

        this.showLoading('Parsing OCMF data...');

        try {
            let result;

            if (inputFormat === 'hex') {
                result = await this.bridge.parseHex(inputText);
            } else {
                result = await this.bridge.parseString(inputText);
            }

            if (result.success) {
                this.currentData = result;
                this.displayResult(result);
            } else {
                this.showError(result.error || 'Failed to parse OCMF data');
            }
        } catch (error) {
            this.showError(`Error: ${error.message}`);
        }
    }

    /**
     * Handle file upload
     */
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.showLoading('Reading XML file...');

        try {
            const content = await file.text();
            const result = await this.bridge.parseXML(content);

            if (result.success) {
                this.displayXMLResult(result);
            } else {
                this.showError(result.error || 'Failed to parse XML file');
            }
        } catch (error) {
            this.showError(`Error reading file: ${error.message}`);
        }
    }

    /**
     * Handle format change
     */
    handleFormatChange(event) {
        const format = event.target.value;
        const placeholder = document.getElementById('ocmfInput');

        if (format === 'hex') {
            placeholder.placeholder = 'Paste hex-encoded OCMF data here...';
        } else {
            placeholder.placeholder = 'Paste OCMF string here (OCMF|{...}|{...})...';
        }
    }

    /**
     * Load example data
     */
    async loadExample() {
        const exampleOCMF = 'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"","ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}';

        document.getElementById('ocmfInput').value = exampleOCMF;
        document.getElementById('inputFormat').value = 'plain';

        await this.handleParse();
    }

    /**
     * Handle signature verification
     */
    async handleVerifySignature() {
        if (!this.currentData || !this.currentData.ocmf_string) {
            this.showError('No OCMF data loaded');
            return;
        }

        const publicKeyInput = document.getElementById('publicKeyInput');
        const publicKeyHex = publicKeyInput ? publicKeyInput.value.trim() : '';

        if (!publicKeyHex) {
            this.showError('Please enter a public key');
            return;
        }

        this.showLoading('Verifying signature...');

        try {
            const result = await this.bridge.verifySignature(
                this.currentData.ocmf_string,
                publicKeyHex
            );

            this.displayVerificationResult(result);
        } catch (error) {
            this.showError(`Verification error: ${error.message}`);
        }
    }

    /**
     * Display parsed result
     */
    displayResult(result) {
        this.showSection('resultSection');

        const resultContainer = document.getElementById('resultContainer');
        if (!resultContainer) return;

        const data = result.data;

        let html = '<div class="result-content">';

        // Header section
        html += `
            <div class="result-section">
                <h3>Format Information</h3>
                <table class="info-table">
                    <tr><td><strong>Format Version:</strong></td><td>${data.payload.FV}</td></tr>
                    <tr><td><strong>Gateway ID:</strong></td><td>${data.payload.GI}</td></tr>
                    <tr><td><strong>Gateway Serial:</strong></td><td>${data.payload.GS || 'N/A'}</td></tr>
                    <tr><td><strong>Gateway Version:</strong></td><td>${data.payload.GV || 'N/A'}</td></tr>
                    <tr><td><strong>Pagination:</strong></td><td>${data.payload.PG}</td></tr>
                </table>
            </div>
        `;

        // Readings section
        if (data.payload.RD && data.payload.RD.length > 0) {
            html += '<div class="result-section"><h3>Meter Readings</h3><table class="readings-table">';
            html += '<thead><tr><th>Timestamp</th><th>Type</th><th>Value</th><th>Unit</th><th>Status</th></tr></thead><tbody>';

            data.payload.RD.forEach(reading => {
                html += `
                    <tr>
                        <td>${reading.TM}</td>
                        <td>${reading.TX}</td>
                        <td>${reading.RV}</td>
                        <td>${reading.RU}</td>
                        <td>${reading.ST}</td>
                    </tr>
                `;
            });

            html += '</tbody></table></div>';
        }

        // Signature section
        html += `
            <div class="result-section">
                <h3>Signature Information</h3>
                <table class="info-table">
                    <tr><td><strong>Algorithm:</strong></td><td>${data.signature.SA || 'N/A'}</td></tr>
                    <tr><td><strong>Encoding:</strong></td><td>${data.signature.SE || 'N/A'}</td></tr>
                    <tr><td><strong>Signature Data:</strong></td><td class="signature-data">${data.signature.SD.substring(0, 60)}...</td></tr>
                </table>
            </div>
        `;

        // Export options
        html += `
            <div class="result-section">
                <h3>Export</h3>
                <div class="export-buttons">
                    <button onclick="uiController.copyToClipboard('${this.escapeHtml(result.ocmf_string)}', 'OCMF String')">Copy OCMF String</button>
                    <button onclick="uiController.copyToClipboard('${result.ocmf_hex}', 'Hex')">Copy Hex</button>
                    <button onclick="uiController.downloadJSON(${JSON.stringify(data)})">Download JSON</button>
                </div>
            </div>
        `;

        html += '</div>';

        resultContainer.innerHTML = html;
    }

    /**
     * Display XML parsing result with multiple entries
     */
    displayXMLResult(result) {
        this.showSection('resultSection');

        const resultContainer = document.getElementById('resultContainer');
        if (!resultContainer) return;

        let html = `<div class="result-content">`;
        html += `<h3>Found ${result.count} OCMF ${result.count === 1 ? 'entry' : 'entries'}</h3>`;

        result.entries.forEach((entry, index) => {
            html += `<div class="xml-entry">`;
            html += `<h4>Entry ${index + 1}</h4>`;

            if (entry.transaction_id) {
                html += `<p><strong>Transaction ID:</strong> ${entry.transaction_id}</p>`;
            }
            if (entry.context) {
                html += `<p><strong>Context:</strong> ${entry.context}</p>`;
            }

            // Store entry data for verification
            this.currentData = { ocmf_string: entry.ocmf_string, data: entry.ocmf };

            if (entry.public_key_hex) {
                html += `<p><strong>Public Key:</strong> <code class="public-key">${entry.public_key_hex.substring(0, 40)}...</code></p>`;
                html += `<button onclick="uiController.autoVerify('${this.escapeHtml(entry.ocmf_string)}', '${entry.public_key_hex}')">Verify Signature</button>`;
            }

            html += `</div>`;
        });

        html += `</div>`;
        resultContainer.innerHTML = html;
    }

    /**
     * Display verification result
     */
    displayVerificationResult(result) {
        this.showSection('resultSection');

        const verifyContainer = document.getElementById('verificationResult');
        if (!verifyContainer) return;

        if (result.success) {
            const status = result.valid ? '✓ VALID' : '✗ INVALID';
            const statusClass = result.valid ? 'valid' : 'invalid';

            verifyContainer.innerHTML = `
                <div class="verification-status ${statusClass}">
                    <h3>${status}</h3>
                    <p>Algorithm: ${result.algorithm}</p>
                    <p>Encoding: ${result.encoding}</p>
                </div>
            `;
        } else {
            verifyContainer.innerHTML = `
                <div class="verification-status error">
                    <h3>Verification Failed</h3>
                    <p>${result.error}</p>
                </div>
            `;
        }
    }

    /**
     * Show loading state
     */
    showLoading(message) {
        this.showSection('loadingSection');
        const loadingText = document.getElementById('loadingText');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    /**
     * Show error
     */
    showError(message) {
        this.showSection('errorSection');
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
    }

    /**
     * Copy to clipboard
     */
    async copyToClipboard(text, label = 'Text') {
        try {
            await navigator.clipboard.writeText(text);
            alert(`${label} copied to clipboard!`);
        } catch (error) {
            console.error('Failed to copy:', error);
            alert('Failed to copy to clipboard');
        }
    }

    /**
     * Download JSON
     */
    downloadJSON(data) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ocmf-data.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Auto-verify signature (from XML with public key)
     */
    async autoVerify(ocmfString, publicKeyHex) {
        this.currentData = { ocmf_string: ocmfString };
        const publicKeyInput = document.getElementById('publicKeyInput');
        if (publicKeyInput) {
            publicKeyInput.value = publicKeyHex;
        }
        await this.handleVerifySignature();
    }

    /**
     * Escape HTML for safe insertion
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Global reference for inline event handlers
let uiController = null;
