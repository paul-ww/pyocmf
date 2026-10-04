/**
 * Starts Pyodide, installs pyocmf and loads the demo's Python module.
 *
 * The docs build ships a wheel of the current repository in wheels/ (see the
 * demo-wheel poe task), so the demo runs unreleased code. Without it, pyocmf
 * comes from PyPI.
 *
 * Python starts once per page load; the docs' instant navigation keeps it alive
 * when the demo page is left and visited again.
 */

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js";

let runtimePromise = null;
let lastProgress = "Starting Python…";
let progressListener = () => {};

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = () => reject(new Error(`${src} could not be loaded`));
    document.head.append(script);
  });
}

async function localWheel() {
  try {
    const response = await fetch("wheels/latest.json", { cache: "no-store" });
    if (!response.ok) return null;
    const info = await response.json();
    return {
      url: new URL(`wheels/${info.wheel}`, window.location.href).href,
      commit: info.commit || null,
    };
  } catch {
    return null;
  }
}

async function bootRuntime(onProgress) {
  onProgress("Starting Python…");
  if (typeof loadPyodide === "undefined") await loadScript(PYODIDE_URL);
  const pyodide = await loadPyodide();

  // Pyodide ships compiled builds of these; micropip would fail on them
  onProgress("Loading pydantic and cryptography…");
  await pyodide.loadPackage(["pydantic", "cryptography", "micropip"]);

  onProgress("Installing pyocmf…");
  const wheel = await localWheel();
  const micropip = pyodide.pyimport("micropip");
  await micropip.install(wheel ? wheel.url : "pyocmf");

  const source = await (await fetch("py/demo.py")).text();
  const namespace = pyodide.globals.get("dict")();
  pyodide.runPython(source, { globals: namespace });

  const info = JSON.parse(namespace.get("runtime_info")());
  return {
    info: { ...info, commit: wheel ? wheel.commit : null },
    analyzeText: (text, publicKey, strict) =>
      JSON.parse(namespace.get("analyze_text")(text, publicKey || null, strict)),
    analyzeXml: (content, strict) =>
      JSON.parse(namespace.get("analyze_xml")(content, strict)),
  };
}

function startRuntime(onProgress) {
  progressListener = onProgress;
  onProgress(lastProgress);
  if (!runtimePromise) {
    runtimePromise = bootRuntime((message) => {
      lastProgress = message;
      progressListener(message);
    }).catch((error) => {
      runtimePromise = null;
      lastProgress = "Starting Python…";
      throw error;
    });
  }
  return runtimePromise;
}
