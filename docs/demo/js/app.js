/**
 * Browser demo UI: three input steps on the left, the report on the right.
 * Record data is untrusted, so the report is built with textContent only.
 */

(function () {
  "use strict";

  const READING_REASONS = {
    B: "Begin",
    C: "Charging",
    X: "Exception",
    E: "End",
    L: "Terminated locally",
    R: "Terminated remotely",
    A: "Aborted",
    P: "Power failure",
    S: "Suspended",
    T: "Tariff change",
  };

  const $ = (id) => document.getElementById(id);
  const ui = {
    status: $("runtimeStatus"),
    modeText: $("modeText"),
    modeXml: $("modeXml"),
    textPanel: $("textPanel"),
    xmlPanel: $("xmlPanel"),
    ocmfInput: $("ocmfInput"),
    xmlInput: $("xmlInput"),
    xmlName: $("xmlName"),
    dropzone: $("dropzone"),
    exampleSelect: $("exampleSelect"),
    exampleDescription: $("exampleDescription"),
    publicKeyInput: $("publicKeyInput"),
    keyHint: $("keyHint"),
    strictInput: $("strictInput"),
    checkButton: $("checkButton"),
    result: $("result"),
  };

  const state = { mode: "text", xml: null, runtime: null, examples: [], pendingCheck: false };

  function h(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
      if (value === null || value === undefined || value === false) continue;
      if (key === "className") node.className = value;
      else node.setAttribute(key, value === true ? "" : value);
    }
    for (const child of children.flat(Infinity)) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }

  /* ---------- Input ---------- */

  function setMode(mode) {
    state.mode = mode;
    ui.modeText.setAttribute("aria-selected", String(mode === "text"));
    ui.modeXml.setAttribute("aria-selected", String(mode === "xml"));
    ui.textPanel.hidden = mode !== "text";
    ui.xmlPanel.hidden = mode !== "xml";
    ui.publicKeyInput.disabled = mode === "xml";
    ui.keyHint.textContent =
      mode === "xml" ? "XML files carry their own public keys." : "Without a key, the signature is not verified.";
    updateCheckButton();
  }

  function hasInput() {
    return state.mode === "text" ? ui.ocmfInput.value.trim() !== "" : state.xml !== null;
  }

  function updateCheckButton() {
    if (!state.runtime) {
      ui.checkButton.disabled = true;
      return;
    }
    ui.checkButton.textContent = state.mode === "xml" ? "Check file" : "Check record";
    ui.checkButton.disabled = !hasInput();
  }

  async function loadXmlFile(file) {
    state.xml = { name: file.name, content: await file.text() };
    ui.xmlName.textContent = file.name;
    updateCheckButton();
  }

  async function loadExamples() {
    try {
      state.examples = await (await fetch("examples/examples.json")).json();
    } catch {
      ui.exampleSelect.disabled = true;
      return;
    }
    for (const example of state.examples) {
      ui.exampleSelect.append(h("option", { value: example.id }, example.label));
    }
  }

  async function applyExample(id) {
    const example = state.examples.find((e) => e.id === id);
    ui.exampleDescription.textContent = example ? example.description : "";
    if (!example) return;
    if (example.kind === "xml") {
      const content = await (await fetch(`examples/${example.file}`)).text();
      state.xml = { name: example.file, content };
      ui.xmlName.textContent = example.file;
      setMode("xml");
    } else {
      ui.ocmfInput.value = example.ocmf;
      ui.publicKeyInput.value = example.publicKey || "";
      setMode("text");
    }
    if (state.runtime) runCheck();
    else state.pendingCheck = true;
  }

  /* ---------- Check ---------- */

  function runCheck() {
    if (!hasInput()) return;
    const strict = ui.strictInput.checked;
    ui.checkButton.disabled = true;
    ui.checkButton.textContent = "Checking…";
    // Let the button repaint before Python blocks the main thread
    setTimeout(() => {
      let report;
      try {
        report =
          state.mode === "xml"
            ? state.runtime.analyzeXml(state.xml.content, strict)
            : state.runtime.analyzeText(ui.ocmfInput.value.trim(), ui.publicKeyInput.value.trim(), strict);
      } catch (error) {
        report = { ok: false, error: String(error), errorType: "PythonError" };
      }
      renderReport(report);
      updateCheckButton();
    }, 20);
  }

  /* ---------- Report ---------- */

  const ICONS = { ok: "✓", warn: "!", error: "✗", info: "~", muted: "–" };

  function plural(count, word) {
    return `${count} ${word}${count === 1 ? "" : "s"}`;
  }

  function duration(seconds) {
    if (seconds === null || seconds === undefined) return null;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const rest = seconds % 60;
    if (hours) return `${hours} h ${minutes} min`;
    if (minutes) return rest ? `${minutes} min ${rest} s` : `${minutes} min`;
    return `${rest} s`;
  }

  function energyText(energy) {
    if (!energy) return null;
    const time = duration(energy.seconds);
    return `${energy.value} ${energy.unit}${time ? ` in ${time}` : ""}`;
  }

  function signatureVerdict(records) {
    const statuses = records.map((r) => r.signature.status);
    const count = (s) => statuses.filter((x) => x === s).length;
    if (count("invalid")) {
      return ["error", "Invalid", `${count("invalid")} of ${plural(records.length, "record")} fail`];
    }
    if (count("error")) {
      return ["error", "Not verified", records.find((r) => r.signature.status === "error").signature.message];
    }
    if (count("valid") === records.length) {
      return ["ok", "Valid", [...new Set(records.map((r) => r.signature.algorithm))].join(", ")];
    }
    if (count("valid")) return ["warn", "Partly checked", `${count("valid")} of ${records.length} records have a key`];
    return ["muted", "Not checked", "No public key"];
  }

  function eichrechtVerdict(findings) {
    const distinct = (severity) =>
      new Set(findings.filter((f) => (f.severity === "error") === (severity === "error")).map((f) => f.message)).size;
    const violations = distinct("error");
    const notes = distinct("warning");
    if (violations) return ["error", "Not compliant", `${plural(violations, "violation")}, ${plural(notes, "note")}`];
    return ["ok", "Compliant", notes ? plural(notes, "note") : "No notes"];
  }

  function specVerdict(deviations) {
    if (!deviations.length) return ["ok", "Conforms", "No deviations"];
    return ["info", "Deviates", plural(deviations.length, "deviation")];
  }

  function verdictCell(label, [tone, value, detail]) {
    return h(
      "div",
      { className: "verdict" },
      h("span", { className: "label" }, label),
      h("span", { className: `verdict-value ${tone}` }, h("span", { "aria-hidden": "true" }, ICONS[tone]), value),
      detail ? h("span", { className: "verdict-detail" }, detail) : null,
    );
  }

  function section(title, lede, ...content) {
    return h("section", { className: "block" }, h("h3", {}, title), h("p", { className: "lede" }, lede), content);
  }

  function findingList(items) {
    // Reading-level checks repeat the same finding for every reading; show it once
    const grouped = new Map();
    for (const item of items) {
      const key = `${item.tag}|${item.message}`;
      const entry = grouped.get(key);
      if (entry) entry.count += 1;
      else grouped.set(key, { ...item, count: 1 });
    }
    return h(
      "ul",
      { className: "findings" },
      [...grouped.values()].map(({ tone, tag, message, code, count }) =>
        h(
          "li",
          { title: code || null },
          h("span", { className: `tag ${tone}` }, tag),
          h("span", {}, count > 1 ? `${message} (${count} readings)` : message),
        ),
      ),
    );
  }

  function eichrechtFindings(report) {
    const { records, transaction } = report;
    if (transaction) return transaction.issues;
    if (records.length === 1) return records[0].issues;
    return records.flatMap((record, index) =>
      record.issues.map((issue) => ({ ...issue, message: `Record ${index + 1}: ${issue.message}` })),
    );
  }

  function readingsTable(readings) {
    return h(
      "div",
      { className: "table-wrap" },
      h(
        "table",
        {},
        h("thead", {}, h("tr", {}, h("th", {}, "TX"), h("th", {}, "Time"), h("th", { className: "number" }, "Value"), h("th", {}, "Register"), h("th", {}, "ST"))),
        h(
          "tbody",
          {},
          readings.map((r) =>
            h(
              "tr",
              {},
              h("td", { title: READING_REASONS[r.tx] || null }, r.tx ?? "–"),
              h("td", {}, r.time),
              h("td", { className: "number" }, r.value === null ? "–" : `${r.value} ${r.unit ?? ""}`),
              h("td", {}, r.register ?? "–"),
              h("td", {}, r.status ?? "–"),
            ),
          ),
        ),
      ),
    );
  }

  function recordSummary(record) {
    return [record.gateway, record.pagination, energyText(record.energy)].filter(Boolean).join(" · ");
  }

  function recordsSection(records) {
    if (records.length === 1) {
      return h(
        "section",
        { className: "block" },
        h("h3", {}, "Record"),
        h("p", { className: "lede" }, recordSummary(records[0])),
        readingsTable(records[0].readings),
      );
    }
    return h(
      "section",
      { className: "block" },
      h("h3", {}, `Records (${records.length})`),
      records.map((record, index) => {
        const reasons = [...new Set(record.readings.map((r) => READING_REASONS[r.tx]).filter(Boolean))].join(", ");
        return h(
          "details",
          { className: "record" },
          h("summary", {}, `Record ${index + 1}`, h("span", {}, ` · ${[record.pagination, reasons, `signature ${record.signature.status}`].filter(Boolean).join(" · ")}`)),
          h("p", { className: "lede" }, recordSummary(record)),
          readingsTable(record.readings),
        );
      }),
    );
  }

  function renderReport(report) {
    ui.result.replaceChildren();

    if (!report.ok) {
      const deviation = /^(Payload|Signature) deviates from the OCMF spec: (.*)$/s.exec(report.error);
      if (deviation) {
        ui.result.append(
          h(
            "div",
            { className: "verdicts" },
            verdictCell("Signature", ["muted", "Not checked", null]),
            verdictCell("Eichrecht", ["muted", "Not checked", null]),
            verdictCell("OCMF Spec", ["error", "Rejected", "Strict mode"]),
          ),
          section(
            "OCMF Spec",
            "Strict mode rejects records that deviate from the specification. Turn it off to check the record anyway.",
            findingList([{ tone: "error", tag: "Rejected", message: deviation[2] }]),
          ),
        );
        return;
      }
      ui.result.append(
        h("div", { className: "notice" }, h("p", {}, h("strong", {}, "The record could not be read")), h("code", {}, report.error)),
      );
      return;
    }

    const findings = eichrechtFindings(report);
    const deviations = report.specDeviations;
    const transaction = report.transaction;

    ui.result.append(
      h(
        "div",
        { className: "verdicts" },
        verdictCell("Signature", signatureVerdict(report.records)),
        verdictCell("Eichrecht", eichrechtVerdict(findings)),
        verdictCell("OCMF Spec", specVerdict(deviations)),
      ),
    );

    ui.result.append(
      section(
        "Eichrecht",
        transaction
          ? `Billing rules for the transaction ${transaction.pagination[0]} → ${transaction.pagination[1]}${transaction.energy ? ` (${energyText(transaction.energy)})` : ""}, as the Transparenzsoftware applies them.`
          : "Billing rules under German calibration law, as the Transparenzsoftware applies them.",
        findings.length
          ? findingList(
              findings.map((f) => ({
                tone: f.severity === "error" ? "error" : "warn",
                tag: f.severity === "error" ? "Violation" : "Note",
                message: f.message,
                code: f.code,
              })),
            )
          : h("p", { className: "none" }, "No violations or notes."),
      ),
      section(
        "OCMF Spec",
        "Format conformance. Deviations are accepted, as by the Transparenzsoftware, unless strict mode is on.",
        deviations.length
          ? findingList(deviations.map((message) => ({ tone: "info", tag: "Deviation", message })))
          : h("p", { className: "none" }, "Follows the specification."),
      ),
      recordsSection(report.records),
    );
  }

  /* ---------- Wiring ---------- */

  ui.modeText.addEventListener("click", () => setMode("text"));
  ui.modeXml.addEventListener("click", () => setMode("xml"));
  ui.ocmfInput.addEventListener("input", updateCheckButton);
  ui.xmlInput.addEventListener("change", () => ui.xmlInput.files[0] && loadXmlFile(ui.xmlInput.files[0]));
  ui.exampleSelect.addEventListener("change", () => applyExample(ui.exampleSelect.value));
  ui.checkButton.addEventListener("click", runCheck);
  ui.strictInput.addEventListener("change", () => {
    if (ui.result.querySelector(".verdicts, .notice")) runCheck();
  });

  for (const type of ["dragenter", "dragover"]) {
    ui.dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      ui.dropzone.classList.add("dragging");
    });
  }
  for (const type of ["dragleave", "drop"]) {
    ui.dropzone.addEventListener(type, () => ui.dropzone.classList.remove("dragging"));
  }
  ui.dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) loadXmlFile(file);
  });

  loadExamples();
  startRuntime((message) => {
    ui.status.textContent = message;
  })
    .then((runtime) => {
      state.runtime = runtime;
      const { python, pyocmf, commit } = runtime.info;
      ui.status.textContent = `Python ${python} · pyocmf ${pyocmf}${commit ? ` · main@${commit}` : ""}`;
      updateCheckButton();
      if (state.pendingCheck) runCheck();
    })
    .catch((error) => {
      ui.status.textContent = "Python failed to start";
      ui.checkButton.textContent = "Unavailable";
      ui.result.replaceChildren(
        h("div", { className: "notice" }, h("p", {}, h("strong", {}, "Python could not be started")), h("code", {}, String(error))),
      );
    });
})();
