# Architecture

## System Overview
The full pipeline flows from a client request, through the FastAPI backend, into sequential processing stages, saving state into JSON metadata, and concluding with human validation on the frontend UI.

## Component Architecture
- **Backend**: FastAPI web server. Organized into routers, services, and pipeline components.
- **Frontend**: React SPA. Uses component-based architecture for the canvas editor and project management.

## Intermediate Domain Representation
Project → Page → Diagram → Elements → Labels.
This hierarchical JSON structure defines the state at every stage.

## Data Flow
Upload -> Raw Storage -> Pipeline Processing -> Metadata Generation -> Frontend Review -> Export.

## Coordinate System
- Uses explicit units.
- Distinguishes between internal pixel coordinates (px) and physical output dimensions (mm) for the embosser.

## Storage
- File system for raw/processed images.
- JSON files for metadata and intermediate representation.

## API Design Principles
- RESTful standards.
- Clear separation of concerns.

## Error Handling Strategy
- Standardized HTTP error responses.
- Backend logging and pipeline recovery mechanisms.

## Extension Points
- `SemanticDetector` interface to plug in new object detection models in the future.
