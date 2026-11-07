# Warkari (वारकरी) — Phase 3.1: Reliability, Safety & User Experience Refinement

A multilingual, voice-first AI assistance platform engineered for Varkari pilgrims participating in the Pandharpur Wari pilgrimage.

---

## 📌 Phase 3.1 Enhancements

1. **Facility Integrity**:
   - Case A: `is_demo=True` → strictly displays **`DEMO DATA`** (never `VERIFIED`).
   - Case B: `is_demo=False` and `is_verified=True` → displays **`VERIFIED`**.
   - Case C: `is_demo=False` and `is_verified=False` → displays **`UNVERIFIED`**.
   - **Zero Fake Phone Numbers**: All placeholder phone numbers (e.g., `+91-00000-00000`) removed. Contacts render only if non-demo and genuinely verified.

2. **Staged Missing-Person Workflow & Privacy**:
   - Stage 1: Recognition & empathetic response.
   - Stage 2: Explicit consent inquiry ("Would you like to register an assistance request?"). Declining records **NO** incident.
   - Stage 3: Minimum essential information intake (Identifier, approximate age, last known location; no Aadhaar/financial PII).
   - Stage 4: Ticket creation with non-guarantee safety disclaimer (*"Your request has been recorded. This does not mean a volunteer has been assigned or that emergency services have been contacted."*).
   - **Privacy Masking**: Public incident status endpoints mask personal identity and original messages.

3. **Multilingual Consistency**:
   - English requests receive pure English responses (no mixed Marathi/Hindi phrases).
   - Marathi and Hindi requests receive grammatically clean localized responses in their respective scripts.

4. **Friendly Greetings**:
   - Dedicated `GREETING` intent responding warmly across Marathi (*"नमस्कार! मी वारकरी सहाय्यक आहे..."*), Hindi, and English (*"Namaskar! I am Warkari, your pilgrimage assistance assistant..."*) without triggering false facilities or incidents.

---

## 🚀 Quickstart Guide

### 1. Backend Server

```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Development Server

```powershell
cd frontend
npm run dev
```

- **Assistant App**: [http://localhost:5173/assistant](http://localhost:5173/assistant) (or port `5174`)
- **FastAPI OpenAPI Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Phase 3.1 Verification Suite**: `python backend/test_phase3_1.py`
