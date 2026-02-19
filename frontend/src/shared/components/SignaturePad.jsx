import { useRef, useEffect, useCallback, useState } from 'react';
import SignaturePadLib from 'signature_pad';
import { RotateCcw, Usb, Pencil, Loader2 } from 'lucide-react';
import signotecService from '../vendor/signotecService';

/**
 * Reusable signature pad component supporting:
 *   1. Canvas drawing (mouse/touch) — default mode
 *   2. Signotec hardware pad via WebSocket — toggled with button
 *
 * Props:
 *  - onChange(base64String | '') — called when signature changes
 *  - value — optional initial base64 string (for re-rendering)
 *  - height — canvas height in px (default: 160)
 *  - penColor — ink color (default: '#000')
 *  - disabled — disables drawing
 *  - error — shows red border
 *  - label — optional label text
 *  - showHardwareToggle — show the Signotec pad button (default: true)
 */
const SignaturePad = ({
  onChange,
  value,
  height = 160,
  penColor = '#000',
  disabled = false,
  error = false,
  label = 'Signature',
  showHardwareToggle = false,
}) => {
  const canvasRef = useRef(null);
  const padRef = useRef(null);
  const containerRef = useRef(null);

  // Hardware pad state
  const [hwMode, setHwMode] = useState(false);
  const [hwStatus, setHwStatus] = useState('idle'); // idle | connecting | waiting | error
  const [hwError, setHwError] = useState('');

  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    const width = container.offsetWidth;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    canvas.getContext('2d').scale(ratio, ratio);

    if (padRef.current && value) {
      padRef.current.fromDataURL(value, { width, height });
    }
  }, [height, value]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const pad = new SignaturePadLib(canvas, {
      penColor,
      backgroundColor: 'rgba(255, 255, 255, 0)',
    });

    // In hardware mode, disable canvas drawing
    if (disabled || hwMode) {
      pad.off();
    }

    pad.addEventListener('endStroke', () => {
      if (onChange) {
        onChange(pad.toDataURL('image/png'));
      }
    });

    padRef.current = pad;
    resizeCanvas();

    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);

    return () => {
      pad.off();
      window.removeEventListener('resize', handleResize);
    };
  }, [penColor, disabled, hwMode]);

  // Load initial value
  useEffect(() => {
    if (padRef.current && value && padRef.current.isEmpty()) {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (canvas && container) {
        padRef.current.fromDataURL(value, {
          width: container.offsetWidth,
          height,
        });
      }
    }
  }, [value, height]);

  const handleClear = () => {
    if (padRef.current && !disabled) {
      padRef.current.clear();
      if (onChange) onChange('');
    }
    setHwStatus('idle');
    setHwError('');
  };

  // Draw a point on the canvas (for live preview from hardware pad)
  const drawHwPoint = useCallback((x, y, pressure) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const ratio = Math.max(window.devicePixelRatio || 1, 1);

    // Scale hardware pad coords to our canvas size
    const container = containerRef.current;
    if (!container) return;
    const cw = container.offsetWidth;
    const ch = height;

    ctx.fillStyle = penColor;
    ctx.strokeStyle = penColor;
    ctx.lineWidth = 2 * ratio;
    ctx.lineCap = 'round';

    // Scale x,y from pad display coords to our canvas
    const sx = (x / canvas.width) * cw * ratio;
    const sy = (y / canvas.height) * ch * ratio;

    if (pressure === 0) {
      ctx.beginPath();
      ctx.arc(sx, sy, 0.5, 0, 2 * Math.PI, true);
      ctx.fill();
      ctx.stroke();
      ctx.moveTo(sx, sy);
    } else {
      ctx.lineTo(sx, sy);
      ctx.stroke();
    }
  }, [height, penColor]);

  // Start hardware signature capture
  const handleStartHardware = async () => {
    setHwError('');
    setHwStatus('connecting');

    try {
      // Connect to STPadServer
      await signotecService.connect();

      // Open the first USB pad
      const padInfo = await signotecService.openPad();
      console.log('[Signotec] Pad opened:', padInfo);

      // Resize canvas to match pad display proportions
      const canvas = canvasRef.current;
      if (canvas) {
        canvas.width = padInfo.displayWidth;
        canvas.height = padInfo.displayHeight;
      }

      setHwStatus('waiting');

      // Clear existing canvas content
      if (padRef.current) padRef.current.clear();

      // Start capture — resolves when user confirms on pad
      const signData = await signotecService.startSignature({
        onPoint: drawHwPoint,
        customText: 'Please sign',
        fieldName: 'Signature',
      });

      // After confirm, convert the canvas content to base64 PNG
      if (canvas) {
        const base64 = canvas.toDataURL('image/png');
        if (onChange) onChange(base64);
      }

      setHwStatus('idle');
    } catch (err) {
      console.error('[Signotec] Error:', err);
      setHwError(err.message || 'Hardware pad error');
      setHwStatus('error');
      try { await signotecService.closePad(); } catch (_) { /* ignore */ }
    }
  };

  // Switch to canvas mode
  const handleSwitchToCanvas = () => {
    setHwMode(false);
    setHwStatus('idle');
    setHwError('');
    handleClear();
    try { signotecService.closePad(); } catch (_) { /* ignore */ }
  };

  // Switch to hardware mode
  const handleSwitchToHardware = () => {
    setHwMode(true);
    setHwStatus('idle');
    setHwError('');
    handleClear();
  };

  return (
    <div>
      {label && (
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium text-gray-700">{label}</label>
          <div className="flex items-center space-x-2">
            {showHardwareToggle && !disabled && (
              <button
                type="button"
                onClick={hwMode ? handleSwitchToCanvas : handleSwitchToHardware}
                className={`flex items-center text-xs px-2 py-0.5 rounded-md border transition-colors ${
                  hwMode
                    ? 'border-orange-300 bg-orange-50 text-orange-600 hover:bg-orange-100'
                    : 'border-gray-300 text-gray-400 hover:text-orange-500 hover:border-orange-300'
                }`}
                title={hwMode ? 'Switch to canvas drawing' : 'Use Signotec hardware pad'}
              >
                {hwMode ? (
                  <><Pencil className="w-3 h-3 mr-1" />Canvas</>
                ) : (
                  <><Usb className="w-3 h-3 mr-1" />Signotec Pad</>
                )}
              </button>
            )}
            {!disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="flex items-center text-xs text-gray-400 hover:text-red-500 transition-colors"
                title="Clear signature"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Clear
              </button>
            )}
          </div>
        </div>
      )}
      <div
        ref={containerRef}
        className={`relative border rounded-lg overflow-hidden ${
          error ? 'border-red-400' : 'border-gray-300'
        } ${disabled ? 'bg-gray-50 opacity-60' : 'bg-white'}`}
      >
        <canvas
          ref={canvasRef}
          className={`w-full ${disabled ? 'cursor-not-allowed' : hwMode ? 'cursor-default' : 'cursor-crosshair'}`}
          style={{ height: `${height}px`, touchAction: 'none' }}
        />

        {/* Canvas mode placeholder */}
        {!hwMode && !value && padRef.current?.isEmpty?.() !== false && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <span className="text-sm text-gray-300 uppercase tracking-wider select-none">
              Sign here
            </span>
          </div>
        )}

        {/* Hardware mode overlay */}
        {hwMode && hwStatus === 'idle' && !value && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <button
              type="button"
              onClick={handleStartHardware}
              className="flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm font-medium shadow-sm transition-colors"
            >
              <Usb className="w-4 h-4 mr-2" />
              Start Signotec Pad
            </button>
            <p className="text-xs text-gray-400 mt-2">Connect pad via USB, then click to capture</p>
          </div>
        )}

        {/* Connecting state */}
        {hwMode && hwStatus === 'connecting' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-80">
            <Loader2 className="w-6 h-6 text-orange-500 animate-spin mb-2" />
            <p className="text-sm text-gray-500">Connecting to Signotec pad...</p>
          </div>
        )}

        {/* Waiting for signature */}
        {hwMode && hwStatus === 'waiting' && (
          <div className="absolute inset-x-0 bottom-0 bg-orange-50 border-t border-orange-200 px-3 py-1.5 flex items-center justify-center">
            <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse mr-2" />
            <span className="text-xs text-orange-600 font-medium">Waiting for signature on pad...</span>
          </div>
        )}

        {/* Error state */}
        {hwMode && hwStatus === 'error' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90">
            <p className="text-sm text-red-500 mb-2">{hwError}</p>
            <button
              type="button"
              onClick={handleStartHardware}
              className="flex items-center px-3 py-1.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-xs font-medium"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SignaturePad;
