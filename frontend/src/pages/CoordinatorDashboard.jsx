import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchCoordinatorIncidents,
  fetchEligibleVolunteers,
  assignVolunteerToIncident,
  fetchIncidentAssignmentsHistory
} from '../services/api';
import {
  Activity,
  Filter,
  UserCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  Eye,
  Loader2,
  MapPin,
  Shield,
  PhoneCall
} from 'lucide-react';

export function CoordinatorDashboard() {
  const { currentUser } = useAuth();
  const [incidents, setIncidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Assignment Modal State
  const [assigningIncident, setAssigningIncident] = useState(null);
  const [volunteers, setVolunteers] = useState([]);
  const [selectedVolId, setSelectedVolId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');
  const [submittingAssign, setSubmittingAssign] = useState(false);
  const [successBanner, setSuccessBanner] = useState(null);

  // History Modal State
  const [historyIncident, setHistoryIncident] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadIncidents = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, limit: 10 };
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await fetchCoordinatorIncidents(params);
      setIncidents(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err.message || 'Failed to load incident records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [page, categoryFilter, statusFilter]);

  const openAssignModal = async (incident) => {
    setAssigningIncident(incident);
    setSelectedVolId('');
    setAssignNotes('');
    try {
      const volData = await fetchEligibleVolunteers();
      setVolunteers(volData);
      if (volData.length > 0) {
        setSelectedVolId(volData[0].id.toString());
      }
    } catch (err) {
      setError('Failed to fetch eligible volunteers.');
    }
  };

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!assigningIncident || !selectedVolId) return;

    setSubmittingAssign(true);
    try {
      await assignVolunteerToIncident(
        assigningIncident.id,
        parseInt(selectedVolId),
        assignNotes
      );
      setSuccessBanner(`Incident #${assigningIncident.id} assigned successfully.`);
      setAssigningIncident(null);
      await loadIncidents();
      setTimeout(() => setSuccessBanner(null), 4000);
    } catch (err) {
      setError(err.message || 'Failed to assign volunteer.');
    } finally {
      setSubmittingAssign(false);
    }
  };

  const openHistoryModal = async (incident) => {
    setHistoryIncident(incident);
    setLoadingHistory(true);
    try {
      const hist = await fetchIncidentAssignmentsHistory(incident.id);
      setHistoryList(hist);
    } catch (err) {
      setError('Failed to load assignment audit history.');
    } finally {
      setLoadingHistory(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-6">
      {/* Editorial Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2DDD3] pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/40 text-[#A83E16] text-xs font-semibold">
            <Shield className="w-3.5 h-3.5 text-[#C65319]" />
            <span>वारी नियंत्रण कक्ष / Coordinator Operations Hub</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-[#292723] mt-2">
            घटना व्यवस्थापन आणि स्वयंसेवक नियुक्ती
          </h1>
          <p className="text-xs text-[#7A6858]">
            समन्वयक: <strong>{currentUser?.name || 'Officer'}</strong> • एकूण नोंदी: <strong>{total}</strong>
          </p>
        </div>

        <button
          onClick={loadIncidents}
          disabled={loading}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-[#F0EDE5] text-[#292723] text-xs font-semibold rounded-xl border border-[#E2DDD3] shadow-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#C65319] ${loading ? 'animate-spin' : ''}`} />
          <span>रिफ्रेश (Refresh)</span>
        </button>
      </div>

      {successBanner && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successBanner}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Row */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-2xl border border-[#E2DDD3] shadow-xs">
        <Filter className="w-4 h-4 text-[#C65319]" />
        <span className="text-xs font-semibold text-[#292723]">गाळणी (Filters):</span>

        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
          className="text-xs bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl px-3 py-1.5 text-[#292723] focus:outline-hidden focus:border-[#C65319]"
        >
          <option value="">सर्व श्रेणी (All Categories)</option>
          <option value="medical_emergency">Medical Emergency</option>
          <option value="water_shortage">Water Shortage</option>
          <option value="lost_person">Lost Person</option>
          <option value="general_assistance">General Assistance</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="text-xs bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl px-3 py-1.5 text-[#292723] focus:outline-hidden focus:border-[#C65319]"
        >
          <option value="">सर्व स्थिती (All Status)</option>
          <option value="OPEN">OPEN (प्रलंबित)</option>
          <option value="ASSIGNED">ASSIGNED (नियुक्त)</option>
          <option value="EN_ROUTE">EN_ROUTE (मार्गावर)</option>
          <option value="ON_SCENE">ON_SCENE (स्थळी)</option>
          <option value="RESOLVED">RESOLVED (पूर्ण)</option>
        </select>
      </div>

      {/* High-Contrast Professional Operational Incident Table */}
      <div className="bg-white border border-[#E2DDD3] rounded-2xl overflow-hidden shadow-xs">
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-[#C65319] animate-spin mx-auto" />
            <p className="text-xs text-[#7A6858]">घटना नोंदी लोड होत आहेत...</p>
          </div>
        ) : incidents.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Activity className="w-8 h-8 text-[#A09385] mx-auto" />
            <p className="text-xs text-[#7A6858]">कोणतीही घटना आढळली नाही.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF8F3] text-[#594333] uppercase text-[11px] font-bold border-b border-[#E2DDD3]">
                <tr>
                  <th className="py-3 px-4">ID / Ref</th>
                  <th className="py-3 px-4">श्रेणी (Category)</th>
                  <th className="py-3 px-4">वर्णन (Description)</th>
                  <th className="py-3 px-4">ठिकाण (Location)</th>
                  <th className="py-3 px-4">स्थिती (Status)</th>
                  <th className="py-3 px-4">सक्रिय स्वयंसेवक</th>
                  <th className="py-3 px-4 text-right">कृती (Actions)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2DDD3] text-[#292723]">
                {incidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-[#FAF8F3]/60 transition-colors">
                    <td className="py-3.5 px-4 font-mono">
                      <span className="font-bold text-[#292723]">#{inc.id}</span>
                      {inc.public_reference && (
                        <div className="text-[10px] text-[#7A6858] font-sans">
                          {inc.public_reference}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold capitalize text-[#A83E16]">
                        {inc.category.replace('_', ' ')}
                      </span>
                      <div className="text-[10px] text-[#A09385]">
                        Priority: {inc.urgency_level || inc.priority}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate" title={inc.description}>
                      {inc.description}
                    </td>
                    <td className="py-3.5 px-4 text-[#594333]">
                      {inc.location_description || 'Pandharpur Marg'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          inc.status === 'RESOLVED'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : inc.status === 'OPEN'
                            ? 'bg-rose-50 text-rose-800 border border-rose-200'
                            : 'bg-amber-50 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-[#594333]">
                      {inc.active_assignment ? (
                        <span className="font-semibold text-emerald-700">
                          Sevak #{inc.active_assignment.volunteer_profile_id} ({inc.active_assignment.status})
                        </span>
                      ) : (
                        <span className="text-[#A09385] italic">नियुक्त नाही</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => openAssignModal(inc)}
                        className="px-2.5 py-1 bg-[#C65319] hover:bg-[#A83E16] text-white text-[11px] font-semibold rounded-lg shadow-2xs"
                      >
                        नियुक्त करा
                      </button>
                      <button
                        onClick={() => openHistoryModal(inc)}
                        className="p-1 text-[#7A6858] hover:text-[#292723] hover:bg-[#F0EDE5] rounded-md"
                        title="View Audit History"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-[#7A6858] pt-2">
        <span>पृष्ठ {page} (एकूण {Math.ceil(total / 10) || 1})</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 bg-white border border-[#E2DDD3] rounded-lg disabled:opacity-50 text-[#292723] hover:bg-[#F0EDE5]"
          >
            मागील
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * 10 >= total}
            className="px-3 py-1.5 bg-white border border-[#E2DDD3] rounded-lg disabled:opacity-50 text-[#292723] hover:bg-[#F0EDE5]"
          >
            पुढील
          </button>
        </div>
      </div>

      {/* Assignment Modal */}
      {assigningIncident && (
        <div className="fixed inset-0 bg-[#292723]/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-[#E2DDD3] rounded-3xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-[#292723]">
              स्वयंसेवक नियुक्ती — तिकीट #{assigningIncident.id}
            </h3>
            <p className="text-xs text-[#594333]">
              {assigningIncident.description}
            </p>

            <form onSubmit={handleAssignSubmit} className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-[#292723] mb-1">
                  पात्र स्वयंसेवक निवडा (Eligible Approved Sevak):
                </label>
                <select
                  value={selectedVolId}
                  onChange={(e) => setSelectedVolId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-xs text-[#292723]"
                >
                  {volunteers.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.phone}) — {v.sector || 'Pandharpur'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#292723] mb-1">
                  समन्वयक सूचना (Notes):
                </label>
                <textarea
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
                  rows="2"
                  placeholder="कृपया तात्काळ घटनास्थळी भेट द्या..."
                  className="w-full px-3 py-2 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl text-xs text-[#292723]"
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setAssigningIncident(null)}
                  className="px-4 py-2 text-xs text-[#7A6858] hover:text-[#292723]"
                >
                  रद्द करा
                </button>
                <button
                  type="submit"
                  disabled={submittingAssign || !selectedVolId}
                  className="px-4 py-2 bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-bold rounded-xl shadow-xs disabled:opacity-50"
                >
                  {submittingAssign ? 'नियुक्त करत आहे...' : 'नियुक्ती निश्चित करा'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* History Modal */}
      {historyIncident && (
        <div className="fixed inset-0 bg-[#292723]/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-[#E2DDD3] rounded-3xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-[#292723]">
              ऑडिट इतिहास — तिकीट #{historyIncident.id}
            </h3>

            {loadingHistory ? (
              <div className="py-8 text-center">
                <Loader2 className="w-6 h-6 text-[#C65319] animate-spin mx-auto" />
              </div>
            ) : historyList.length === 0 ? (
              <p className="text-xs text-[#7A6858] py-4">या घटनेसाठी अद्याप कोणतीही नियुक्ती नोंद नाही.</p>
            ) : (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {historyList.map((h) => (
                  <div key={h.id} className="p-3 bg-[#FAF8F3] rounded-xl border border-[#E2DDD3] text-xs space-y-1">
                    <div className="flex justify-between font-bold">
                      <span className="text-[#292723]">Sevak Profile #{h.volunteer_profile_id}</span>
                      <span className="text-[#C65319] uppercase">{h.status}</span>
                    </div>
                    <p className="text-[#7A6858] text-[11px]">वेळ: {new Date(h.assigned_at).toLocaleString()}</p>
                    {h.rejection_reason && (
                      <p className="text-rose-700 font-semibold">अस्वीकार कारण: {h.rejection_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setHistoryIncident(null)}
                className="px-4 py-2 bg-[#FAF8F3] hover:bg-[#F0EDE5] border border-[#E2DDD3] text-[#292723] text-xs font-semibold rounded-xl"
              >
                बंद करा (Close)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
