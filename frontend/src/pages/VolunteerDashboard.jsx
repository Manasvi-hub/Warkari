import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchVolunteerAssignments,
  acceptAssignment,
  rejectAssignment,
  updateIncidentProgress
} from '../services/api';
import {
  ClipboardList,
  CheckCircle,
  XCircle,
  Truck,
  MapPin,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  RefreshCw,
  HeartHandshake,
  ShieldAlert
} from 'lucide-react';

export function VolunteerDashboard() {
  const { currentUser } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  const loadAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchVolunteerAssignments();
      setAssignments(data);
    } catch (err) {
      setError(err.message || 'Failed to load assignments.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, []);

  const handleAccept = async (assignmentId) => {
    setActionLoading(assignmentId);
    try {
      await acceptAssignment(assignmentId);
      await loadAssignments();
    } catch (err) {
      setError(err.message || 'Failed to accept assignment.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (e, assignmentId) => {
    e.preventDefault();
    if (!rejectReason.trim()) return;

    setActionLoading(assignmentId);
    try {
      await rejectAssignment(assignmentId, rejectReason.trim());
      setRejectingId(null);
      setRejectReason('');
      await loadAssignments();
    } catch (err) {
      setError(err.message || 'Failed to reject assignment.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleProgress = async (incidentId, targetStatus) => {
    setActionLoading(incidentId);
    try {
      await updateIncidentProgress(incidentId, targetStatus);
      await loadAssignments();
    } catch (err) {
      setError(err.message || `Failed to update status to ${targetStatus}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-3.5 sm:px-6 lg:px-8 py-5 sm:py-10 space-y-5 sm:space-y-6">
      {/* Mobile-first header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 border-b border-[#E2DDD3] pb-4 sm:pb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FAF8F3] border border-[#C69A52]/40 text-[#A83E16] text-[11px] sm:text-xs font-semibold">
            <HeartHandshake className="w-3.5 h-3.5 text-[#C65319]" />
            <span>स्वयंसेवक सेवा डॅशबोर्ड / Volunteer Seva Desk</span>
          </div>
          <h1 className="text-xl sm:text-3xl font-display font-bold text-[#292723] mt-1.5 sm:mt-2">
            आपल्याकडे सोपवलेली कार्ये
          </h1>
          <p className="text-xs text-[#7A6858] mt-0.5">
            स्वागत आहे, <strong>{currentUser?.name || 'Sevak'}</strong> • सेक्टर:{' '}
            <span className="font-semibold text-[#292723]">{currentUser?.volunteer_sector || 'वाखारी'}</span>
          </p>
        </div>

        <button
          onClick={loadAssignments}
          disabled={loading}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-[#F0EDE5] text-[#292723] text-xs font-semibold rounded-xl border border-[#E2DDD3] shadow-xs transition-colors min-h-[40px]"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#C65319] ${loading ? 'animate-spin' : ''}`} />
          <span>रिफ्रेश (Refresh)</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 sm:p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Assignments List */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#C65319] animate-spin mx-auto" />
          <p className="text-xs text-[#7A6858]">मदत कार्ये लोड होत आहेत...</p>
        </div>
      ) : assignments.length === 0 ? (
        <div className="py-16 text-center bg-white border border-[#E2DDD3] rounded-3xl space-y-2">
          <ClipboardList className="w-8 h-8 text-[#A09385] mx-auto" />
          <h3 className="text-sm font-bold text-[#292723]">सध्या कोणतीही प्रलंबित विनंती नाही</h3>
          <p className="text-xs text-[#7A6858]">नवीन विनंती नियुक्त झाल्यावर येथे तात्काळ दिसेल.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {assignments.map((assignment) => (
            <div
              key={assignment.id}
              className="bg-white border border-[#E2DDD3] rounded-2xl p-4 sm:p-6 shadow-xs space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2DDD3] pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold text-[#292723] bg-[#FAF8F3] px-2.5 py-1 rounded border border-[#E2DDD3]">
                    तिकीट #{assignment.incident_id}
                  </span>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${assignment.status === 'ACCEPTED'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : assignment.status === 'REJECTED'
                          ? 'bg-rose-50 text-rose-800 border border-rose-200'
                          : 'bg-amber-50 text-amber-800 border border-amber-200'
                      }`}
                  >
                    {assignment.status}
                  </span>
                </div>

                <span className="text-[11px] text-[#A09385]">
                  {new Date(assignment.assigned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>

              {/* Assignment Actions */}
              {assignment.status === 'PENDING' && (
                <div className="space-y-3">
                  <p className="text-xs text-[#594333] leading-relaxed">
                    समन्वयकाने आपल्याकडे हे सहाय्य कार्य सोपवले आहे. आपण हे स्वीकारण्यास तयार आहात का?
                  </p>
                  <div className="flex flex-col xs:flex-row gap-2">
                    <button
                      onClick={() => handleAccept(assignment.id)}
                      disabled={actionLoading === assignment.id}
                      className="w-full xs:w-auto px-4 py-2.5 bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center justify-center gap-1.5 min-h-[42px]"
                    >
                      {actionLoading === assignment.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <CheckCircle className="w-3.5 h-3.5" />
                      )}
                      <span>स्वीकारा (Accept)</span>
                    </button>

                    <button
                      onClick={() => setRejectingId(assignment.id)}
                      className="w-full xs:w-auto px-4 py-2.5 bg-white hover:bg-[#F0EDE5] text-rose-700 text-xs font-semibold rounded-xl border border-rose-200 transition-colors flex items-center justify-center gap-1.5 min-h-[42px]"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>अस्वीकार (Reject)</span>
                    </button>
                  </div>

                  {rejectingId === assignment.id && (
                    <form
                      onSubmit={(e) => handleReject(e, assignment.id)}
                      className="p-3.5 bg-[#FAF8F3] border border-[#E2DDD3] rounded-xl space-y-2 mt-2"
                    >
                      <label className="block text-[11px] font-semibold text-[#292723]">
                        अस्वीकाराचे कारण (Mandatory Reason):
                      </label>
                      <input
                        type="text"
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                        placeholder="उदा. सध्या इतर रुग्णासोबत व्यस्त आहे"
                        required
                        className="w-full px-3 py-2 bg-white border border-[#E2DDD3] rounded-lg text-xs text-[#292723]"
                      />
                      <div className="flex gap-2">
                        <button
                          type="submit"
                          className="px-3.5 py-1.5 bg-rose-700 hover:bg-rose-800 text-white text-xs font-bold rounded-lg min-h-[38px]"
                        >
                          अस्वीकार निश्चित करा
                        </button>
                        <button
                          type="button"
                          onClick={() => setRejectingId(null)}
                          className="px-3 py-1.5 text-xs text-[#7A6858] hover:text-[#292723]"
                        >
                          रद्द करा
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}

              {/* Progress Stepper for Accepted Assignments */}
              {assignment.status === 'ACCEPTED' && (
                <div className="space-y-2.5 pt-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#C65319]">
                    मदत प्रगती अद्ययावत करा:
                  </span>
                  <div className="grid grid-cols-1 xs:grid-cols-3 gap-2">
                    <button
                      onClick={() => handleProgress(assignment.incident_id, 'EN_ROUTE')}
                      disabled={actionLoading === assignment.incident_id}
                      className="py-2.5 px-3 bg-[#FAF8F3] hover:bg-[#F0EDE5] border border-[#C69A52]/50 text-[#594333] text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-colors min-h-[42px]"
                    >
                      <Truck className="w-3.5 h-3.5 text-[#C65319]" />
                      <span>मार्गावर</span>
                    </button>

                    <button
                      onClick={() => handleProgress(assignment.incident_id, 'ON_SCENE')}
                      disabled={actionLoading === assignment.incident_id}
                      className="py-2.5 px-3 bg-[#FAF8F3] hover:bg-[#F0EDE5] border border-[#C69A52]/50 text-[#594333] text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-colors min-h-[42px]"
                    >
                      <MapPin className="w-3.5 h-3.5 text-[#C65319]" />
                      <span>स्थळी पोहोचलो</span>
                    </button>

                    <button
                      onClick={() => handleProgress(assignment.incident_id, 'RESOLVED')}
                      disabled={actionLoading === assignment.incident_id}
                      className="py-2.5 px-3 bg-[#C65319] hover:bg-[#A83E16] text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-xs transition-all min-h-[42px]"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>पूर्ण झाले</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
