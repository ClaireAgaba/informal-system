/**
 * Signotec WebSocket Pad Server service wrapper.
 * Connects to STPadServer via WSS and provides a simple async API
 * for signature capture from hardware Signotec pads.
 *
 * Flow: connect() → startSignature() → (live points via onPoint callback) → user confirms on pad → returns base64 PNG
 */
import { STPadServerLibCommons, STPadServerLibDefault } from './STPadServerLib';

const WS_URI = 'wss://local.signotecwebsocket.de:49494';

let connected = false;
let padOpened = false;
let padIndex = 0;
let scaleFactorX = 1.0;
let scaleFactorY = 1.0;
let sampleRate = 100;

// Callbacks set by the consumer
let _onPoint = null;
let _onConfirm = null;
let _onCancel = null;
let _onError = null;
let _onDisconnect = null;

/**
 * Connect to the STPadServer WebSocket
 */
export function connect() {
  return new Promise((resolve, reject) => {
    if (connected) {
      resolve();
      return;
    }

    STPadServerLibCommons.handleLogging = (msg) => {
      console.log('[Signotec]', msg);
    };

    STPadServerLibCommons.handleDisconnect = (index) => {
      padOpened = false;
      if (_onDisconnect) _onDisconnect(index);
    };

    STPadServerLibCommons.handleNextSignaturePoint = (x, y, p) => {
      if (_onPoint) {
        _onPoint(x * scaleFactorX, y * scaleFactorY, p);
      }
    };

    STPadServerLibDefault.handleRetrySignature = () => {
      retrySignature();
    };

    STPadServerLibDefault.handleConfirmSignature = () => {
      confirmSignature();
    };

    STPadServerLibDefault.handleCancelSignature = () => {
      cancelSignature();
    };

    STPadServerLibDefault.handleError = (ctx, code, desc) => {
      console.error('[Signotec Error]', ctx, code, desc);
      if (_onError) _onError(ctx, code, desc);
    };

    STPadServerLibCommons.createConnection(
      WS_URI,
      () => {
        connected = true;
        resolve();
      },
      () => {
        connected = false;
        padOpened = false;
      },
      (evt) => {
        connected = false;
        reject(new Error('Failed to connect to Signotec pad server'));
      }
    );
  });
}

/**
 * Disconnect from the WebSocket server
 */
export function disconnect() {
  if (connected) {
    STPadServerLibCommons.destroyConnection();
    connected = false;
    padOpened = false;
  }
}

/**
 * Search for connected USB pads and open the first one
 * @returns {Promise<{type: string, serial: string, firmware: string, displayWidth: number, displayHeight: number}>}
 */
export async function openPad() {
  if (!connected) throw new Error('Not connected to Signotec server');

  // Search for HID (USB) pads
  const searchParams = new STPadServerLibDefault.Params.searchForPads();
  searchParams.setPadSubset('HID');
  const pads = await STPadServerLibDefault.searchForPads(searchParams);

  if (!pads.foundPads || pads.foundPads.length === 0) {
    throw new Error('No Signotec pads found. Please connect a pad via USB.');
  }

  const pad = pads.foundPads[padIndex];

  // Open the pad
  const openParams = new STPadServerLibDefault.Params.openPad(padIndex);
  const padInfo = await STPadServerLibDefault.openPad(openParams);
  padOpened = true;

  const info = padInfo.padInfo;
  scaleFactorX = info.displayWidth / info.xResolution;
  scaleFactorY = info.displayHeight / info.yResolution;
  sampleRate = info.samplingRate;

  return {
    type: pad.type,
    serial: pad.serialNumber,
    firmware: pad.firmwareVersion,
    displayWidth: info.displayWidth,
    displayHeight: info.displayHeight,
  };
}

/**
 * Close the pad
 */
export async function closePad() {
  if (padOpened) {
    try {
      const closeParams = new STPadServerLibDefault.Params.closePad(padIndex);
      await STPadServerLibDefault.closePad(closeParams);
    } catch (e) {
      console.warn('[Signotec] Error closing pad:', e);
    }
    padOpened = false;
  }
}

/**
 * Start signature capture on the hardware pad.
 * The pad will display "Please sign" and wait for the user to sign.
 *
 * @param {Object} opts
 * @param {Function} opts.onPoint - (x, y, pressure) called for each signature point (for live preview)
 * @param {string} [opts.customText='Please sign'] - text shown on pad
 * @param {string} [opts.fieldName='Signature'] - field name for the signature
 * @returns {Promise<string>} - resolves with base64 PNG data URL when user confirms
 */
export function startSignature({ onPoint, customText = 'Please sign', fieldName = 'Signature' } = {}) {
  return new Promise(async (resolve, reject) => {
    if (!padOpened) {
      reject(new Error('Pad not opened'));
      return;
    }

    _onPoint = onPoint || null;

    _onConfirm = resolve;
    _onCancel = () => reject(new Error('Signature cancelled'));
    _onError = (ctx, code, desc) => reject(new Error(`Signotec error: ${desc}`));

    try {
      const params = new STPadServerLibDefault.Params.startSignature();
      params.setFieldName(fieldName);
      params.setCustomText(customText);
      await STPadServerLibDefault.startSignature(params);
    } catch (error) {
      await closePad();
      reject(error);
    }
  });
}

/**
 * Called internally when user confirms on pad. Gets signature data and resolves the promise.
 */
async function confirmSignature() {
  try {
    const signature = await STPadServerLibDefault.confirmSignature();

    // Check minimum points
    if ((signature.countedPoints / sampleRate) <= 0.2) {
      // Too short, retry
      await STPadServerLibDefault.retrySignature();
      return;
    }

    // Get signature data (signData contains the biometric data)
    const getDataParams = new STPadServerLibDefault.Params.getSignatureData();
    const signatureData = await STPadServerLibDefault.getSignatureData(getDataParams);

    await closePad();

    // Resolve with the sign data (base64)
    if (_onConfirm) {
      _onConfirm(signatureData.signData || '');
    }
  } catch (error) {
    await closePad();
    if (_onError) _onError('confirm', -1, error.message);
  }
}

/**
 * Called internally when user cancels on pad
 */
async function cancelSignature() {
  try {
    await STPadServerLibDefault.cancelSignature();
    await closePad();
    if (_onCancel) _onCancel();
  } catch (error) {
    await closePad();
    if (_onCancel) _onCancel();
  }
}

/**
 * Called internally when user retries on pad
 */
async function retrySignature() {
  try {
    await STPadServerLibDefault.retrySignature();
  } catch (error) {
    await closePad();
    if (_onError) _onError('retry', -1, error.message);
  }
}

/**
 * Check if connected to the pad server
 */
export function isConnected() {
  return connected;
}

/**
 * Check if a pad is currently open
 */
export function isPadOpen() {
  return padOpened;
}

export default {
  connect,
  disconnect,
  openPad,
  closePad,
  startSignature,
  isConnected,
  isPadOpen,
};
