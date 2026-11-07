import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const { currentUser, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
        <span className="text-sm">Verifying authentication...</span>
      </div>
    );
  }

  if (!currentUser) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(currentUser.role)) {
    // If volunteer but unapproved
    if (currentUser.role === 'volunteer' && currentUser.volunteer_status !== 'APPROVED') {
      return (
        <div className="max-w-md mx-auto my-12 p-6 rounded-2xl bg-amber-950/40 border border-amber-800/60 text-slate-200 text-center space-y-3">
          <h2 className="text-lg font-bold text-amber-400">Application Under Review</h2>
          <p className="text-sm">
            आपला स्वयंसेवक अर्ज सध्या प्रशासकीय पडताळणी प्रक्रियेत आहे. (Your volunteer application is currently pending administrator approval.)
          </p>
        </div>
      );
    }
    return <Navigate to="/" replace />;
  }

  return children;
}

