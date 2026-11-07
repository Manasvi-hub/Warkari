import React, { useState } from 'react';
import { trackIncidentByToken } from '../services/api';
import { Search, ShieldAlert, CheckCircle2, Clock, AlertCircle, Loader2, KeyRound } from 'lucide-react';

export function TrackIncidentPage() {
  const [token, setToken] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTrackSubmit = async (e) => {
    e.preventDefault();
    const cleanToken = token.trim();
    if (!cleanToken) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await trackIncidentByToken(cleanToken);
      setResult(data);
    } catch (err) {
      setError(err.message || 'No incident found matching this private tracking token.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto px-3.5 sm:px-6 py-6 sm:py-12 space-y-5 sm:space-y-6">
      <div className="text-center space-y-1.5 sm:space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/40 text-[#A83E16] text-[11px] sm:text-xs font-semibold">
          <ShieldAlert className="w-3.5 h-3.5 text-[#C65319]" />
          <span>सुरक्षित मदत तिकीट ट्रॅकिंग / Secure Request Tracking</span>
        </div>
        <h1 className="text-xl sm:text-3xl font-display font-bold text-[#292723]">आपल्या विनंतीची सद्यस्थिती</h1>
        <p className="text-xs sm:text-sm text-[#7A6858]">
          मदत विनंती नोंदवताना मिळालेला खाजगी ट्रॅकिंग टोकन येथे प्रविष्ट करा.
        </p>
      </div>

      <div className="bg-white border border-[#E2DDD3] rounded-2xl sm:rounded-3xl p-5 sm:p-8 shadow-xs space-y-4 sm:space-y-5">
        <form onSubmit={handleTrackSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#292723] mb-1.5 flex items-center gap-1.5">
              <KeyRound className="w-3.5 h-3.5 text-[#C65319]" />
              <span>खाजगी ट्रॅकिंग टोकन (Private Tracking Token):</span>
            </label>
            <input
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="e.g. 64-character token from assistant"
              required
              className="w-full px-4 py-3 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs font-mono focus:outline-hidden focus:border-[#C65319] focus:ring-1 focus:ring-[#C65319] transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !token.trim()}
            className="w-full py-3 px-4 bg-[#C65319] hover:bg-[#A83E16] disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>तपासत आहे (Checking status)...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>सद्यस्थिती तपासा (Track Status)</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="pt-4 border-t border-[#E2DDD3] space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#7A6858]">संदर्भ क्रमांक (Reference):</span>
              <span className="text-xs font-bold font-mono text-[#292723] bg-[#F0EDE5] px-2 py-0.5 rounded border border-[#E2DDD3]">
                {result.public_reference}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-[#7A6858]">सद्यस्थिती (Current Status):</span>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                  result.status === 'RESOLVED'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : result.status === 'EN_ROUTE' || result.status === 'ON_SCENE'
                    ? 'bg-amber-50 text-amber-800 border border-amber-200'
                    : 'bg-orange-50 text-[#C65319] border border-orange-200'
                }`}
              >
                {result.status}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-[#FAF8F3] border border-[#E2DDD3] space-y-1.5">
              <p className="text-xs font-semibold text-[#A83E16]">संदेश (Status Update):</p>
              <p className="text-xs text-[#292723] font-marathi leading-relaxed">
                {result.status_message}
              </p>
            </div>

            <p className="text-[11px] text-[#A09385] text-center">
              नोंदणी वेळ: {result.created_at ? new Date(result.created_at).toLocaleString() : 'N/A'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
