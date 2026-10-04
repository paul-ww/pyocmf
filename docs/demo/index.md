---
title: Browser Demo
description: Check OCMF charging records in your browser, covering the signature, Eichrecht compliance and spec conformance.
hide:
  - navigation
  - toc
---

# Browser Demo

Check OCMF charging records in your browser. PyOCMF runs locally with
[Pyodide](https://pyodide.org), so nothing leaves this page.

<div class="ocmf-demo">
  <p id="runtimeStatus" class="runtime" role="status">Starting Python…</p>
  <div class="sheet">
    <section class="input" aria-labelledby="inputHeading">
      <h2 id="inputHeading" class="visually-hidden">Input</h2>
      <div class="step">
        <h3><span class="step-number">1</span>Record</h3>
        <div class="segmented" role="tablist" aria-label="Input type">
          <button id="modeText" type="button" role="tab" aria-selected="true" aria-controls="textPanel">Paste record</button>
          <button id="modeXml" type="button" role="tab" aria-selected="false" aria-controls="xmlPanel">Open XML file</button>
          <button id="modeQr" type="button" role="tab" aria-selected="false" aria-controls="qrPanel">Scan QR code</button>
        </div>
        <div id="textPanel" role="tabpanel" aria-labelledby="modeText">
          <label class="field-label" for="ocmfInput">OCMF string, plain or hex-encoded</label>
          <textarea id="ocmfInput" rows="7" spellcheck="false" placeholder='OCMF|{"FV":"1.0","GI":…}|{"SD":"3045…"}'></textarea>
        </div>
        <div id="xmlPanel" role="tabpanel" aria-labelledby="modeXml" hidden>
          <label class="dropzone" for="xmlInput" id="dropzone">
            <span id="xmlName">Choose or drop a Transparenzsoftware XML file</span>
            <small>Public keys are read from the file</small>
          </label>
          <input id="xmlInput" type="file" accept=".xml,text/xml,application/xml" class="visually-hidden" />
        </div>
        <div id="qrPanel" role="tabpanel" aria-labelledby="modeQr" hidden>
          <div class="scanner">
            <video id="qrVideo" playsinline muted hidden></video>
            <p id="qrStatus">Point the camera at a QR code with OCMF data, or open a photo of one.</p>
          </div>
          <div class="scanner-actions">
            <button id="qrCameraButton" type="button" class="md-button">Use camera</button>
            <label class="md-button" for="qrImageInput">Open image</label>
            <input id="qrImageInput" type="file" accept="image/*" class="visually-hidden" />
          </div>
        </div>
        <div class="examples">
          <label class="field-label" for="exampleSelect">Or load an example</label>
          <select id="exampleSelect">
            <option value="">Choose an example…</option>
          </select>
          <p id="exampleDescription" class="hint"></p>
        </div>
      </div>
      <div class="step" id="keyStep">
        <h3><span class="step-number">2</span>Public key <small>optional</small></h3>
        <label class="field-label" for="publicKeyInput">Hex or base64</label>
        <input id="publicKeyInput" type="text" spellcheck="false" autocomplete="off" placeholder="3059301306072A8648CE3D0201…" />
        <p id="keyHint" class="hint">Not needed if the record carries its own key, as QR codes often do.</p>
      </div>
      <div class="step">
        <h3><span class="step-number">3</span>Check</h3>
        <label class="checkbox" for="strictInput">
          <input id="strictInput" type="checkbox" />
          <span>Strict mode <small>Reject records that deviate from the OCMF Spec</small></span>
        </label>
        <button id="checkButton" type="button" class="md-button md-button--primary" disabled>Preparing Python…</button>
      </div>
    </section>
    <section class="result" aria-labelledby="resultHeading" aria-live="polite">
      <h2 id="resultHeading" class="visually-hidden">Result</h2>
      <div id="result">
        <div class="empty">
          <p class="empty-title">Results appear here</p>
          <p>Each record is checked three ways:</p>
          <dl class="empty-list">
            <dt>Signature</dt>
            <dd>Is the record unchanged since the meter signed it?</dd>
            <dt>Eichrecht</dt>
            <dd>Can the charging session be billed under German calibration law?</dd>
            <dt>OCMF Spec</dt>
            <dd>Does the record follow the format specification?</dd>
          </dl>
        </div>
      </div>
    </section>
  </div>
</div>

!!! info "Unofficial"
    This demo is not a legally binding verification. For that, use the
    [Transparenzsoftware](https://www.safe-ev.de/de/transparenzsoftware.php) by S.A.F.E. e.V.

<script>
  // Instant navigation re-runs this script on every visit, but the demo scripts declare
  // globals and must load only once
  window.ocmfDemoScripts ??= Promise.all(
    ["js/runtime.js", "js/qr.js", "js/app.js"].map(
      (src) =>
        new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.src = new URL(src, window.location.href).href;
          script.onload = resolve;
          script.onerror = () => reject(new Error(`${src} could not be loaded`));
          document.head.append(script);
        }),
    ),
  );
  window.ocmfDemoScripts
    .then(() => mountOcmfDemo())
    .catch((error) => {
      window.ocmfDemoScripts = undefined;
      document.getElementById("runtimeStatus").textContent = `The demo failed to load: ${error.message}`;
    });
</script>
