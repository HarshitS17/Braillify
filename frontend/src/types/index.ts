// Health check
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

// Project
export type ProjectStatus = 'created' | 'processing' | 'review' | 'completed' | 'error';

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  page_count: number;
}

// Coordinate system
export type CoordinateUnit = 'px' | 'mm' | 'cm';

export interface Point {
  x: number;
  y: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  unit: CoordinateUnit;
}

export interface Canvas {
  width: number;
  height: number;
  unit: CoordinateUnit;
}

// Diagram
export type DiagramStatus = 
  | 'candidate' | 'selected' | 'extracted' | 'vectorized'
  | 'simplified' | 'labeled' | 'validated' | 'exported' | 'error';

export type ElementType = 
  | 'line' | 'polyline' | 'polygon' | 'circle' | 'ellipse'
  | 'arc' | 'curve' | 'arrow' | 'text_region' | 'boundary' | 'filled_region';

export type SemanticRole = 
  | 'boundary' | 'label' | 'arrow' | 'connector'
  | 'structure' | 'decoration' | 'unknown';

export interface DiagramElement {
  id: string;
  type: ElementType;
  geometry: Record<string, unknown>;
  unit: CoordinateUnit;
  semantic_role: SemanticRole;
  confidence: number;
  metadata: Record<string, unknown>;
}

export interface DetectionFeatures {
  edge_density: number;
  text_density: number;
  component_density: number;
  contour_count: number;
  has_enclosed_regions: boolean;
}

export interface DiagramCandidate {
  id: string;
  bbox: BoundingBox;
  confidence: number;
  features: DetectionFeatures;
  classification_reason: string;
  accepted: boolean;
  rejected: boolean;
}

// Label
export interface LeaderLine {
  start: Point;
  end: Point;
}

export interface LabelPlacement {
  position: Point;
  width: number;
  height: number;
  rotation: number;
  leader_line: LeaderLine | null;
  placement_score: number;
  is_manual: boolean;
}

export interface BrailleRepresentation {
  braille_unicode: string;
  braille_dots: string;
  grade: number;
  language: string;
}

export interface Label {
  id: string;
  diagram_id: string;
  target_component_id: string | null;
  target_element_id: string | null;
  text: string;
  braille: BrailleRepresentation;
  source: 'ocr' | 'manual' | 'generated';
  ocr_confidence: number | null;
  placement: LabelPlacement | null;
  metadata: Record<string, unknown>;
}

// Diagram (full)
export interface Diagram {
  id: string;
  project_id: string;
  page_id: string;
  status: DiagramStatus;
  source_bbox: BoundingBox | null;
  canvas: Canvas | null;
  elements: DiagramElement[];
  labels: string[];
  processing_log: string[];
}

// Validation
export type ValidationLevel = 'error' | 'warning' | 'suggestion';

export interface ValidationMessage {
  id: string;
  level: ValidationLevel;
  message: string;
  element_ids: string[];
  label_ids: string[];
}

export interface ValidationResult {
  errors: ValidationMessage[];
  warnings: ValidationMessage[];
  suggestions: ValidationMessage[];
}

// Export
export type PhysicalUnit = 'mm' | 'cm' | 'in';

export interface ExportConfig {
  width: number;
  height: number;
  unit: PhysicalUnit;
  include_metadata: boolean;
  stroke_width_mm: number;
}

// API Error
export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}
