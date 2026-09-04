import { useState } from 'react';
import type { DiagramElement, Label } from '../../types';

interface PropertiesPanelProps {
  selectedId: string | null;
  selectedType: 'element' | 'label' | null;
  elements: DiagramElement[];
  labels: Label[];
  onUpdateLabel: (labelId: string, updates: Partial<Label>) => void;
  onDeleteSelected: () => void;
}

export default function PropertiesPanel({
  selectedId, selectedType, elements, labels, onUpdateLabel, onDeleteSelected,
}: PropertiesPanelProps) {
  const [editText, setEditText] = useState('');

  if (!selectedId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-slate-400 text-center border-b border-slate-200">
        <svg className="w-8 h-8 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
        </svg>
        <p className="text-sm font-medium">No selection</p>
        <p className="text-xs mt-1">Select an element to view properties</p>
      </div>
    );
  }

  if (selectedType === 'element') {
    const el = elements.find(e => e.id === selectedId);
    if (!el) return null;
    return (
      <div className="flex-1 overflow-y-auto border-b border-slate-200">
        <div className="p-3 border-b border-slate-200 sticky top-0 bg-white z-10 flex items-center justify-between">
          <p className="text-xs font-bold text-slate-800 tracking-wider uppercase">Element</p>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">{el.id.slice(0, 8)}</span>
        </div>
        
        <div className="p-4 space-y-5">
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Type</label>
            <div className="text-sm font-medium text-slate-900 capitalize">{el.type}</div>
          </div>
          
          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Detection Confidence</label>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${el.confidence > 0.8 ? 'bg-emerald-500' : el.confidence > 0.5 ? 'bg-amber-500' : 'bg-slate-400'}`}
                  style={{ width: `${el.confidence * 100}%` }}
                />
              </div>
              <span className="text-xs font-mono text-slate-600 w-8 text-right">{(el.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Geometry Data</label>
            <div className="bg-slate-50 border border-slate-200 rounded-md p-2 max-h-40 overflow-y-auto">
              <pre className="text-[10px] font-mono text-slate-600 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(el.geometry, null, 2)}
              </pre>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={onDeleteSelected}
              className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-md transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Element
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (selectedType === 'label') {
    const lbl = labels.find(l => l.id === selectedId);
    if (!lbl) return null;

    const handleSave = () => {
      if (editText.trim()) {
        onUpdateLabel(lbl.id, { text: editText, source: 'manual' });
      }
    };

    return (
      <div className="flex-1 overflow-y-auto border-b border-slate-200">
        <div className="p-3 border-b border-slate-200 sticky top-0 bg-white z-10 flex items-center justify-between">
          <p className="text-xs font-bold text-slate-800 tracking-wider uppercase">Label</p>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">{lbl.id.slice(0, 8)}</span>
        </div>
        
        <div className="p-4 space-y-6">
          
          {/* Text Editing */}
          <div>
            <label htmlFor="label-text-input" className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">Text Content</label>
            <div className="flex gap-2">
              <input
                id="label-text-input"
                key={lbl.id + ':' + lbl.text}
                type="text"
                defaultValue={lbl.text}
                onChange={e => setEditText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleSave(); }}
                className="flex-1 border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                placeholder="Label text..."
              />
              <button
                onClick={handleSave}
                disabled={!editText.trim()}
                className="bg-indigo-600 text-white px-3 py-1.5 rounded-md text-xs font-medium hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                Save
              </button>
            </div>
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-[10px] font-medium text-slate-400 capitalize">Source: {lbl.source}</span>
              {lbl.ocr_confidence != null && (
                <span className="text-[10px] font-medium text-slate-400">OCR: {(lbl.ocr_confidence * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>

          {/* Braille Translation */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3">
            <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-2 flex items-center gap-1.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
              Braille Translation
            </label>
            <div className="text-2xl text-indigo-900 tracking-widest mb-1">{lbl.braille?.braille_unicode || '—'}</div>
            <div className="text-xs font-mono text-indigo-500/70">{lbl.braille?.braille_dots || 'No dots mapped'}</div>
          </div>

          {/* Placement Data */}
          {lbl.placement && (
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">Placement Metrics</label>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-50 border border-slate-200 rounded p-2 text-center">
                  <div className="text-[10px] text-slate-400 font-bold mb-0.5">X</div>
                  <div className="font-mono text-slate-700">{lbl.placement.position.x.toFixed(1)}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-2 text-center">
                  <div className="text-[10px] text-slate-400 font-bold mb-0.5">Y</div>
                  <div className="font-mono text-slate-700">{lbl.placement.position.y.toFixed(1)}</div>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded p-2 text-center col-span-2 flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 font-bold">COLLISION SCORE</span>
                  <span className="font-mono text-slate-700">{lbl.placement.placement_score.toFixed(2)}</span>
                </div>
              </div>
              {lbl.placement.leader_line && (
                <div className="mt-2 text-[10px] font-medium text-indigo-600 bg-indigo-50 py-1 px-2 rounded inline-flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Leader line attached
                </div>
              )}
            </div>
          )}

          <div className="pt-2 border-t border-slate-100">
            <button
              onClick={onDeleteSelected}
              className="w-full flex items-center justify-center gap-2 py-2 text-xs font-medium text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-md transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Label
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
