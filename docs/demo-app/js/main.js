/**
 * Main Application Entry Point
 * Initializes Pyodide, loads PyOCMF, and sets up the UI
 */

(async function () {
  "use strict";

  let pyodideLoader;
  let ocmfBridge;

  /**
   * Initialize the application
   */
  async function initializeApp() {
    try {
      // Create loader with progress callback
      pyodideLoader = new PyodideLoader((progress) => {
        updateProgress(progress.stage, progress.percent, progress.message);
      });

      // Initialize Pyodide and load packages
      const pyodide = await pyodideLoader.initialize();

      // Create bridge
      ocmfBridge = new OCMFBridge(pyodide);
      await ocmfBridge.initialize();

      // Create UI controller
      uiController = new UIController(ocmfBridge);
      uiController.initializeEventListeners();
      setupMethodTabs();

      // Show input section
      showSection("inputSection");

      console.log("PyOCMF browser demo ready!");
    } catch (error) {
      console.error("Initialization error:", error);
      showError(`Failed to initialize: ${error.message}`);
    }
  }

  /**
   * Update progress display
   */
  function updateProgress(stage, percent, message) {
    const progressBar = document.getElementById("loadingProgress");
    const progressText = document.getElementById("loadingText");

    if (progressBar) {
      progressBar.style.width = `${percent}%`;
      progressBar.setAttribute("aria-valuenow", percent);
    }

    if (progressText) {
      progressText.textContent = message;
    }
  }

  /**
   * Show specific section
   */
  function showSection(sectionId) {
    document.querySelectorAll(".content-section").forEach((section) => {
      section.classList.add("hidden");
    });

    const section = document.getElementById(sectionId);
    if (section) {
      section.classList.remove("hidden");
    }
  }

  /**
   * Show error
   */
  function showError(message) {
    showSection("errorSection");
    const errorMessage = document.getElementById("errorMessage");
    if (errorMessage) {
      errorMessage.textContent = message;
    }
  }

  /**
   * Setup input method tabs
   */
  function setupMethodTabs() {
    const tabs = document.querySelectorAll(".method-tab");
    const methods = {
      text: document.getElementById("textInputMethod"),
      file: document.getElementById("fileInputMethod"),
    };

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const method = tab.getAttribute("data-method");

        // Update active tab
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        // Show corresponding method
        Object.entries(methods).forEach(([key, element]) => {
          if (element) {
            if (key === method) {
              element.classList.remove("hidden");
            } else {
              element.classList.add("hidden");
            }
          }
        });
      });
    });
  }

  // Start initialization when page loads
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeApp);
  } else {
    initializeApp();
  }
})();
