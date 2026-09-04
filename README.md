# TactileEd — Textbook Diagram-to-Embossable Tactile Graphic Converter

An academic computer vision + accessibility engineering project that converts scanned textbook pages containing diagrams into simplified tactile graphics suitable for visually impaired students, compatible with tactile/embossing workflows.

**Supervisor**: Anupam Sharma (E17312)

> **Academic Disclaimer**: This is a university engineering project. It prioritizes correctness, explainability, and deterministic processing over visual polish. Every major algorithm is designed to be explainable in a project viva.

---

## Problem Statement

Visually impaired students cannot access the diagrams in their textbooks. Existing solutions require manual redrawing by trained specialists — a slow, expensive process that limits educational access.

TactileEd automates the conversion pipeline: it detects diagram regions on scanned textbook pages, extracts and vectorizes them, simplifies the geometry for tactile perception, generates Braille labels with collision-free placement, and exports embosser-ready SVG/PDF files — with human-in-the-loop correction at every stage.

## Core Deliverables (Supervisor-Approved)

| # | Deliverable | Description |
|---|---|---|
| 1 | **Diagram-region detector** | Separates diagrams from body text on a scanned textbook page |
| 2 | **Simplifier** | Converts detected diagrams into clean, embossable line art (removing shading/gradients/fine detail) |
| 3 | **Braille labels** | Auto-generates Braille labels for diagram parts, positioned without overlap |
| 4 | **SVG/PDF export** | Exports to embosser-ready formats with physical dimensions |

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12+, FastAPI, Pydantic, OpenCV, NumPy, Pillow, scikit-image, Shapely |
| Vectorization | OpenCV `findContours` + `approxPolyDP` (contour-to-polygon) |
| Braille | Pure-Python Grade 1 Braille (liblouis as optional upgrade path) |
| SVG/PDF | svgwrite, ReportLab, CairoSVG |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Testing | pytest, pytest-asyncio, TypeScript strict mode |
| Infrastructure | Docker, docker-compose |
| Storage | Filesystem + JSON metadata (no database required) |

## Processing Pipeline

```
Textbook Page Image / PDF
  ↓ Preprocessing (grayscale, threshold, deskew, denoise)
  ↓ Page Layout Analysis
  ↓ Diagram Region Detection → ranked candidates
  ↓ Human Selection (accept/reject/draw/resize/merge)
  ↓ Diagram Extraction
  ↓ Image Structure Analysis (edges, contours, lines, circles)
  ↓ Vectorization (contour → polygon/circle/line)
  ↓ Tactile Simplification (Douglas-Peucker, min-feature filtering)
  ↓ Component Detection (heuristic + OCR)
  ↓ Label Extraction + Braille Translation
  ↓ Collision-Free Label Placement
  ↓ Human Review / Editing
  ↓ Validation (min line width, min gap, collisions, bounds)
  ↓ SVG / PDF Export
```

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker (optional)

### Backend Setup
```bash
cd TextileEd
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run the server
cd backend
uvicorn app.main:app --reload

# Verify
curl http://localhost:8000/health
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Docker Setup
```bash
cp .env.example .env
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Run Tests
```bash
# Backend
source .venv/bin/activate
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm run build
```

## API Endpoints

| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/health` | System health check | ✅ Active |
| `POST` | `/api/projects` | Create project | ✅ Active |
| `GET` | `/api/projects` | List projects | ✅ Active |
| `GET` | `/api/projects/{id}` | Get project | ✅ Active |
| `DELETE` | `/api/projects/{id}` | Delete project | ✅ Active |
| `POST` | `/api/projects/{id}/pages` | Upload page | 🔜 Phase 1 |
| `POST` | `/api/pages/{id}/preprocess` | Preprocess page | 🔜 Phase 1 |
| `POST` | `/api/pages/{id}/detect-diagrams` | Detect diagrams | 🔜 Phase 2 |
| `POST` | `/api/diagrams/{id}/vectorize` | Vectorize diagram | 🔜 Phase 5 |
| `POST` | `/api/diagrams/{id}/export/svg` | Export SVG | 🔜 Phase 12 |

## Project Structure

```
TextileEd/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── api/                 # API route handlers
│   │   │   ├── routes_projects.py
│   │   │   ├── routes_upload.py
│   │   │   ├── routes_processing.py
│   │   │   └── routes_export.py
│   │   ├── core/                # Config, logging, exceptions
│   │   ├── models/              # Pydantic domain models
│   │   │   ├── project.py
│   │   │   ├── page.py
│   │   │   ├── diagram.py       # Core intermediate representation
│   │   │   ├── component.py
│   │   │   └── label.py
│   │   ├── pipeline/            # Processing algorithms (Phase 1+)
│   │   ├── services/
│   │   └── utils/
│   ├── spikes/                  # Technical spike scripts
│   ├── tests/                   # pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── services/            # API client
│   │   └── types/               # TypeScript type definitions
│   └── package.json
├── data/
│   ├── samples/                 # Test images and spike outputs
│   ├── fixtures/                # Test fixture datasets
│   └── outputs/                 # Generated outputs
├── docs/                        # Project documentation
├── docker/                      # Dockerfiles
├── docker-compose.yml
└── README.md
```

## Design Principles

1. **Intermediate Domain Representation** — The SVG is NOT the source of truth. A structured JSON representation (Project → Page → Diagram → Elements → Labels) allows editing, validation, re-rendering, and debugging.

2. **Explicit Coordinate Systems** — Every coordinate-bearing field declares its unit (px, mm, cm). Pixel and physical coordinates are never mixed without explicit logged conversion.

3. **Human-in-the-Loop** — Automatic detection assists humans; it does not replace them. Manual correction is a first-class feature at every pipeline stage.

4. **Deterministic Processing** — Algorithms use fixed seeds and explicit parameters. The same input with the same configuration must produce the same output.

5. **Debuggability** — Every pipeline stage can emit debug artifacts (images, intermediate SVGs, logs).

## Current Status (Phase 0 Complete)

- ✅ Backend: FastAPI app with health check, CORS, structured logging, error handling
- ✅ Domain models: Project, Page, Diagram (with intermediate representation), Component, Label
- ✅ API: Project CRUD (in-memory)
- ✅ Frontend: React + TypeScript + Vite + Tailwind with backend connectivity check
- ✅ Spike: OpenCV vectorization validated (3/3 shapes detected correctly)
- ✅ Spike: Braille fallback working (liblouis unavailable natively, pure-Python Grade 1 fallback operational)
- ✅ Tests: 19/19 passing
- ✅ Documentation: Architecture, algorithms, API, development guide, tactile design guidelines

## Limitations

- Phase 0: No image processing pipeline yet — only the foundation and validated spikes.
- Braille: Only Grade 1 (uncontracted) English is supported via the fallback. Grade 2 requires liblouis.
- Vectorization: Contour-to-polygon works well for solid shapes; performance on complex diagrams with gradients/textures requires Phase 4-6 work.
- No persistence: Project data is in-memory only (filesystem persistence planned).

## Future Work

See the phased development plan for upcoming work:
- Phase 1: Input preprocessing
- Phase 2: Diagram region detection
- Phase 3-6: Extraction, structure analysis, vectorization, tactile simplification
- Phase 7-10: Semantic detection, OCR, Braille translation, label placement
- Phase 11-13: Validation, SVG/PDF export
- Phase 14: Interactive editor with human-in-the-loop editing
