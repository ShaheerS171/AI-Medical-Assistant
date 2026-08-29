# Medical Assistant Chatbot & Doctor Locator
## Technical Documentation & API Specification

---

# 1. System Overview

The Medical Assistant platform combines an AI-powered consultation engine with a healthcare facility discovery system.

The platform consists of two primary backend services exposed through FastAPI:

## 1. AI Medical Consultation Engine (`/consult`)

Provides symptom-based guidance and multimodal medical report analysis.

Supported inputs include:

- Plain-text symptom descriptions
- PDF medical reports
- Medical images (`.png`, `.jpg`, `.jpeg`)

The consultation engine uses:

- **Mistral OCR (`mistral-ocr-latest`)** for extracting text from PDFs
- **Pixtral Vision Model (`pixtral-12b-2409`)** for image understanding
- **Mistral Small (`mistral-small-latest`)** for text-based consultations

The service produces structured clinical guidance in JSON format.

---

## 2. Healthcare Locator Engine (`/find-doctors`)

Provides location-aware discovery of:

- Hospitals
- Clinics
- Medical practitioners
- Healthcare facilities

The service utilizes:

- LocationIQ Forward Geocoding API
- LocationIQ Nearby Places API
- Haversine distance calculations
- Deduplication and ranking logic

Users may search by:

```text
Rawalpindi
Islamabad
Satellite Town
Gulberg
Any city, area, landmark, or address
```

Optional specialty filtering is supported.

---

# 2. Environment Setup & Configuration

Create a `.env` file in the project root directory.

```env
# Mistral AI API Key
# Required for OCR, Vision Analysis, and Consultation Engine

MISTRAL_API_KEY=your_mistral_api_key_here

# LocationIQ API Key
# Required for Geocoding and Nearby Healthcare Searches

LOCATION_API_KEY=your_locationiq_api_key_here
```

---

# 3. Architecture & Data Flow

```text
[ User / Frontend ]
          │
          │
          ├────────────► POST /consult
          │                    │
          │                    ├── PDF Upload
          │                    │       │
          │                    │       └──► Mistral OCR API
          │                    │
          │                    ├── Image Upload
          │                    │       │
          │                    │       └──► Pixtral Vision Model
          │                    │
          │                    └── Symptoms Text
          │                            │
          │                            ▼
          │                    Mistral Chat Model
          │                            │
          │                            ▼
          │                    Structured JSON Advice
          │
          │
          └────────────► GET /find-doctors
                               │
                               ▼
                    LocationIQ Geocoder
                               │
                     Location → Lat/Lon
                               │
                               ▼
                    LocationIQ Nearby API
                               │
                               ▼
                     Healthcare Facilities
                               │
                               ▼
                    Distance Calculations
                               │
                               ▼
                  Deduplicate & Sort Results
                               │
                               ▼
                         JSON Response
```

---

# 4. API Endpoints Specification

---

# 4.1 Consultation Engine

## Endpoint

```http
POST /consult
```

Performs symptom consultation and multimodal document analysis.

### Content Type

```text
multipart/form-data
```

---

## Request Parameters

| Parameter | Type | Location | Required | Description |
|------------|--------|----------|-----------|-------------|
| symptoms | String | Form | No* | Plain-text symptom description |
| file | Binary | Form | No* | PDF or image file |
| api_key | String | Form | No | Runtime API key override |
| X-Mistral-Api-Key | String | Header | No | Runtime API key override |

> **Validation Rule:** At least one of `symptoms` or `file` must be provided.

---

## Example Request

```bash
curl -X POST \
  http://localhost:8000/consult \
  -F "symptoms=Persistent cough and mild fever"
```

---

## Response

### 200 OK

```json
{
  "advice": "The symptoms described suggest a mild respiratory irritation. Stay hydrated and rest.",
  "urgency": "low",
  "recommended_specialist": "General Physician",
  "disclaimer": "This is not a medical diagnosis. Please consult a licensed physician."
}
```

---

## Response Fields

| Field | Type | Description |
|----------|--------|-------------|
| advice | String | AI-generated medical guidance |
| urgency | String | low, medium, or high |
| recommended_specialist | String | Suggested healthcare specialist |
| disclaimer | String | Medical safety disclaimer |

---

# 4.2 Doctor & Facility Locator

