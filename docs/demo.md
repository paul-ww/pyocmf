# Browser Demo

Try PyOCMF in your browser. The demo lets you parse, validate, verify, and check regulatory compliance for OCMF data without installing anything.

[Launch Demo →](demo/)

## Features

- Parse OCMF data from plain text, hex-encoded, or XML files
- Validate structure using Pydantic
- Verify ECDSA cryptographic signatures
- Check German Eichrecht (calibration law) compliance
- Runs entirely in your browser, no data sent to servers
- Uses Pyodide (Python compiled to WebAssembly)

## What You Can Do

### Parse and Validate

- Paste OCMF strings in plain text or hex-encoded format
- Upload XML files (e.g., from Transparenzsoftware)
- View parsed structure with all payload fields and readings
- Get instant validation feedback

### Verify Signatures

- Provide a public key (hex format) for signature verification
- Public keys are automatically extracted from XML files
- Verify data authenticity and integrity
- See which signature algorithm was used

### Check Regulatory Compliance

- Validate against German Eichrecht requirements
- Check meter status, error flags, time synchronization
- Verify transaction consistency (begin/end pairs)
- Identify compliance issues with detailed error messages

## Quick Start

1. Visit the [demo page](demo/)
2. Paste an OCMF string or upload an XML file
3. Optionally provide a public key for signature verification
4. Click "Parse & Validate"

The demo includes example data to help you get started.

## Running the Demo Locally

You can run the Pyodide demo on your local machine using any HTTP server:

### Using Python's Built-in Server

```bash
# Navigate to the demo directory
cd docs/demo

# Python 3
python -m http.server 8000

# Then open: http://localhost:8000
```

### Using Node.js http-server

```bash
# Install http-server globally (one time)
npm install -g http-server

# Navigate to the demo directory
cd docs/demo

# Start server
http-server -p 8000

# Then open: http://localhost:8000
```

### Using uv with poe (Recommended for this Project)

```bash
# From the project root (easiest method)
uv run poe demo

# Then open: http://localhost:8000
```

Or without poe:

```bash
cd docs/demo
uv run python -m http.server 8000

# Then open: http://localhost:8000
```

### Why a Server is Required

The demo loads Python WebAssembly modules from CDN, which requires proper CORS headers. Opening `index.html` directly as a file (file://) won't work due to browser security restrictions. Any local HTTP server will work fine.

### First Load Performance

The first time you load the demo, it downloads Pyodide runtime (~6 MB), Python standard library, and PyOCMF with dependencies. This takes 5-10 seconds. Subsequent loads are cached.
