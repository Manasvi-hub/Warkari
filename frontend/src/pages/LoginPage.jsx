import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, Phone, User, AlertCircle, Loader2, Sparkles, Shield, HeartHandshake } from 'lucide-react';
import { registerUser } from '../services/api';

export function LoginPage() {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [requestedRole, setRequestedRole] = useState('pilgrim');
  const [sector, setSector] = useState('');
  const [skills, setSkills] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegisterMode) {
        await registerUser({
          name,
          phone,
          password,
          requested_role: requestedRole,
          sector: requestedRole === 'volunteer' ? sector : null,
          skills: requestedRole === 'volunteer' ? skills : null,
        });
        const user = await login(phone, password);
        redirectByRole(user.role);
      } else {
        const user = await login(phone, password);
        const from = location.state?.from?.pathname;
        if (from) {
          navigate(from, { replace: true });
        } else {
          redirectByRole(user.role);
        }
      }
    } catch (err) {
      setError(err.message || 'Operation failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const redirectByRole = (role) => {
    if (role === 'coordinator' || role === 'admin') {
      navigate('/coordinator');
    } else if (role === 'volunteer') {
      navigate('/volunteer');
    } else {
      navigate('/assistant');
    }
  };

  return (
    <div className="max-w-md mx-auto px-3.5 sm:px-6 py-6 sm:py-14 space-y-5 sm:space-y-6">
      <div className="text-center space-y-1.5 sm:space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/40 text-[#A83E16] text-[11px] sm:text-xs font-semibold">
          <HeartHandshake className="w-3.5 h-3.5 text-[#C65319]" />
          <span>वारकरी सेवा व्यासपीठ / Warkari Seva Portal</span>
        </div>
        <h1 className="text-xl sm:text-3xl font-display font-bold text-[#292723]">
          {isRegisterMode ? 'नवीन खाते नोंदणी' : 'प्रवेश करा (Login)'}
        </h1>
        <p className="text-xs sm:text-sm text-[#7A6858]">
          {isRegisterMode
            ? 'वारकरी किंवा स्वयंसेवक म्हणून सहभागी व्हा.'
            : 'आपल्या खात्यात प्रवेश करून सेवा व समन्वय सुरू करा.'}
        </p>
      </div>

      <div className="bg-white border border-[#E2DDD3] rounded-2xl sm:rounded-3xl p-5 sm:p-8 shadow-xs space-y-4 sm:space-y-5">
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegisterMode && (
            <div>
              <label className="block text-xs font-semibold text-[#292723] mb-1.5 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-[#C65319]" />
                <span>पूर्ण नाव (Full Name):</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="उदा. विठ्ठल पाटील"
                required
                className="w-full px-3.5 py-2.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs focus:outline-hidden focus:border-[#C65319] focus:ring-1 focus:ring-[#C65319]"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#292723] mb-1.5 flex items-center gap-1.5">
              <Phone className="w-3.5 h-3.5 text-[#C65319]" />
              <span>मोबाईल क्रमांक (Phone Number):</span>
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+9198XXXXXXXX"
              required
              className="w-full px-3.5 py-2.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs focus:outline-hidden focus:border-[#C65319] focus:ring-1 focus:ring-[#C65319]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#292723] mb-1.5 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-[#C65319]" />
              <span>पासवर्ड (Password):</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="किमान ८ अक्षरे"
              required
              className="w-full px-3.5 py-2.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs focus:outline-hidden focus:border-[#C65319] focus:ring-1 focus:ring-[#C65319]"
            />
          </div>

          {isRegisterMode && (
            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-semibold text-[#292723] mb-1.5">
                  सहभागाचा प्रकार (Role):
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRequestedRole('pilgrim')}
                    className={`p-2.5 rounded-xl text-xs font-semibold border transition-all ${
                      requestedRole === 'pilgrim'
                        ? 'bg-[#FAF8F3] border-[#C65319] text-[#A83E16]'
                        : 'bg-white border-[#E2DDD3] text-[#7A6858]'
                    }`}
                  >
                    वारकरी (Pilgrim)
                  </button>
                  <button
                    type="button"
                    onClick={() => setRequestedRole('volunteer')}
                    className={`p-2.5 rounded-xl text-xs font-semibold border transition-all ${
                      requestedRole === 'volunteer'
                        ? 'bg-[#FAF8F3] border-[#C65319] text-[#A83E16]'
                        : 'bg-white border-[#E2DDD3] text-[#7A6858]'
                    }`}
                  >
                    स्वयंसेवक (Volunteer Sevak)
                  </button>
                </div>
              </div>

              {requestedRole === 'volunteer' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-[#292723] mb-1">
                      कार्यक्षेत्र / सेक्टर (Assigned Sector):
                    </label>
                    <input
                      type="text"
                      value={sector}
                      onChange={(e) => setSector(e.target.value)}
                      placeholder="उदा. वाखारी, पंढरपूर प्रवेशद्वार"
                      className="w-full px-3.5 py-2.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs focus:outline-hidden focus:border-[#C65319]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#292723] mb-1">
                      कौशल्ये (Skills / Seva Specialization):
                    </label>
                    <input
                      type="text"
                      value={skills}
                      onChange={(e) => setSkills(e.target.value)}
                      placeholder="उदा. प्रथमोपचार, गर्दी नियंत्रण, रुग्णवाहिका"
                      className="w-full px-3.5 py-2.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-[#292723] placeholder-[#A09385] text-xs focus:outline-hidden focus:border-[#C65319]"
                    />
                  </div>
                </>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center justify-center gap-2 mt-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>प्रक्रिया सुरू आहे...</span>
              </>
            ) : (
              <span>{isRegisterMode ? 'नोंदणी पूर्ण करा (Register)' : 'प्रवेश करा (Login)'}</span>
            )}
          </button>
        </form>

        <div className="pt-3 border-t border-[#E2DDD3] text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegisterMode(!isRegisterMode);
              setError(null);
            }}
            className="text-xs text-[#594333] hover:text-[#C65319] font-semibold"
          >
            {isRegisterMode
              ? 'आधीपासून खाते आहे का? येथे प्रवेश करा (Sign In)'
              : 'नवीन आहात का? येथे विनामूल्य नोंदणी करा (Register)'}
          </button>
        </div>
      </div>
    </div>
  );
}
