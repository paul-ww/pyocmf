/**
 * UI Controller - Handles DOM manipulation and user interactions
 */

class UIController {
  constructor(ocmfBridge) {
    this.bridge = ocmfBridge;
  }

  initializeEventListeners() {
    document
      .getElementById("parseBtn")
      ?.addEventListener("click", () => this.handleParse());
    document
      .getElementById("xmlFileInput")
      ?.addEventListener("change", (e) => this.handleFileUpload(e));
    document
      .getElementById("loadExampleBtn")
      ?.addEventListener("click", () => this.loadExample());

    // Input method tabs
    document.querySelectorAll(".method-tab").forEach((tab) => {
      tab.addEventListener("click", (e) =>
        this.switchInputMethod(e.target.dataset.method),
      );
    });
  }

  switchInputMethod(method) {
    document
      .querySelectorAll(".method-tab")
      .forEach((t) => t.classList.remove("active"));
    document
      .querySelector(`[data-method="${method}"]`)
      ?.classList.add("active");

    document
      .getElementById("textInputMethod")
      ?.classList.toggle("hidden", method !== "text");
    document
      .getElementById("fileInputMethod")
      ?.classList.toggle("hidden", method !== "file");
  }

  updateProgress(stage, percent, message) {
    const progressBar = document.getElementById("loadingProgress");
    const progressText = document.getElementById("loadingText");

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }
    if (progressText) {
      progressText.textContent = message;
    }
  }

  showSection(sectionId) {
    document
      .querySelectorAll(".content-section")
      .forEach((s) => s.classList.add("hidden"));
    document.getElementById(sectionId)?.classList.remove("hidden");
  }

  async handleParse() {
    const inputText = document.getElementById("ocmfInput").value.trim();
    const publicKey =
      document.getElementById("publicKeyInput")?.value.trim() || null;

    if (!inputText) {
      this.showError("Please enter OCMF data");
      return;
    }

    this.showLoading("Parsing OCMF data...");

    try {
      const result = await this.bridge.parseString(inputText, publicKey);

      if (result.success) {
        this.displayResult(result);
      } else {
        this.showError(result.error || "Failed to parse OCMF data");
      }
    } catch (error) {
      this.showError(`Error: ${error.message}`);
    }
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    this.showLoading("Reading XML file...");

    try {
      const content = await file.text();
      const result = await this.bridge.parseXML(content);

      if (result.success) {
        this.displayXMLResult(result);
      } else {
        this.showError(result.error || "Failed to parse XML file");
      }
    } catch (error) {
      this.showError(`Error reading file: ${error.message}`);
    }
  }

  async loadExample() {
    const exampleOCMF =
      'OCMF|{"FV":"1.0","GI":"KEBA_KCP30","GS":"17619300","GV":"2.8.5","PG":"T32","IS":false,"IL":"NONE","IF":["RFID_NONE","OCPP_NONE","ISO15118_NONE","PLMN_NONE"],"IT":"NONE","ID":"","RD":[{"TM":"2019-08-13T10:03:15,000+0000 I","TX":"B","EF":"","ST":"G","RV":0.2596,"RI":"1-b:1.8.0","RU":"kWh"},{"TM":"2019-08-13T10:03:36,000+0000 R","TX":"E","EF":"","ST":"G","RV":0.2597,"RI":"1-b:1.8.0","RU":"kWh"}]}|{"SD":"304502200E2F107C987A300AC1695CA89EA149A8CDFA16188AF0A33EE64B67964AA943F9022100889A72B6D65364BEA8562E7F6A0253157ACFF84FE4929A93B5964D23C4265699"}';

    document.getElementById("ocmfInput").value = exampleOCMF;
    await this.handleParse();
  }

  displayResult(result) {
    this.showSection("resultSection");

    const container = document.getElementById("resultContainer");
    if (!container) return;

    const data = result.data;
    let html = '<div class="result-content">';

    // Signature verification status
    html += this.renderSignatureStatus(
      result.signature_valid,
      result.signature_error,
      data.signature,
    );

    // Compliance status
    html += this.renderComplianceStatus(
      result.is_compliant,
      result.compliance_issues,
    );

    // Meter readings
    html += this.renderReadings(data.payload.RD);

    // Payload info
    html += this.renderPayloadInfo(data.payload);

    html += "</div>";
    container.innerHTML = html;
  }

  displayXMLResult(result) {
    this.showSection("resultSection");

    const container = document.getElementById("resultContainer");
    if (!container) return;

    let html = `<div class="result-content">`;
    html += `<p class="entry-count">Found ${result.count} OCMF ${result.count === 1 ? "entry" : "entries"}</p>`;

    result.entries.forEach((entry, index) => {
      html += `<div class="xml-entry">`;
      if (result.count > 1) {
        html += `<h3>Entry ${index + 1}</h3>`;
      }

      // Signature verification status
      html += this.renderSignatureStatus(
        entry.signature_valid,
        entry.signature_error,
        entry.ocmf.signature,
      );

      // Compliance status
      html += this.renderComplianceStatus(
        entry.is_compliant,
        entry.compliance_issues,
      );

      // Meter readings
      html += this.renderReadings(entry.ocmf.payload.RD);

      // Payload info
      html += this.renderPayloadInfo(entry.ocmf.payload);

      html += `</div>`;
    });

    html += `</div>`;
    container.innerHTML = html;
  }

  renderSignatureStatus(valid, error, signature) {
    let html = '<div class="result-section signature-section">';
    html += "<h3>Signature</h3>";

    if (valid === true) {
      html += '<div class="status-badge valid">Valid</div>';
    } else if (valid === false) {
      html += '<div class="status-badge invalid">Invalid</div>';
    } else if (error) {
      html += `<div class="status-badge error">Error: ${this.escapeHtml(error)}</div>`;
    } else {
      html +=
        '<div class="status-badge unknown">Not verified (no public key)</div>';
    }

    html += `<table class="info-table">
            <tr><td>Algorithm:</td><td>${signature.SA || "N/A"}</td></tr>
            <tr><td>Encoding:</td><td>${signature.SE || "N/A"}</td></tr>
        </table>`;

    html += "</div>";
    return html;
  }

  renderComplianceStatus(isCompliant, issues) {
    let html = '<div class="result-section compliance-section">';
    html += "<h3>Eichrecht Compliance</h3>";

    if (isCompliant) {
      html += '<div class="status-badge valid">Compliant</div>';
    } else {
      const errors = issues.filter((i) => i.severity === "error");
      const warnings = issues.filter((i) => i.severity === "warning");

      if (errors.length > 0) {
        html += '<div class="status-badge invalid">Non-compliant</div>';
      } else if (warnings.length > 0) {
        html += '<div class="status-badge warning">Warnings</div>';
      }
    }

    if (issues && issues.length > 0) {
      html += '<ul class="issues-list">';
      issues.forEach((issue) => {
        const icon = issue.severity === "error" ? "✗" : "⚠";
        const cls = issue.severity === "error" ? "error" : "warning";
        html += `<li class="${cls}">${icon} <strong>${issue.code}</strong>: ${this.escapeHtml(issue.message)}</li>`;
      });
      html += "</ul>";
    }

    html += "</div>";
    return html;
  }

  renderReadings(readings) {
    if (!readings || readings.length === 0) return "";

    let html = '<div class="result-section">';
    html += "<h3>Meter Readings</h3>";
    html +=
      '<table class="readings-table"><thead><tr><th>Time</th><th>Type</th><th>Value</th><th>Unit</th><th>Status</th></tr></thead><tbody>';

    readings.forEach((r) => {
      html += `<tr>
                <td>${r.TM}</td>
                <td>${r.TX}</td>
                <td>${r.RV}</td>
                <td>${r.RU}</td>
                <td>${r.ST}</td>
            </tr>`;
    });

    html += "</tbody></table></div>";
    return html;
  }

  renderPayloadInfo(payload) {
    let html = '<div class="result-section">';
    html += "<h3>Device Info</h3>";
    html += `<table class="info-table">
            <tr><td>Format Version:</td><td>${payload.FV}</td></tr>
            <tr><td>Gateway ID:</td><td>${payload.GI}</td></tr>
            <tr><td>Gateway Serial:</td><td>${payload.GS || "N/A"}</td></tr>
            <tr><td>Gateway Version:</td><td>${payload.GV || "N/A"}</td></tr>
            <tr><td>Pagination:</td><td>${payload.PG}</td></tr>
        </table>`;
    html += "</div>";
    return html;
  }

  showLoading(message) {
    this.showSection("loadingSection");
    const loadingText = document.getElementById("loadingText");
    if (loadingText) {
      loadingText.textContent = message;
    }
  }

  showError(message) {
    this.showSection("errorSection");
    const errorMessage = document.getElementById("errorMessage");
    if (errorMessage) {
      errorMessage.textContent = message;
    }
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

let uiController = null;
