# Medical Assistant Chatbot & Doctor Locator
## Technical Documentation & API Specification

---

# 1. System Overview

The Medical Assistant Chatbot module combines three capabilities:

1. **RAG-Grounded Consultation Engine** — multi-turn symptom triage powered by Mistral AI, grounded with live PubMed citations via NCBI E-utilities.
2. **PubMed Citation Pipeline** — fetches peer-reviewed literature in real time and injects abstracts as context before Mistral is called, eliminating hallucinated references.
3. **Healthcare Facility Locator** — geographic discovery of hospitals, clinics, and specialists using LocationIQ.

### Module Files

| File | Purpose |
|---|---|
| `chatbot/engine.py` | Core consultation + doctor-finder logic |
| `chatbot/pubmed_rag.py` | Live PubMed E-utilities citation fetcher (RAG) |

---

# 2. Environment Setup & Configuration

Create a `.env` file in the project root:

```env
# Required — Mistral AI (OCR, Vision, Consultation)
MISTRAL_API_KEY=your_mistral_api_key_here

# Required — LocationIQ (Geocoding + Nearby Search)
LOCATIONIQ_API_KEY=your_locationiq_api_key_here

# Optional — NCBI PubMed (raises rate limit from 3 req/s → 10 req/s)
# Get a free key at https://www.ncbi.nlm.nih.gov/account/
PUBMED_API_KEY=
```

> **Note:** The system works without `PUBMED_API_KEY` at 3 requests/second. Add a key for production workloads.

---

# 3. Architecture & Data Flow

## 3.1 Consultation Flow (with PubMed RAG)

```text
[ User Input: Symptoms / File ]
            │
            ▼
  ┌─────────────────────┐
  │   PubMed RAG Layer  │  ◄── chatbot/pubmed_rag.py
  │                     │
  │ 1. Extract keywords │
  │ 2. E-search PMIDs   │
  │ 3. E-fetch abstracts│
  │ 4. Build context    │
  └─────────┬───────────┘
            │  context_block + citations[]
            ▼
  ┌───────────────────────────────┐
  │   Prompt Construction         │
  │                               │
  │  • Patient symptoms           │
  │  • PubMed literature block    │
  │  • PDF OCR text (if present)  │
  │  • Conversation history       │  ◄── last 10 turns
  └─────────────┬─────────────────┘
                │
                ▼
      Mistral Chat Completion
      (mistral-small / pixtral)
                │
                ▼
       Structured JSON Advice
                │
                ▼
  ┌─────────────────────────────┐
  │  Response                   │
  │  • advice                   │
  │  • urgency                  │
  │  • recommended_specialist   │
  │  • disclaimer               │
  │  • citations[]  ◄── PubMed  │
  └─────────────────────────────┘
```

## 3.2 Doctor Finder Flow

```text
[ Location String ]
        │
        ▼
LocationIQ Geocoder → Lat/Lon
        │
        ▼
LocationIQ Nearby API
(hospitals, clinics, doctors, healthcare)
        │
        ▼
Haversine Distance Filter
        │
        ▼
Optional Specialty Filter
        │
        ▼
Deduplicate & Sort by Distance
        │
        ▼
Top 15 Results (JSON)
```

---

# 4. PubMed RAG Pipeline (`chatbot/pubmed_rag.py`)

This module provides live, citation-backed grounding for every consultation response.

## 4.1 How It Works

| Step | Function | Description |
|---|---|---|
| 1 | `extract_medical_keywords()` | Strips filler words, deduplicates, takes top 6 medical terms |
| 2 | `search_pubmed()` | NCBI E-search — last 10 years, English, sorted by relevance |
| 3 | `fetch_abstracts()` | NCBI E-fetch XML — title, authors, abstract, journal, PMID, URL |
| 4 | `get_pubmed_citations()` | Orchestrates steps 1–3, returns `citations[]` + `context_block` |

## 4.2 `get_pubmed_citations()` Return Schema

