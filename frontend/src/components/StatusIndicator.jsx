import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, AlertCircle, RefreshCw, Server } from 'lucide-react';
import { fetchSystemInfo } from '../services/api';

export function StatusIndicator() {
  const [status, setStatus] = useState('checking');
  const [details, setDetails] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const checkConnection = async () => {
    setStatus('checking');
    try {
      const data = await fetchSystemInfo();
      setStatus('connected');
      setDetails(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      setStatus('disconnected');
      setDetails(null);
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  return (
    <div className="bg-white border border-[#E2DDD3] rounded-2xl p-4 shadow-xs">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center">
            {status === 'connected' && (
              <>
                <span className="absolute w-3 h-3 bg-emerald-500 rounded-full animate-ping opacity-60"></span>
                <CheckCircle2 className="w-5 h-5 text-emerald-600 relative z-10" />
              </>
            )}
            {status === 'disconnected' && (
              <AlertCircle className="w-5 h-5 text-rose-600" />
            )}
            {status === 'checking' && (
              <Activity className="w-5 h-5 text-[#C69A52] animate-pulse" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold tracking-wide text-[#292723]">
                Warkari Platform Services:
              </span>
              <span
                className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                  status === 'connected'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : status === 'disconnected'
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {status === 'connected' && 'Online & Connected'}
                {status === 'disconnected' && 'Disconnected'}
                {status === 'checking' && 'Verifying...'}
              </span>
            </div>
            {details && (
              <p className="text-[11px] text-[#7A6858] mt-0.5">
                {details.project || 'Warkari'} v{details.version || '1.0.0'} • DB: {details.services?.database || 'healthy'} • STT: {details.services?.gnani_stt_service || 'active'} • TTS: {details.services?.gnani_tts_service || 'active'}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={checkConnection}
          disabled={status === 'checking'}
          className="p-2 text-[#7A6858] hover:text-[#292723] hover:bg-[#F0EDE5] rounded-lg transition-colors"
          title="Refresh service status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${status === 'checking' ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