## Endpoint

```http
GET /find-doctors
```

Searches nearby healthcare facilities using LocationIQ.

---

## Query Parameters

| Parameter | Type | Required | Default | Description |
|------------|--------|-----------|-----------|-------------|
| location | String | Yes | — | City, area, landmark, or address |
| specialty | String | No | null | Medical specialty filter |
| radius_km | Float | No | 15.0 | Search radius in kilometers |

---

## Example Request

```http
GET /find-doctors?location=Rawalpindi
```

---

## Example Response

### 200 OK

```json
{
  "results": [
    {
      "name": "Holy Family Hospital",
      "address": "Holy Family Road, Satellite Town, Rawalpindi, Punjab, Pakistan",
      "distance_km": 2.45,
      "lat": 33.6335,
      "lon": 73.0658
    },
    {
      "name": "AFIRM Clinic",
      "address": "Abid Majeed Road, Rawalpindi, Punjab, Pakistan",
      "distance_km": 4.12,
      "lat": 33.5932,
      "lon": 73.0551
    }
  ]
}
```

---

## Response Fields

| Field | Type | Description |
|----------|--------|-------------|
| name | String | Facility name |
| address | String | Full formatted address |
| distance_km | Float | Distance from requested location |
| lat | Float | Latitude |
| lon | Float | Longitude |

---

# 5. Core Engine Utility Functions (`chatbot/engine.py`)

---

## `run_consult_logic(...)`

Primary consultation workflow.

### Responsibilities

- Input validation
- PDF OCR extraction
- Image processing
- Prompt construction
- Mistral API communication
- Structured JSON parsing

### Workflow

```text
Input Validation
       │
       ▼
Extract PDF Text (OCR)
       │
       ▼
Process Images (Vision Model)
       │
       ▼
Generate Structured Prompt
       │
       ▼
Mistral Chat Completion
       │
       ▼
JSON Cleanup
       │
       ▼
Structured Response
```

### Internal Functions

#### `_ocr_pdf()`

Processes PDF reports through:

```text
mistral-ocr-latest
```

Returns extracted clinical text.

---

#### `_extract_json()`

Removes markdown artifacts:

````text
```json
...
```# Medical Assistant Chatbot & Doctor Locator
## Technical Documentation & API Specification

---

# 1. System Overview

The Medical Assistant platform combines an AI-powered consultation engine with a healthcare facility discovery system.

The platform consists of two primary backend services exposed through FastAPI:

## 1. AI Medical Consultation Engine (`/consult`)

Provides symptom-based guidance and multimodal medical report analysis.

Supported inputs include:

- Plain-text symptom descriptions
- PDF medical reports
- Medical images (`.png`, `.jpg`, `.jpeg`)

The consultation engine uses:

- **Mistral OCR (`mistral-ocr-latest`)** for extracting text from PDFs
- **Pixtral Vision Model (`pixtral-12b-2409`)** for image understanding
- **Mistral Small (`mistral-small-latest`)** for text-based consultations

The service produces structured clinical guidance in JSON format.

---

## 2. Healthcare Locator Engine (`/find-doctors`)

Provides location-aware discovery of:

- Hospitals
- Clinics
- Medical practitioners
- Healthcare facilities

The service utilizes:

- LocationIQ Forward Geocoding API
- LocationIQ Nearby Places API
- Haversine distance calculations
- Deduplication and ranking logic

Users may search by:

```text
Rawalpindi
Islamabad
Satellite Town
Gulberg
Any city, area, landmark, or address
```

Optional specialty filtering is supported.

---

# 2. Environment Setup & Configuration

Create a `.env` file in the project root directory.

```env
# Mistral AI API Key
# Required for OCR, Vision Analysis, and Consultation Engine

MISTRAL_API_KEY=your_mistral_api_key_here

# LocationIQ API Key
# Required for Geocoding and Nearby Healthcare Searches

LOCATION_API_KEY=your_locationiq_api_key_here
```

---

# 3. Architecture & Data Flow

