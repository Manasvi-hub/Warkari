import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Flame, Compass, Search, User, LogOut, Mic, Users, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="border-b border-[#E8E2D5] bg-[#FAF8F3]/95 backdrop-blur-md sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Brand identity */}
        <Link to="/" className="flex items-center gap-3.5 group">
          <div className="w-11 h-11 rounded-xl bg-[#C65319] text-white flex items-center justify-center shadow-md shadow-[#C65319]/20 group-hover:bg-[#A83E16] transition-all transform group-hover:scale-102">
            <Flame className="w-6 h-6 fill-white/20" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-xl tracking-wider text-[#292723]">
                WARKARI
              </span>
              <span className="text-xs font-marathi font-bold text-[#A83E16] bg-[#C65319]/10 px-2 py-0.5 rounded border border-[#C65319]/20">
                वारकरी
              </span>
            </div>
            <p className="text-[11px] text-[#7A6858] font-medium tracking-wide hidden sm:block">
              Pandharpur Waari Companion
            </p>
          </div>
        </Link>

        {/* Navigation links */}
        <nav className="flex items-center gap-2 sm:gap-3">
          <Link
            to="/assistant"
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#FAF8F3] hover:bg-[#F0EDE5] text-[#292723] border border-[#E2DDD3] transition-all shadow-xs"
          >
            <Mic className="w-3.5 h-3.5 text-[#C65319]" />
            <span className="hidden xs:inline">Voice Assistant</span>
            <span className="xs:hidden">Assistant</span>
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
            <span className="hidden sm:inline">Track Request</span>
            <span className="sm:hidden">Track</span>
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
                className="p-2 rounded-lg text-[#7A6858] hover:text-[#292723] hover:bg-[#F0EDE5] transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#C65319] hover:bg-[#A83E16] text-white shadow-sm shadow-[#C65319]/20 transition-all ml-1"
            >
              <User className="w-3.5 h-3.5" />
              <span>Login</span>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
