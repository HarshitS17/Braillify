import React from 'react';
import type { EditorTool } from '../../hooks/useEditorState';

interface ToolConfig {
  id: EditorTool;
  name: string;
  shortcut: string;
  icon: React.ReactNode;
}

const getIcon = (id: string) => {
  switch (id) {
    case 'select': return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" /></svg>;
    case 'move': return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>;
    case 'label': return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" /></svg>;
    case 'draw_line': return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>;
    case 'draw_rect': return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>;
    default: return <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" /></svg>;
  }
};

const tools: ToolConfig[] = [
  { id: 'select', name: 'Select', shortcut: 'V', icon: getIcon('select') },
  { id: 'move', name: 'Move', shortcut: 'G', icon: getIcon('move') },
  { id: 'label', name: 'Label', shortcut: 'T', icon: getIcon('label') },
  { id: 'draw_line', name: 'Line', shortcut: 'L', icon: getIcon('draw_line') },
  { id: 'draw_rect', name: 'Rectangle', shortcut: 'R', icon: getIcon('draw_rect') },
];

interface ToolPanelProps {
  activeTool: EditorTool;
  onSetTool: (tool: EditorTool) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
}

export default function ToolPanel({
  activeTool,
  onSetTool,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
}: ToolPanelProps) {
  return (
    <div className="p-3 border-b border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-bold text-slate-800 tracking-wider uppercase">Tools</p>
        <div className="flex gap-1">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className="w-6 h-6 flex items-center justify-center rounded text-slate-500 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            title="Undo (Ctrl+Z)"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className="w-6 h-6 flex items-center justify-center rounded text-slate-500 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            title="Redo (Ctrl+Y)"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" /></svg>
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-1.5">
        {tools.map(t => (
          <button
            key={t.id}
            onClick={() => onSetTool(t.id)}
            className={`px-2 py-2 rounded-lg text-xs flex flex-col items-center justify-center gap-1.5 transition-all ${
              activeTool === t.id
                ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-sm border border-indigo-100'
                : 'hover:bg-slate-50 text-slate-600 border border-transparent'
            }`}
            title={`${t.name} (${t.shortcut})`}
          >
            {t.icon}
            <div className="flex items-center gap-1">
              <span>{t.name}</span>
              <span className={`text-[9px] font-mono rounded px-1 ${activeTool === t.id ? 'bg-indigo-100 text-indigo-500' : 'bg-slate-100 text-slate-400'}`}>{t.shortcut}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}