```text
[ User / Frontend ]
          │
          │
          ├────────────► POST /consult
          │                    │
          │                    ├── PDF Upload
          │                    │       │
          │                    │       └──► Mistral OCR API
          │                    │
          │                    ├── Image Upload
          │                    │       │
          │                    │       └──► Pixtral Vision Model
          │                    │
          │                    └── Symptoms Text
          │                            │
          │                            ▼
          │                    Mistral Chat Model
          │                            │
          │                            ▼
          │                    Structured JSON Advice
          │
          │
          └────────────► GET /find-doctors
                               │
                               ▼
                    LocationIQ Geocoder
                               │
                     Location → Lat/Lon
                               │
                               ▼
                    LocationIQ Nearby API
                               │
                               ▼
                     Healthcare Facilities
                               │
                               ▼
                    Distance Calculations
                               │
                               ▼
                  Deduplicate & Sort Results
                               │
                               ▼
                         JSON Response
```

---

# 4. API Endpoints Specification

---

# 4.1 Consultation Engine

## Endpoint

```http
POST /consult
```

Performs symptom consultation and multimodal document analysis.

### Content Type

```text
multipart/form-data
```

---

## Request Parameters

| Parameter | Type | Location | Required | Description |
|------------|--------|----------|-----------|-------------|
| symptoms | String | Form | No* | Plain-text symptom description |
| file | Binary | Form | No* | PDF or image file |
| api_key | String | Form | No | Runtime API key override |
| X-Mistral-Api-Key | String | Header | No | Runtime API key override |

> **Validation Rule:** At least one of `symptoms` or `file` must be provided.

---

## Example Request

```bash
curl -X POST \
  http://localhost:8000/consult \
  -F "symptoms=Persistent cough and mild fever"
```

---

## Response

### 200 OK

```json
{
  "advice": "The symptoms described suggest a mild respiratory irritation. Stay hydrated and rest.",
  "urgency": "low",
  "recommended_specialist": "General Physician",
  "disclaimer": "This is not a medical diagnosis. Please consult a licensed physician."
}
```

---

## Response Fields

| Field | Type | Description |
|----------|--------|-------------|
| advice | String | AI-generated medical guidance |
| urgency | String | low, medium, or high |
| recommended_specialist | String | Suggested healthcare specialist |
| disclaimer | String | Medical safety disclaimer |

---

# 4.2 Doctor & Facility Locator

## Endpoint

```http
GET /find-doctors
```

Searches nearby healthcare facilities using LocationIQ.

---

## Query Parameters

| Parameter | Type | Required | Default | Description |
|------------|--------|-----------|-----------|-------------|
| location | String | Yes | — | City, area, landmark, or address |
| specialty | String | No | null | Medical specialty filter |
| radius_km | Float | No | 15.0 | Search radius in kilometers |

---

## Example Request

```http
GET /find-doctors?location=Rawalpindi
```

---

## Example Response

### 200 OK

```json
{
  "results": [
    {
      "name": "Holy Family Hospital",
      "address": "Holy Family Road, Satellite Town, Rawalpindi, Punjab, Pakistan",
      "distance_km": 2.45,
      "lat": 33.6335,
      "lon": 73.0658
    },
    {
      "name": "AFIRM Clinic",
      "address": "Abid Majeed Road, Rawalpindi, Punjab, Pakistan",
      "distance_km": 4.12,
      "lat": 33.5932,
      "lon": 73.0551
    }
  ]
}
```

---

## Response Fields

| Field | Type | Description |
|----------|--------|-------------|
| name | String | Facility name |
| address | String | Full formatted address |
| distance_km | Float | Distance from requested location |
| lat | Float | Latitude |
| lon | Float | Longitude |

---

# 5. Core Engine Utility Functions (`chatbot/engine.py`)

---

## `run_consult_logic(...)`

Primary consultation workflow.

### Responsibilities

- Input validation
- PDF OCR extraction
- Image processing
- Prompt construction
- Mistral API communication
- Structured JSON parsing

### Workflow

```text
Input Validation
       │
       ▼
Extract PDF Text (OCR)
       │
       ▼
Process Images (Vision Model)
       │
       ▼
Generate Structured Prompt
       │
       ▼
Mistral Chat Completion
       │
       ▼
JSON Cleanup
       │
       ▼
Structured Response
```

### Internal Functions

#### `_ocr_pdf()`

Processes PDF reports through:

```text
mistral-ocr-latest
```

Returns extracted clinical text.

---

#### `_extract_json()`

Removes markdown artifacts:

````text
```json
...
```