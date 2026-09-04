import type { LayerConfig } from '../../hooks/useEditorState';

interface LayerPanelProps {
  layers: LayerConfig[];
  onToggleLayer: (layerId: string) => void;
  onSetOpacity: (layerId: string, opacity: number) => void;
}

export default function LayerPanel({ layers, onToggleLayer, onSetOpacity }: LayerPanelProps) {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-3 border-b border-slate-200 sticky top-0 bg-white z-10">
        <p className="text-xs font-bold text-slate-800 tracking-wider uppercase">Layers</p>
      </div>
      <div className="p-2 space-y-1">
        {layers.map(layer => (
          <div 
            key={layer.id} 
            className={`p-2 rounded-lg transition-colors ${layer.visible ? 'bg-slate-50' : 'bg-transparent opacity-60 grayscale'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <label className="flex items-center gap-2.5 text-sm cursor-pointer font-medium text-slate-700 flex-1">
                <div 
                  className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${layer.visible ? 'bg-indigo-500 border-indigo-500' : 'border-slate-300 bg-white'}`}
                  onClick={(e) => { e.preventDefault(); onToggleLayer(layer.id); }}
                >
                  {layer.visible && (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
                <span className="select-none">{layer.name}</span>
              </label>
            </div>
            
            {layer.visible && (
              <div className="flex items-center gap-3 pl-6 pr-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={layer.opacity}
                  onChange={e => onSetOpacity(layer.id, parseInt(e.target.value))}
                  className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
                <span className="text-[10px] font-mono text-slate-500 w-6 text-right">{layer.opacity}%</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}