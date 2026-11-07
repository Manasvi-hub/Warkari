import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { HomePage } from './pages/HomePage';
import { AssistantPage } from './pages/AssistantPage';
import { LoginPage } from './pages/LoginPage';
import { FacilitiesPage } from './pages/FacilitiesPage';
import { VolunteerDashboard } from './pages/VolunteerDashboard';
import { CoordinatorDashboard } from './pages/CoordinatorDashboard';
import { TrackIncidentPage } from './pages/TrackIncidentPage';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-[#FAF8F3] text-[#292723] flex flex-col antialiased selection:bg-[#C65319] selection:text-white">
        <Navbar />
        <main className="flex-1 w-full">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/facilities" element={<FacilitiesPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/track" element={<TrackIncidentPage />} />
            <Route
              path="/volunteer"
              element={
                <ProtectedRoute allowedRoles={['volunteer', 'coordinator', 'admin']}>
                  <VolunteerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/coordinator"
              element={
                <ProtectedRoute allowedRoles={['coordinator', 'admin']}>
                  <CoordinatorDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>

        {/* Editorial Culturally Grounded Footer */}
        <footer className="border-t border-[#E2DDD3] bg-[#F0EDE5] py-12 text-sm text-[#594333]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-[#E2DDD3]">
              {/* Brand & Cultural Rooting */}
              <div className="md:col-span-2 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="font-display font-bold text-lg tracking-wider text-[#292723]">
                    WARKARI | वारकरी
                  </span>
                </div>
                <p className="text-xs text-[#7A6858] leading-relaxed max-w-md">
                  A digital companion dedicated to the centuries-old tradition of the Pandharpur Waari procession. Built with multilingual speech intelligence, real-time verified route facilities, and compassionate seva coordination.
                </p>
                <p className="text-xs font-marathi text-[#A83E16] font-medium pt-1">
                  "ज्ञानोबा-तुकाराम" — विठ्ठल नामाचा गजर आणि सेवाभावाची निरंतर वाटचाल.
                </p>
              </div>

              {/* Quick Navigation */}
              <div className="space-y-2.5">
                <h4 className="text-xs uppercase font-bold tracking-wider text-[#292723]">Quick Navigation</h4>
                <ul className="space-y-1.5 text-xs">
                  <li><a href="/assistant" className="text-[#594333] hover:text-[#C65319] transition-colors">Pilgrim Voice Assistant</a></li>
                  <li><a href="/facilities" className="text-[#594333] hover:text-[#C65319] transition-colors">Route Facilities & Camps</a></li>
                  <li><a href="/track" className="text-[#594333] hover:text-[#C65319] transition-colors">Track Assistance Request</a></li>
                  <li><a href="/login" className="text-[#594333] hover:text-[#C65319] transition-colors">Sevak & Coordinator Portal</a></li>
                </ul>
              </div>

              {/* Technology & Safety */}
              <div className="space-y-2.5">
                <h4 className="text-xs uppercase font-bold tracking-wider text-[#292723]">Pilgrim Safety</h4>
                <div className="text-xs text-[#7A6858] space-y-1">
                  <p>National Emergency: <strong className="text-[#292723]">112</strong></p>
                  <p>Ambulance Service: <strong className="text-[#C65319]">108</strong></p>
                  <p className="pt-2 text-[11px]">Backend API: FastAPI + SQLite</p>
                  <p className="text-[11px]">Speech Engine: Gnani Multilingual</p>
                </div>
              </div>
            </div>

            <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-[#7A6858] gap-4">
              <p>© 2026 Warkari Platform. Dedicated to all Palkhi pilgrims, Sevaks, and Temple Trusts.</p>
              <div className="flex items-center gap-4">
                <span>Sant Dnyaneshwar Maharaj Palkhi</span>
                <span>•</span>
                <span>Sant Tukaram Maharaj Palkhi</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </AuthProvider>
  );
}
