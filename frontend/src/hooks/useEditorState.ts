import { useState, useCallback } from 'react';
import type { DiagramElement, Label } from '../types';

export type EditorTool = 'select' | 'move' | 'label' | 'draw_line' | 'draw_rect';

export interface LayerConfig {
  id: string;
  name: string;
  visible: boolean;
  opacity: number;
}

interface EditorSnapshot {
  elements: DiagramElement[];
  labels: Label[];
}

export interface ValidationMessage {
  id: string;
  level: 'error' | 'warning' | 'suggestion';
  message: string;
  element_ids: string[];
  label_ids: string[];
}

export interface ValidationResult {
  errors: ValidationMessage[];
  warnings: ValidationMessage[];
  suggestions: ValidationMessage[];
}

interface EditorState {
  elements: DiagramElement[];
  labels: Label[];
  selectedId: string | null;
  selectedType: 'element' | 'label' | null;
  activeTool: EditorTool;
  /** Past states (deep-copied snapshots taken BEFORE each mutation). */
  history: EditorSnapshot[];
  /** Index of the most recent past state in `history`. */
  historyIndex: number;
  /** States undone by the user, ready to be re-applied by redo. */
  redoStack: EditorSnapshot[];
  layers: LayerConfig[];
  view: { zoom: number; panX: number; panY: number };
  validationResult: ValidationResult | null;
  isValidating: boolean;
}

const defaultLayers: LayerConfig[] = [
  { id: 'original', name: 'Original Image', visible: true, opacity: 30 },
  { id: 'geometry', name: 'Tactile Geometry', visible: true, opacity: 100 },
  { id: 'labels', name: 'Labels', visible: true, opacity: 100 },
  { id: 'grid', name: 'Grid', visible: false, opacity: 100 },
];

export function useEditorState() {
  const [state, setState] = useState<EditorState>({
    elements: [],
    labels: [],
    selectedId: null,
    selectedType: null,
    activeTool: 'select',
    history: [],
    historyIndex: -1,
    redoStack: [],
    layers: defaultLayers,
    view: { zoom: 1, panX: 0, panY: 0 },
    validationResult: null,
    isValidating: false,
  });

  const pushHistory = useCallback((elements: DiagramElement[], labels: Label[]) => {
    setState(prev => {
      const trimmed = prev.history.slice(0, prev.historyIndex + 1);
      const snapshot: EditorSnapshot = { elements: JSON.parse(JSON.stringify(elements)), labels: JSON.parse(JSON.stringify(labels)) };
      return { ...prev, history: [...trimmed, snapshot], historyIndex: trimmed.length };
    });
  }, []);

  const setElements = useCallback((elements: DiagramElement[]) => { setState(prev => ({ ...prev, elements })); }, []);
  const setLabels = useCallback((labels: Label[]) => { setState(prev => ({ ...prev, labels })); }, []);

  const loadDiagram = useCallback((elements: DiagramElement[], labels: Label[]) => {
    setState(prev => ({ ...prev, elements, labels, history: [{ elements: JSON.parse(JSON.stringify(elements)), labels: JSON.parse(JSON.stringify(labels)) }], historyIndex: 0, redoStack: [] }));
  }, []);

  const select = useCallback((id: string | null, type: 'element' | 'label' | null) => { setState(prev => ({ ...prev, selectedId: id, selectedType: type })); }, []);
  const setTool = useCallback((tool: EditorTool) => { setState(prev => ({ ...prev, activeTool: tool })); }, []);
  const setZoom = useCallback((zoom: number) => { setState(prev => ({ ...prev, view: { ...prev.view, zoom: Math.min(Math.max(zoom, 0.1), 10) } })); }, []);

  const toggleLayer = useCallback((layerId: string) => {
    setState(prev => ({ ...prev, layers: prev.layers.map(l => l.id === layerId ? { ...l, visible: !l.visible } : l) }));
  }, []);

  const setLayerOpacity = useCallback((layerId: string, opacity: number) => {
    setState(prev => ({ ...prev, layers: prev.layers.map(l => l.id === layerId ? { ...l, opacity } : l) }));
  }, []);

  const undo = useCallback(() => {
    setState(prev => {
      if (prev.historyIndex < 0 || prev.history.length === 0) return prev;
      // The undo target is the most recent past state.
      const target = prev.history[prev.historyIndex];
      if (!target) return prev;
      // Stash the current live state so redo can re-apply it.
      const redoEntry: EditorSnapshot = {
        elements: JSON.parse(JSON.stringify(prev.elements)),
        labels: JSON.parse(JSON.stringify(prev.labels)),
      };
      return {
        ...prev,
        elements: JSON.parse(JSON.stringify(target.elements)),
        labels: JSON.parse(JSON.stringify(target.labels)),
        historyIndex: prev.historyIndex - 1,
        redoStack: [...prev.redoStack, redoEntry],
      };
    });
  }, []);

  const redo = useCallback(() => {
    setState(prev => {
      if (prev.redoStack.length === 0) return prev;
      const next = prev.redoStack[prev.redoStack.length - 1];
      if (!next) return prev;
      return {
        ...prev,
        elements: JSON.parse(JSON.stringify(next.elements)),
        labels: JSON.parse(JSON.stringify(next.labels)),
        historyIndex: Math.min(prev.historyIndex + 1, prev.history.length - 1),
        redoStack: prev.redoStack.slice(0, -1),
      };
    });
  }, []);

  const updateLabel = useCallback((labelId: string, updates: Partial<Label>) => {
    setState(prev => ({ ...prev, labels: prev.labels.map(l => l.id === labelId ? { ...l, ...updates } : l) }));
  }, []);

  const moveLabel = useCallback((labelId: string, dx: number, dy: number) => {
    setState(prev => ({
      ...prev,
      labels: prev.labels.map(l => {
        if (l.id !== labelId || !l.placement) return l;
        return { ...l, placement: { ...l.placement, position: { x: l.placement.position.x + dx, y: l.placement.position.y + dy }, is_manual: true } };
      })
    }));
  }, []);

  const deleteSelected = useCallback(() => {
    setState(prev => {
      if (!prev.selectedId) return prev;
      if (prev.selectedType === 'element') return { ...prev, elements: prev.elements.filter(e => e.id !== prev.selectedId), selectedId: null, selectedType: null };
      if (prev.selectedType === 'label') return { ...prev, labels: prev.labels.filter(l => l.id !== prev.selectedId), selectedId: null, selectedType: null };
      return prev;
    });
  }, []);

  const setValidationResult = useCallback((result: ValidationResult | null) => { setState(prev => ({ ...prev, validationResult: result })); }, []);
  const setValidating = useCallback((validating: boolean) => { setState(prev => ({ ...prev, isValidating: validating })); }, []);

  return {
    ...state, setElements, setLabels, loadDiagram, select, setTool, setZoom, toggleLayer, setLayerOpacity,
    undo, redo, updateLabel, moveLabel, deleteSelected, pushHistory, setValidationResult, setValidating,
    canUndo: state.historyIndex >= 0 && state.history.length > 0,
    canRedo: state.redoStack.length > 0,
  };
}