```python
{
  "citations": [
    {
      "pmid":    "30252328",
      "title":   "Acute Chest Pain ...",
      "authors": "Smith AB, Jones CD et al.",
      "journal": "J Am Coll Cardiol",
      "year":    "2018",
      "url":     "https://pubmed.ncbi.nlm.nih.gov/30252328/"
    },
    ...
  ],
  "context_block": "--- RELEVANT MEDICAL LITERATURE (PubMed) ---\n\n[1] ..."
}
```

## 4.3 Rate Limiting & Graceful Degradation

- Without `PUBMED_API_KEY`: 3 requests/second (0.4 s sleep added automatically)
- With `PUBMED_API_KEY`: 10 requests/second
- If PubMed is unreachable or returns no results, the engine proceeds without citations (no error thrown to the user)

---

# 5. API Endpoints

## 5.1 Consultation Engine

```http
POST /consult
Content-Type: multipart/form-data
Authorization: Bearer <JWT>
```

### Request Parameters

| Parameter | Type | Location | Required | Description |
|---|---|---|---|---|
| `symptoms` | String | Form | No* | Plain-text symptom description |
| `file` | Binary | Form | No* | PDF or image (jpg/png) |

> *At least one of `symptoms` or `file` must be provided.

> **Note:** The Mistral API key is no longer accepted as a form parameter or header — it is read exclusively from the server's `.env` file.

### Response — 200 OK

```json
{
  "advice": "The symptoms suggest a mild respiratory infection. Rest and stay hydrated.",
  "urgency": "low",
  "recommended_specialist": "General Physician",
  "disclaimer": "This is not a medical diagnosis. Please consult a licensed physician.",
  "citations": [
    {
      "pmid": "30252328",
      "title": "Upper Respiratory Tract Infections in Adults",
      "authors": "Eccles R et al.",
      "journal": "Postgrad Med J",
      "year": "2005",
      "url": "https://pubmed.ncbi.nlm.nih.gov/30252328/"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|---|---|---|
| `advice` | String | AI-generated clinical guidance (grounded in PubMed literature where available) |
| `urgency` | String | `low`, `medium`, or `high` |
| `recommended_specialist` | String \| null | Suggested specialist type |
| `disclaimer` | String | Medical safety disclaimer |
| `citations` | Array | PubMed articles used as RAG context (may be empty if no results found) |

### Error Responses

| Code | Condition |
|---|---|
| `400` | No symptoms or file provided |
| `401` | Invalid or missing JWT token |
| `500` | Mistral API failure, OCR failure, or unsupported file type |

---

## 5.2 Doctor & Facility Locator

```http
GET /find-doctors?location=Rawalpindi&specialty=neurologist&radius_km=15
Authorization: Bearer <JWT>
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `location` | String | Yes | — | City, area, landmark, or address |
| `specialty` | String | No | null | Medical specialty keyword filter |
| `radius_km` | Float | No | 15.0 | Search radius in kilometres |

### Response — 200 OK

```json
{
  "results": [
    {
      "name": "Holy Family Hospital",
      "address": "Holy Family Road, Satellite Town, Rawalpindi, Punjab, Pakistan",
      "distance_km": 2.45,
      "lat": 33.6335,
      "lon": 73.0658
    }
  ]
}
```

---

# 6. Core Engine Functions (`chatbot/engine.py`)

## `run_consult_logic()`

```python
def run_consult_logic(
    symptoms: str = "",
    file_bytes: Optional[bytes] = None,
    content_type: str = "",
    api_key: Optional[str] = None,         # deprecated — ignored, reads from .env
    chat_history: Optional[List[Dict]] = None,  # NEW: prior conversation turns
) -> dict
```

### Parameters

| Parameter | Description |
|---|---|
| `symptoms` | Free-text symptom description from the user |
| `file_bytes` | Raw bytes of an uploaded PDF or image |
| `content_type` | MIME type of the uploaded file |
| `chat_history` | List of `{"role": "user"/"assistant", "content": "..."}` — last 10 turns injected into Mistral context |

### Workflow

