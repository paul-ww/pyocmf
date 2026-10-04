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
