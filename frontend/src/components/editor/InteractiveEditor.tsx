import { useState, useCallback, useEffect, useRef } from 'react';
import type { DiagramElement, Label } from '../../types';
import { useEditorState } from '../../hooks/useEditorState';
import { apiClient } from '../../services/api';
import Canvas from './Canvas';
import PropertiesPanel from './PropertiesPanel';
import ValidationPanel from './ValidationPanel';
import LayerPanel from './LayerPanel';
import ToolPanel from './ToolPanel';
import ZoomControls from './ZoomControls';
import PipelineBar from './PipelineBar';

type SaveState = 'saved' | 'saving' | 'error';

interface InteractiveEditorProps {
  projectId: string;
  pageId: string;
  diagramId: string;
  initialElements: DiagramElement[];
  initialLabels: Label[];
  canvasWidth: number;
  canvasHeight: number;
}

export default function InteractiveEditor({
  projectId, pageId, diagramId,
  initialElements, initialLabels,
  canvasWidth, canvasHeight,
}: InteractiveEditorProps) {
  const editor = useEditorState();
  const [statusMsg, setStatusMsg] = useState('Ready');
  const [diagram, setDiagram] = useState<{ status?: string } | null>(null);
  const [saveState, setSaveState] = useState<SaveState>('saved');

  const stateRef = useRef({ elements: editor.elements, labels: editor.labels });
  stateRef.current = { elements: editor.elements, labels: editor.labels };
  const syncedRef = useRef<{ labels: string | null; elements: string | null }>({ labels: null, elements: null });
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const keysOf = (s: { elements: DiagramElement[]; labels: Label[] }) => ({
    labels: JSON.stringify(s.labels),
    elements: JSON.stringify(s.elements),
  });

  const doSync = useCallback(async (): Promise<boolean> => {
    const snapshot = stateRef.current;
    const keys = keysOf(snapshot);
    if (syncedRef.current.labels === keys.labels && syncedRef.current.elements === keys.elements) return true;
    setSaveState('saving');
    try {
      const ops: Promise<unknown>[] = [];
      if (syncedRef.current.labels !== keys.labels) {
        ops.push(
          apiClient.replaceLabels(projectId, pageId, diagramId, snapshot.labels).then(() => { syncedRef.current.labels = keys.labels; })
        );
      }
      if (syncedRef.current.elements !== keys.elements) {
        ops.push(
          apiClient.updateDiagramElements(projectId, pageId, diagramId, snapshot.elements).then(() => { syncedRef.current.elements = keys.elements; })
        );
      }
      await Promise.all(ops);
      setSaveState('saved');
      return true;
    } catch (err) {
      console.error('Failed to persist edits to backend:', err);
      setSaveState('error');
      return false;
    }
  }, [projectId, pageId, diagramId]);

  useEffect(() => {
    if (syncedRef.current.labels === null) return;
    const keys = keysOf({ elements: editor.elements, labels: editor.labels });
    if (syncedRef.current.labels === keys.labels && syncedRef.current.elements === keys.elements) return;
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => { void doSync(); }, 400);
    return () => { if (syncTimerRef.current) clearTimeout(syncTimerRef.current); };
  }, [editor.elements, editor.labels, doSync]);

  const flushSave = useCallback(async (): Promise<boolean> => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    return doSync();
  }, [doSync]);

  useEffect(() => {
    (async () => {
      try {
        const [data, labels] = await Promise.all([
          apiClient.getDiagram(projectId, pageId, diagramId),
          apiClient.getLabels(projectId, pageId, diagramId),
        ]);
        setDiagram(data);
        editor.loadDiagram(data.elements || [], labels || []);
        syncedRef.current = keysOf({ elements: data.elements || [], labels: labels || [] });
      } catch (err) {
        console.error('Failed to load diagram:', err);
        editor.loadDiagram(initialElements, initialLabels);
        syncedRef.current = keysOf({ elements: initialElements, labels: initialLabels });
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleValidation = useCallback(async () => {
    editor.setValidating(true);
    setStatusMsg('Running validation...');
    try {
      const result = await apiClient.runValidation(projectId, pageId, diagramId);
      editor.setValidationResult(result);
      const total = result.errors.length + result.warnings.length + result.suggestions.length;
      setStatusMsg(total === 0 ? 'Validation passed' : total + ' issue(s) found');
    } catch (err) {
      setStatusMsg('Validation failed');
    } finally {
      editor.setValidating(false);
    }
  }, [projectId, pageId, diagramId, editor]);

  const triggerDownload = useCallback((blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }, []);

  const handleUpdateLabel = useCallback((labelId: string, updates: Partial<Label>) => {
    editor.pushHistory(editor.elements, editor.labels);
    if (typeof updates.text === 'string') {
      apiClient
        .updateLabel(projectId, pageId, diagramId, labelId, { text: updates.text })
        .then((serverLabel) => {
          editor.updateLabel(labelId, { text: serverLabel.text, braille: serverLabel.braille, source: serverLabel.source });
          setStatusMsg(`Label updated (Braille re-translated)`);
        })
        .catch((err) => {
          console.error('Failed to persist label text, will retry via sync:', err);
          editor.updateLabel(labelId, updates);
          setSaveState('error');
          setStatusMsg('Save failed — will retry on next change');
        });
    } else {
      editor.updateLabel(labelId, updates);
    }
  }, [editor, projectId, pageId, diagramId]);

  const handleDeleteSelected = useCallback(() => {
    if (!editor.selectedId) return;
    editor.pushHistory(editor.elements, editor.labels);
    editor.deleteSelected();
    setStatusMsg('Deleted — saving…');
    void flushSave().then((ok) => { if (ok) setStatusMsg('Deleted and saved'); });
  }, [editor, flushSave]);

  const handleUndo = useCallback(() => {
    editor.undo();
    setStatusMsg('Undo — syncing…');
  }, [editor]);

  const handleRedo = useCallback(() => {
    editor.redo();
    setStatusMsg('Redo — syncing…');
  }, [editor]);

  const handleLabelDragEnd = useCallback(() => {
    void flushSave();
  }, [flushSave]);

  const handleExportSvg = useCallback(async () => {
    setStatusMsg('Saving changes…');
    const saved = await flushSave();
    if (!saved) {
      setStatusMsg('SVG export cancelled — changes failed to save.');
      return;
    }
    setStatusMsg('Exporting SVG...');
    try {
      const blob = await apiClient.exportSvg(projectId, pageId, diagramId);
      triggerDownload(blob, 'diagram_' + diagramId + '.svg');
      setStatusMsg('SVG exported');
    } catch (err) {
      setStatusMsg('SVG export failed');
    }
  }, [projectId, pageId, diagramId, triggerDownload, flushSave]);

  const handleExportPdf = useCallback(async () => {
    setStatusMsg('Saving changes…');
    const saved = await flushSave();
    if (!saved) {
      setStatusMsg('PDF export cancelled — changes failed to save.');
      return;
    }
    setStatusMsg('Exporting PDF...');
    try {
      const blob = await apiClient.exportPdf(projectId, pageId, diagramId);
      triggerDownload(blob, 'diagram_' + diagramId + '.pdf');
      setStatusMsg('PDF exported');
    } catch (err) {
      setStatusMsg('PDF export failed');
    }
  }, [projectId, pageId, diagramId, triggerDownload, flushSave]);

  const handleZoomIn = useCallback(() => { editor.setZoom(editor.view.zoom * 1.2); }, [editor]);
  const handleZoomOut = useCallback(() => { editor.setZoom(editor.view.zoom / 1.2); }, [editor]);
  const handleResetView = useCallback(() => { editor.setZoom(1); }, [editor]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) { e.preventDefault(); editor.undo(); }
      if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); editor.redo(); }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA' && editor.selectedId) {
          handleDeleteSelected();
        }
      }
      if (e.key === '=' || e.key === '+') handleZoomIn();
      if (e.key === '-') handleZoomOut();
      if (e.key === '0') handleResetView();
      if (e.key === 'v' || e.key === 'V') editor.setTool('select');
      if (e.key === 'g' || e.key === 'G') editor.setTool('move');
      if (e.key === 't' || e.key === 'T') editor.setTool('label');
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [editor, handleZoomIn, handleZoomOut, handleResetView, handleDeleteSelected, handleUndo, handleRedo]);

  const getCompletedStages = (): string[] => {
    if (!diagram?.status) return [];
    const stageOrder = ['extracted', 'vectorized', 'simplified', 'labeled', 'validated', 'exported'];
    const currentIndex = stageOrder.indexOf(diagram.status);
    if (currentIndex <= 0) return [];
    return stageOrder.slice(0, currentIndex);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Top Toolbar */}
      <div className="bg-white px-4 py-2 border-b border-slate-200 flex items-center justify-between shrink-0 shadow-sm z-10">
        <PipelineBar currentStage={diagram?.status} completedStages={getCompletedStages()} />
        <div className="flex items-center gap-2 ml-4">
          <button onClick={handleExportSvg} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium text-xs rounded transition-colors border border-indigo-200">Export SVG</button>
          <button onClick={handleExportPdf} className="px-3 py-1.5 bg-indigo-600 text-white hover:bg-indigo-700 font-medium text-xs rounded transition-colors shadow-sm">Export PDF</button>
        </div>
      </div>
      
      {/* Editor Workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: Tools & Layers */}
        <div className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 z-10 shadow-sm">
          <ToolPanel activeTool={editor.activeTool} onSetTool={editor.setTool} canUndo={editor.canUndo} canRedo={editor.canRedo} onUndo={handleUndo} onRedo={handleRedo} />
          <LayerPanel layers={editor.layers} onToggleLayer={editor.toggleLayer} onSetOpacity={editor.setLayerOpacity} />
        </div>
        
        {/* Center Pane: Canvas */}
        <div className="flex-1 overflow-hidden bg-slate-100 relative shadow-inner">
          <Canvas elements={editor.elements} labels={editor.labels} selectedId={editor.selectedId} canvasWidth={canvasWidth} canvasHeight={canvasHeight} layers={editor.layers} zoom={editor.view.zoom} panX={editor.view.panX} panY={editor.view.panY} onSelect={editor.select} onMoveLabel={editor.moveLabel} onPushHistory={editor.pushHistory} onLabelDragEnd={handleLabelDragEnd} />
        </div>
        
        {/* Right Pane: Properties & Validation */}
        <div className="w-72 bg-white border-l border-slate-200 flex flex-col shrink-0 z-10 shadow-sm">
          <PropertiesPanel selectedId={editor.selectedId} selectedType={editor.selectedType} elements={editor.elements} labels={editor.labels} onUpdateLabel={handleUpdateLabel} onDeleteSelected={handleDeleteSelected} />
          <ValidationPanel result={editor.validationResult} loading={editor.isValidating} onRunValidation={handleValidation} />
        </div>
      </div>
      
      {/* Status Bar */}
      <div className="h-8 bg-white text-slate-500 text-xs flex items-center px-4 gap-6 border-t border-slate-200 shrink-0">
        <span className="flex-1 font-medium" role="status" aria-live="polite">{statusMsg}</span>
        
        <button
          type="button"
          onClick={() => { if (saveState === 'error') { setStatusMsg('Retrying save…'); void flushSave().then((ok) => setStatusMsg(ok ? 'Changes saved' : 'Save failed — check backend connection')); } }}
          disabled={saveState !== 'error'}
          title={saveState === 'error' ? 'Click to retry saving your changes' : `Save state: ${saveState}`}
          className={
            'flex items-center gap-1.5 px-2 py-0.5 rounded font-medium ' +
            (saveState === 'saved' ? 'text-emerald-600 cursor-default'
              : saveState === 'saving' ? 'text-amber-600 cursor-wait'
              : 'text-rose-600 cursor-pointer bg-rose-50 hover:bg-rose-100 transition-colors')
          }
        >
          <span className={`w-1.5 h-1.5 rounded-full ${saveState === 'saved' ? 'bg-emerald-500' : saveState === 'saving' ? 'bg-amber-500 animate-pulse' : 'bg-rose-500'}`}></span>
          {saveState === 'saved' ? 'Saved' : saveState === 'saving' ? 'Saving...' : 'Save failed - retry'}
        </button>
        
        <div className="flex items-center gap-4 text-slate-400 font-mono">
          <span>{editor.elements.length} elm</span>
          <span>{editor.labels.length} lbl</span>
          <span className="capitalize">{editor.activeTool}</span>
        </div>
        
        <div className="ml-2 pl-4 border-l border-slate-200 h-4 flex items-center">
          <ZoomControls zoom={editor.view.zoom} onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} onResetView={handleResetView} />
        </div>
      </div>
    </div>
  );
}
