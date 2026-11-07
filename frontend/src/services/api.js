const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function fetchSystemInfo() {
  const response = await fetch(`${API_BASE_URL}/api/system/info`);
  if (!response.ok) {
    throw new Error(`System info request failed with status: ${response.status}`);
  }
  return response.json();
}

/**
 * Transcribe recorded audio file using Gnani Prisma v2.5 STT.
 */
export async function transcribeAudio(audioBlob, language = 'mr-IN') {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('language', language);

  const response = await fetch(`${API_BASE_URL}/api/assistant/transcribe`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Audio transcription failed.');
  }
  return data;
}

/**
 * Synthesize speech from text using Gnani Timbre v2.5 TTS.
 */
export async function synthesizeSpeech(text, language = 'mr-IN', signal = null) {
  const response = await fetch(`${API_BASE_URL}/api/assistant/speak`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, language }),
    signal: signal || undefined,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Speech synthesis failed.');
  }
  return response.blob();
}

/**
 * Executes end-to-end voice pipeline (STT -> Response -> TTS).
 */
export async function processVoicePipeline(audioBlob, language = 'mr-IN', signal = null) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('language', language);

  const response = await fetch(`${API_BASE_URL}/api/assistant/voice`, {
    method: 'POST',
    body: formData,
    signal: signal || undefined,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Voice processing pipeline failed.');
  }
  return data;
}

/**
 * Phase 3 & 3.1: Text Assistant Intelligence Pipeline with staged consent support.
 * Sends message to /api/intelligence/chat.
 * @param {string} message
 * @param {string} language
 * @param {object} [options]
 * @returns {Promise<{intent: string, confidence: number, response_text: string, facilities: Array, incident: object, clarification_required: boolean, awaiting_missing_person_consent: boolean, awaiting_missing_person_details: boolean}>}
 */
export async function sendChatMessage(message, language = 'mr-IN', options = {}, signal = null) {
  const payload = {
    message,
    language,
    latitude: options.latitude || null,
    longitude: options.longitude || null,
    location_name: options.location_name || null,
    missing_person_consent: options.missing_person_consent !== undefined ? options.missing_person_consent : null,
    missing_person_details: options.missing_person_details || null,
  };

  const response = await fetch(`${API_BASE_URL}/api/intelligence/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: signal || undefined,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to process chat intelligence.');
  }
  return data;
}

/**
 * Phase 3 & 3.1: Facility Search & Filtering.
 */
export async function searchFacilities(params = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/intelligence/facilities?${query}`);
  if (!response.ok) {
    throw new Error('Failed to fetch facilities.');
  }
  return response.json();
}

// -------------------------------------------------------------
// Phase 4.2 & 4.3: Authentication & User APIs
// -------------------------------------------------------------
export async function registerUser(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Registration failed.');
  }
  return data;
}

export async function loginUser(phone, password) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Receive HttpOnly cookies
    body: JSON.stringify({ phone, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Invalid phone or password.');
  }
  return data;
}

export async function logoutUser() {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  return response.json();
}

export async function getCurrentUser(token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    method: 'GET',
    headers,
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Unauthorized');
  }
  return response.json();
}

// -------------------------------------------------------------
// Phase 4.3: Public Tracking API
// -------------------------------------------------------------
export async function trackIncidentByToken(token) {
  const response = await fetch(`${API_BASE_URL}/api/v1/public/incidents/track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Invalid or expired tracking token.');
  }
  return data;
}

// -------------------------------------------------------------
// Phase 4.3: Volunteer Workflow APIs
// -------------------------------------------------------------
export async function fetchVolunteerAssignments() {
  const response = await fetch(`${API_BASE_URL}/api/v1/volunteer/assignments`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch volunteer assignments.');
  }
  return response.json();
}

export async function acceptAssignment(assignmentId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/volunteer/assignments/${assignmentId}/accept`, {
    method: 'POST',
    credentials: 'include',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to accept assignment.');
  }
  return data;
}

export async function rejectAssignment(assignmentId, reason) {
  const response = await fetch(`${API_BASE_URL}/api/v1/volunteer/assignments/${assignmentId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ reason }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to reject assignment.');
  }
  return data;
}

export async function updateIncidentProgress(incidentId, statusAction, notes = '') {
  // statusAction: 'en-route', 'on-scene', 'resolve'
  const response = await fetch(`${API_BASE_URL}/api/v1/volunteer/incidents/${incidentId}/${statusAction}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ notes }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `Failed to transition incident to ${statusAction}.`);
  }
  return data;
}

// -------------------------------------------------------------
// Phase 4.3: Coordinator Workflow APIs
// -------------------------------------------------------------
export async function fetchCoordinatorIncidents(params = {}) {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/api/v1/coordinator/incidents?${query}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch coordinator incidents.');
  }
  return response.json();
}

export async function fetchEligibleVolunteers(sector = '') {
  const query = sector ? `?sector=${encodeURIComponent(sector)}` : '';
  const response = await fetch(`${API_BASE_URL}/api/v1/coordinator/eligible-volunteers${query}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch eligible volunteers.');
  }
  return response.json();
}

export async function assignVolunteerToIncident(incidentId, volunteerProfileId, notes = '') {
  const response = await fetch(`${API_BASE_URL}/api/v1/coordinator/incidents/${incidentId}/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ volunteer_profile_id: volunteerProfileId, notes }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to assign volunteer.');
  }
  return data;
}

export async function fetchIncidentAssignmentsHistory(incidentId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/coordinator/incidents/${incidentId}/assignments`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch assignment history.');
  }
  return response.json();
}