```text
1. PubMed RAG fetch (from symptoms keywords)
2. Build user prompt:
     - Patient symptoms
     - PubMed context block (if results found)
     - PDF OCR text (if PDF uploaded)
3. Build Mistral messages array:
     [system_prompt, ...history[-10:], user_message]
4. Call Mistral (mistral-small / pixtral for images)
5. Parse JSON response
6. Return advice + citations
```

### Conversation History

The `chat_history` parameter enables multi-turn memory. The engine takes the last **10** `{role, content}` entries from the session and prepends them between the system prompt and the current user message:

```text
[system] Medical assistant instructions...
[user]   "I have chest pain and shortness of breath"   ← turn 1
[assistant] "**Urgency:** 🔴 HIGH..."                  ← turn 1 response
[user]   "I also have sweating"                        ← turn 2 (current)
```

This allows Mistral to reference earlier symptoms when answering follow-up questions.

---

## `find_doctors_logic()`

```python
def find_doctors_logic(
    location: str,
    specialty: Optional[str] = None,
    radius_km: float = 15.0
) -> List[Dict]
```

Returns up to 15 deduplicated facilities sorted by distance.

### Internal Steps

1. **Geocode** — LocationIQ forward geocoding → `(lat, lon)`
2. **Nearby search** — `amenity:hospital,clinic,doctors,healthcare:*` within `radius_meters`
3. **Distance filter** — Haversine formula, drops entries beyond `radius_km`
4. **Specialty filter** — soft keyword match on name + type + class fields
5. **Deduplicate** — removes duplicate facility names
6. **Sort** — ascending distance

---

# 7. Frontend Chat UI (`frontend.py`)

The chatbot tab (`💬 AI Medical Chat`) is a full multi-turn chat interface.

## Features

| Feature | Implementation |
|---|---|
| Chat message bubbles | `st.chat_message("user")` / `st.chat_message("assistant")` |
| Persistent history | `st.session_state.chat_history` list of `{role, content, citations}` |
| File attachment | `st.file_uploader` (PDF, PNG, JPG) above the chat input |
| Chat input bar | `st.chat_input()` at the bottom of the panel |
| Citations (on-demand) | Collapsed `📚 N source(s)` expander per assistant message |
| Clear history | 🗑️ button appears once at least one message exists |
| Urgency badges | 🟢 LOW / 🟡 MEDIUM / 🔴 HIGH inline in assistant response |

## Citation Display

PubMed sources are shown in a **collapsed expander** below each assistant message. The user can click `📚 N source(s)` to reveal citation cards:

```
[1] Smith AB, Jones CD et al. (2018).
    Upper Respiratory Infections — Postgrad Med J.
    PMID: 30252328  →  [clickable link to pubmed.ncbi.nlm.nih.gov]
```

Citations are stored alongside the message in `chat_history` so they persist across re-renders.

## API Key

The Mistral API key is **no longer exposed in the UI**. It is loaded exclusively from the server-side `.env` file via `os.getenv("MISTRAL_API_KEY")`.

---

# 8. System Prompt

The Mistral system prompt instructs the model to:

1. Summarise observations in plain language
2. Suggest safe self-care steps (no prescriptive dosages)
3. Rate urgency: `low`, `medium`, or `high`
4. Recommend a specialist type or `null`
5. Add a medical disclaimer
6. Reference any medical literature provided in context naturally (e.g. *"According to recent literature..."*) — **never fabricate citations**

Respond schema (strict JSON):

```json
{
  "advice": "<string>",
  "urgency": "<low|medium|high>",
  "recommended_specialist": "<string|null>",
  "disclaimer": "<string>"
}
```

---

# 9. Changelog

| Version | Change |
|---|---|
| v1.0 | Initial Mistral consultation + LocationIQ doctor finder |
| v1.1 | PubMed RAG pipeline (`chatbot/pubmed_rag.py`) — live citation grounding |
| v1.2 | Multi-turn conversation memory (`chat_history` param, last 10 turns) |
| v1.3 | Frontend rebuilt as proper chat UI with `st.chat_input` + citation expanders |
| v1.4 | API key removed from frontend — server-side `.env` only |
| v1.5 | Citations collapsed by default (`📚 N source(s)` toggle) |