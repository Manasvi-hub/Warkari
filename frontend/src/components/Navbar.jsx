import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Flame,
  Compass,
  Search,
  User,
  LogOut,
  Mic,
  Users,
  Shield,
  Menu,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu whenever navigation path changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  const handleLogout = async () => {
    await logout();
    setMobileMenuOpen(false);
    navigate('/');
  };

  return (
    <header className="border-b border-[#E8E2D5] bg-[#FAF8F3]/95 backdrop-blur-md sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-18 flex items-center justify-between">
        {/* Brand identity */}
        <Link to="/" className="flex items-center gap-2.5 sm:gap-3.5 group min-w-0">
          <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-[#C65319] text-white flex items-center justify-center shrink-0 shadow-md shadow-[#C65319]/20 group-hover:bg-[#A83E16] transition-all transform group-hover:scale-102">
            <Flame className="w-5 h-5 sm:w-6 sm:h-6 fill-white/20" />
          </div>
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <span className="font-display font-bold text-lg sm:text-xl tracking-wider text-[#292723] truncate">
                WARKARI
              </span>
              <span className="text-[10px] sm:text-xs font-marathi font-bold text-[#A83E16] bg-[#C65319]/10 px-1.5 sm:px-2 py-0.5 rounded border border-[#C65319]/20 shrink-0">
                वारकरी
              </span>
            </div>
            <p className="text-[10px] sm:text-[11px] text-[#7A6858] font-medium tracking-wide hidden md:block">
              Pandharpur Waari Companion
            </p>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-2 lg:gap-3">
          <Link
            to="/assistant"
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#FAF8F3] hover:bg-[#F0EDE5] text-[#292723] border border-[#E2DDD3] transition-all shadow-xs"
          >
            <Mic className="w-3.5 h-3.5 text-[#C65319]" />
            <span>Voice Assistant</span>
          </Link>

          <Link
            to="/facilities"
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg text-[#594333] hover:text-[#292723] hover:bg-[#F0EDE5] transition-colors"
          >
            <Compass className="w-3.5 h-3.5 text-[#C69A52]" />
            <span>Facilities</span>
          </Link>

          <Link
            to="/track"
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg text-[#594333] hover:text-[#292723] hover:bg-[#F0EDE5] transition-colors"
          >
            <Search className="w-3.5 h-3.5 text-[#C65319]" />
            <span>Track Request</span>
          </Link>

          {currentUser ? (
            <div className="flex items-center gap-2 border-l border-[#E2DDD3] pl-3 ml-1">
              {currentUser.role === 'volunteer' && (
                <Link
                  to="/volunteer"
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#FAF8F3] text-[#594333] border border-[#C69A52]/40 hover:bg-[#F0EDE5]"
                >
                  <Users className="w-3.5 h-3.5 text-[#C65319]" />
                  <span>Volunteer Desk</span>
                </Link>
              )}
              {(currentUser.role === 'coordinator' || currentUser.role === 'admin') && (
                <Link
                  to="/coordinator"
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#FAF8F3] text-[#594333] border border-[#C65319]/40 hover:bg-[#F0EDE5]"
                >
                  <Shield className="w-3.5 h-3.5 text-[#C65319]" />
                  <span>Coordinator Desk</span>
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-[#7A6858] hover:text-[#292723] hover:bg-[#F0EDE5] transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                title="Logout"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#C65319] hover:bg-[#A83E16] text-white shadow-sm shadow-[#C65319]/20 transition-all ml-1 min-h-[38px]"
            >
              <User className="w-3.5 h-3.5" />
              <span>Login</span>
            </Link>
          )}
        </nav>

        {/* Mobile Hamburger Button */}
        <div className="flex items-center gap-2 md:hidden">
          <Link
            to="/assistant"
            className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#C65319] text-white shadow-xs"
            title="Voice Assistant"
            aria-label="Voice Assistant"
          >
            <Mic className="w-5 h-5" />
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="w-11 h-11 flex items-center justify-center rounded-xl bg-white border border-[#E2DDD3] text-[#292723] hover:bg-[#F0EDE5] active:scale-95 transition-all shadow-xs"
            aria-label={mobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-5 h-5 text-[#C65319]" /> : <Menu className="w-5 h-5 text-[#292723]" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer / Overlay Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-x-0 top-16 sm:top-18 bottom-0 bg-[#FAF8F3]/98 backdrop-blur-lg z-50 flex flex-col justify-between p-6 overflow-y-auto animate-fade-in border-t border-[#E2DDD3]">
          <div className="space-y-4">
            <div className="text-[11px] font-bold uppercase tracking-wider text-[#7A6858] pb-1 border-b border-[#E2DDD3]">
              मेनू / Navigation
            </div>

            <nav className="flex flex-col space-y-2">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-[#292723] hover:bg-white border border-transparent hover:border-[#E2DDD3] min-h-[48px]"
              >
                <Flame className="w-5 h-5 text-[#C65319]" />
                <span>मुखपृष्ठ (Home)</span>
              </Link>

              <Link
                to="/assistant"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold bg-[#C65319]/10 text-[#C65319] border border-[#C65319]/20 min-h-[48px]"
              >
                <Mic className="w-5 h-5 text-[#C65319]" />
                <span>वारकरी सहाय्यक (Voice Assistant)</span>
              </Link>

              <Link
                to="/facilities"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-[#594333] hover:bg-white border border-transparent hover:border-[#E2DDD3] min-h-[48px]"
              >
                <Compass className="w-5 h-5 text-[#C69A52]" />
                <span>सुविधा केंद्रे (Facilities & Camps)</span>
              </Link>

              <Link
                to="/track"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-[#594333] hover:bg-white border border-transparent hover:border-[#E2DDD3] min-h-[48px]"
              >
                <Search className="w-5 h-5 text-[#C65319]" />
                <span>मदत विनंती ट्रॅक करा (Track Request)</span>
              </Link>

              {currentUser && (
                <>
                  <div className="pt-3 pb-1 text-[11px] font-bold uppercase tracking-wider text-[#7A6858] border-b border-[#E2DDD3]">
                    नियंत्रण व सेवा कक्ष / Seva Desks
                  </div>

                  {currentUser.role === 'volunteer' && (
                    <Link
                      to="/volunteer"
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-[#594333] bg-white border border-[#C69A52]/40 min-h-[48px]"
                    >
                      <Users className="w-5 h-5 text-[#C65319]" />
                      <span>स्वयंसेवक डेस्क (Volunteer Desk)</span>
                    </Link>
                  )}

                  {(currentUser.role === 'coordinator' || currentUser.role === 'admin') && (
                    <Link
                      to="/coordinator"
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-[#594333] bg-white border border-[#C65319]/40 min-h-[48px]"
                    >
                      <Shield className="w-5 h-5 text-[#C65319]" />
                      <span>समन्वयक डेस्क (Coordinator Desk)</span>
                    </Link>
                  )}
                </>
              )}
            </nav>
          </div>

          {/* User Auth Footer on Mobile Drawer */}
          <div className="pt-6 border-t border-[#E2DDD3] space-y-3">
            {currentUser ? (
              <div className="space-y-3">
                <div className="px-4 py-2.5 bg-white rounded-xl border border-[#E2DDD3] text-xs">
                  <p className="text-[#7A6858]">लॉगिन केलेले खाते:</p>
                  <p className="font-bold text-[#292723] text-sm">{currentUser.name || currentUser.phone}</p>
                  <p className="text-[11px] text-[#A83E16] capitalize font-semibold">{currentUser.role} Account</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-white border border-rose-200 text-rose-700 font-semibold text-xs min-h-[48px]"
                >
                  <LogOut className="w-4 h-4" />
                  <span>लॉगआउट करा (Logout)</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl bg-[#C65319] hover:bg-[#A83E16] text-white font-bold text-sm shadow-md shadow-[#C65319]/25 min-h-[48px]"
              >
                <User className="w-4 h-4" />
                <span>प्रवेश करा किंवा नोंदणी करा (Login / Sign Up)</span>
              </Link>
            )}

            <p className="text-center text-[10px] text-[#A09385] pt-2">
              वारकरी — पंढरपूर वारी डिजिटल महासोहळा साथीदार
            </p>
          </div>
        </div>
      )}
    </header>
  );
}
