/**
 * Starts Pyodide, installs pyocmf and loads the demo's Python module.
 *
 * The docs build ships a wheel of the current repository in wheels/ (see the
 * demo-wheel poe task), so the demo runs unreleased code. Without it, pyocmf
 * comes from PyPI.
 */

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

async function startRuntime(onProgress) {
  onProgress("Starting Python…");
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
