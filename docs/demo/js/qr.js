/**
 * QR code decoding from images and the camera.
 *
 * Uses the browser's BarcodeDetector where it supports QR codes and falls back to
 * jsQR, which is only loaded when first needed.
 */

const JSQR_URL = "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js";
// Phone photos are large; QR codes still decode reliably at this size and much faster
const MAX_DECODE_SIZE = 1280;

let jsQrLoader = null;
let nativeDetector;

function loadJsQr() {
  if (!jsQrLoader) {
    jsQrLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = JSQR_URL;
      script.onload = () => resolve(window.jsQR);
      script.onerror = () => reject(new Error("The QR code decoder could not be loaded."));
      document.head.append(script);
    });
  }
  return jsQrLoader;
}

async function getNativeDetector() {
  if (nativeDetector !== undefined) return nativeDetector;
  nativeDetector = null;
  if ("BarcodeDetector" in window) {
    try {
      const formats = await window.BarcodeDetector.getSupportedFormats();
      if (formats.includes("qr_code")) nativeDetector = new window.BarcodeDetector({ formats: ["qr_code"] });
    } catch {
      nativeDetector = null;
    }
  }
  return nativeDetector;
}

async function decodeQr(source, width, height) {
  const detector = await getNativeDetector();
  if (detector) {
    const codes = await detector.detect(source);
    return codes.length ? codes[0].rawValue : null;
  }
  const jsQR = await loadJsQr();
  const scale = Math.min(1, MAX_DECODE_SIZE / Math.max(width, height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(source, 0, 0, canvas.width, canvas.height);
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
  const code = jsQR(pixels.data, canvas.width, canvas.height, { inversionAttempts: "attemptBoth" });
  return code ? code.data : null;
}

async function decodeQrImage(blob) {
  const bitmap = await createImageBitmap(blob);
  try {
    return await decodeQr(bitmap, bitmap.width, bitmap.height);
  } finally {
    bitmap.close();
  }
}

function cameraAvailable() {
  return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

/** Scan the camera until a QR code is found; returns a function that stops scanning. */
async function startQrCameraScan(video, onCode) {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "environment" },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();

  let stopped = false;
  const stop = () => {
    stopped = true;
    for (const track of stream.getTracks()) track.stop();
    video.srcObject = null;
  };

  const scan = async () => {
    if (stopped) return;
    // The docs' instant navigation removes the page without unloading it
    if (!video.isConnected) {
      stop();
      return;
    }
    if (video.videoWidth) {
      const text = await decodeQr(video, video.videoWidth, video.videoHeight).catch(() => null);
      if (text && !stopped) {
        stop();
        onCode(text);
        return;
      }
    }
    setTimeout(scan, 200);
  };
  scan();
  return stop;
}

// DER encoding of the id-ecPublicKey OID (1.2.840.10045.2.1), present in every EC public key
const EC_PUBLIC_KEY_OID = "2a8648ce3d0201";

function hexToText(hex) {
  const bytes = new Uint8Array(hex.match(/../g).map((pair) => parseInt(pair, 16)));
  return new TextDecoder().decode(bytes);
}

function base64ToHex(base64) {
  try {
    return Array.from(atob(base64), (c) => c.charCodeAt(0).toString(16).padStart(2, "0")).join("");
  } catch {
    return null;
  }
}

/**
 * Classify decoded QR text: an OCMF record (plain or hex, possibly with an appended
 * key), XML, a bare public key, a link, or something else.
 */
function classifyQrText(raw) {
  const text = raw.trim();
  if (/^https?:\/\//i.test(text)) return { kind: "url", value: text };
  if (text.startsWith("<")) return { kind: "xml", value: text };

  const compact = text.replace(/-----(BEGIN|END) PUBLIC KEY-----/g, "").replace(/\s+/g, "");
  let ocmf = text.startsWith("OCMF|") ? text : null;
  if (!ocmf && /^([0-9a-f]{2})+$/i.test(compact) && compact.toLowerCase().startsWith("4f434d467c")) {
    ocmf = hexToText(compact);
  }
  if (ocmf) {
    // A fourth section is the public key, as appended for the Transparenzsoftware
    return { kind: "ocmf", value: text, hasKey: ocmf.split("|").length > 3 };
  }

  const hex = /^([0-9a-f]{2})+$/i.test(compact) ? compact : /^[A-Za-z0-9+/]+={0,2}$/.test(compact) ? base64ToHex(compact) : null;
  if (hex && hex.toLowerCase().includes(EC_PUBLIC_KEY_OID)) return { kind: "key", value: compact };
  return { kind: "other", value: text };
}
