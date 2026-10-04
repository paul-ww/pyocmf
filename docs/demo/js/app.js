/**
 * Browser demo UI: three input steps on the left, the report on the right.
 * Record data is untrusted, so the report is built with textContent only.
 */

(function () {
  "use strict";

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
    keyStep: $("keyStep"),
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
    for (const child of children.flat()) {
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
      mode === "xml"
        ? "XML files carry their own public keys."
        : "Without a key the record is parsed and checked, but its signature is not verified.";
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
    requestCheck();
  }

  function requestCheck() {
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
      renderReport(report, strict);
      updateCheckButton();
    }, 20);
  }

  /* ---------- Report ---------- */

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
    const algorithms = [...new Set(records.map((r) => r.signature.algorithm).filter(Boolean))].join(", ");
    if (count("invalid")) {
      return ["error", "Invalid", `${count("invalid")} of ${plural(records.length, "record")} fail`];
    }
    if (count("error")) {
      return ["error", "Not verified", records.find((r) => r.signature.status === "error").signature.message];
    }
    if (count("valid") === records.length) return ["ok", "Valid", algorithms];
    if (count("valid")) return ["warn", "Partly checked", `${count("valid")} of ${records.length} records have a key`];
    return ["muted", "Not checked", "No public key given"];
  }

  function eichrechtVerdict(issues) {
    const errors = issues.filter((i) => i.severity === "error").length;
    const warnings = issues.length - errors;
    if (errors) return ["error", "Not compliant", `${plural(errors, "error")}, ${plural(warnings, "warning")}`];
    return ["ok", "Compliant", warnings ? plural(warnings, "warning") : "No findings"];
  }

  function specVerdict(deviations) {
    if (!deviations.length) return ["ok", "Conforms", "No deviations"];
    return ["warn", "Deviates", plural(deviations.length, "deviation")];
  }

  const ICONS = { ok: "✓", warn: "!", error: "✗", muted: "–" };

  function verdictCell(label, [tone, value, detail]) {
    return h(
      "div",
      { className: "verdict" },
      h("span", { className: "label" }, label),
      h("span", { className: `verdict-value ${tone}` }, h("span", { "aria-hidden": "true" }, ICONS[tone]), value),
      detail ? h("span", { className: "verdict-detail" }, detail) : null,
    );
  }

  function issueList(issues) {
    if (!issues.length) return h("p", { className: "hint" }, "No findings.");
    return h(
      "ul",
      { className: "issues" },
      issues.map((issue) => {
        const tone = issue.severity === "error" ? "error" : "warn";
        return h(
          "li",
          {},
          h("span", { className: tone, "aria-label": issue.severity }, ICONS[tone]),
          h("code", { className: tone }, issue.code),
          h("span", {}, issue.message),
        );
      }),
    );
  }

  function facts(rows) {
    return h(
      "dl",
      { className: "facts" },
      rows.filter(([, value]) => value).flatMap(([term, value]) => [h("dt", {}, term), h("dd", {}, value)]),
    );
  }

  function readingsTable(readings) {
    const columns = ["TX", "Time", "Sync", "Value", "Unit", "Register", "ST", "EF"];
    return h(
      "div",
      { className: "table-wrap" },
      h(
        "table",
        {},
        h("thead", {}, h("tr", {}, columns.map((c) => h("th", { className: c === "Value" ? "number" : null }, c)))),
        h(
          "tbody",
          {},
          readings.map((r) =>
            h(
              "tr",
              {},
              h("td", { title: READING_REASONS[r.tx] || null }, r.tx ?? "–"),
              h("td", {}, r.time),
              h("td", {}, r.sync ?? "–"),
              h("td", { className: "number" }, r.value ?? "–"),
              h("td", {}, r.unit ?? "–"),
              h("td", {}, r.register ?? "–"),
              h("td", {}, r.status ?? "–"),
              h("td", {}, r.errorFlags ?? ""),
            ),
          ),
        ),
      ),
    );
  }

  const SIGNATURE_TEXT = { valid: "valid", invalid: "invalid", error: "could not be verified", unchecked: "not checked" };

  function recordBody(record) {
    return h(
      "div",
      { className: "record-body" },
      facts([
        ["Gateway", record.gateway],
        ["Meter", record.meter],
        ["Pagination", record.pagination],
        ["Identification", record.identification],
        ["Signature", `${record.signature.algorithm || "unknown algorithm"} · ${SIGNATURE_TEXT[record.signature.status]}`],
        ["Energy", energyText(record.energy)],
      ]),
      h("div", { className: "block" }, h("span", { className: "label" }, "Findings"), issueList(record.issues)),
      readingsTable(record.readings),
    );
  }

  function renderReport(report, strict) {
    ui.result.replaceChildren();

    if (!report.ok) {
      ui.result.append(
        h(
          "div",
          { className: "notice" },
          h("p", {}, h("strong", {}, "The record could not be read")),
          h("code", {}, report.error),
          strict
            ? h("p", { className: "hint" }, "Strict mode is on. Turn it off to read records that deviate from the spec and list the deviations as warnings.")
            : null,
        ),
      );
      return;
    }

    const { records, transaction, series, specDeviations } = report;
    const issues = transaction ? transaction.issues : records.flatMap((r) => r.issues);

    ui.result.append(
      h(
        "div",
        { className: "verdicts" },
        verdictCell("Signature", signatureVerdict(records)),
        verdictCell("Eichrecht", eichrechtVerdict(issues)),
        verdictCell("Spec", specVerdict(specDeviations)),
      ),
    );

    if (transaction) {
      ui.result.append(
        h(
          "section",
          { className: "block" },
          h("h3", {}, `Transaction ${transaction.pagination[0]} → ${transaction.pagination[1]}`),
          facts([["Energy", energyText(transaction.energy)]]),
          issueList(transaction.issues),
        ),
      );
    }

    if (series) {
      const block = h(
        "section",
        { className: "block" },
        h("h3", {}, "Meter reading over time"),
        h("p", { className: "chart-caption" }, `Register ${series.register} in ${series.unit}. Hover or focus the chart for each reading.`),
      );
      ui.result.append(block);
      renderChart(block, series);
    }

    if (specDeviations.length) {
      ui.result.append(
        h(
          "section",
          { className: "block" },
          h("h3", {}, "Spec deviations"),
          h(
            "ul",
            { className: "issues" },
            specDeviations.map((message) =>
              h("li", {}, h("span", { className: "warn", "aria-hidden": "true" }, "!"), h("code", { className: "warn" }, "SPEC"), h("span", {}, message)),
            ),
          ),
        ),
      );
    }

    if (records.length === 1) {
      ui.result.append(h("section", { className: "block" }, h("h3", {}, "Record"), recordBody(records[0])));
      return;
    }
    records.forEach((record, index) => {
      ui.result.append(
        h(
          "details",
          { className: "record", open: records.length <= 2 },
          h("summary", {}, `Record ${index + 1} of ${records.length} `, h("span", {}, record.pagination || "")),
          recordBody(record),
        ),
      );
    });
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
