/**
 * Pyodide Loader - Initializes Python runtime in the browser
 * Handles downloading, caching, and dependency installation
 */

class PyodideLoader {
  constructor(progressCallback = null) {
    this.pyodide = null;
    this.progressCallback = progressCallback;
    this.isReady = false;
  }

  updateProgress(stage, percent, message) {
    if (this.progressCallback) {
      this.progressCallback({ stage, percent, message });
    }
  }

  async initialize() {
    try {
      // Stage 1: Load Pyodide runtime
      this.updateProgress("loading", 0, "Loading Pyodide runtime...");

      this.pyodide = await loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/",
      });

      this.updateProgress("loading", 30, "Pyodide loaded");

      // Stage 2: Install core dependencies
      this.updateProgress("dependencies", 35, "Installing pydantic...");
      await this.pyodide.loadPackage("pydantic");

      this.updateProgress("dependencies", 50, "Installing cryptography...");
      await this.pyodide.loadPackage("cryptography");

      // Stage 3: Load micropip (required before we can use it)
      this.updateProgress("dependencies", 60, "Loading micropip...");
      await this.pyodide.loadPackage("micropip");

      // Stage 4: Install additional packages via micropip
      this.updateProgress(
        "dependencies",
        65,
        "Installing additional packages...",
      );

      await this.pyodide.runPythonAsync(`
                import micropip
                await micropip.install([
                    'phonenumbers',
                    'pydantic-extra-types'
                ])
            `);

      this.updateProgress("dependencies", 80, "Dependencies installed");

      // Stage 5: Install pyocmf from PyPI
      this.updateProgress("pyocmf", 85, "Installing pyocmf...");

      await this.pyodide.runPythonAsync(`
        await micropip.install('pyocmf')
      `);

      this.updateProgress("pyocmf", 95, "pyocmf installed successfully");

      this.updateProgress("complete", 100, "Ready!");
      this.isReady = true;

      return this.pyodide;
    } catch (error) {
      this.updateProgress("error", 0, `Error: ${error.message}`);
      throw error;
    }
  }

  async loadLocalPyOCMF(sourceFiles) {
    /**
     * Load pyocmf from local source files if PyPI installation failed
     * @param {Object} sourceFiles - Map of file paths to content
     */
    if (!this.pyodide) {
      throw new Error("Pyodide not initialized");
    }

    for (const [path, content] of Object.entries(sourceFiles)) {
      await this.pyodide.FS.writeFile(path, content);
    }
  }

  getPyodide() {
    if (!this.isReady) {
      throw new Error("Pyodide not ready. Call initialize() first.");
    }
    return this.pyodide;
  }
}
