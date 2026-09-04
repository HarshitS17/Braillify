import React, { useState, useRef, MouseEvent } from 'react';
import { DiagramCandidate, BoundingBox } from '../types';

interface RegionEditorProps {
  imageUrl: string;
  initialCandidates: DiagramCandidate[];
  onSave: (candidates: DiagramCandidate[]) => void;
  onEditDiagram?: (diagramId: string) => void;
  imageWidth: number;
  imageHeight: number;
}

export const RegionEditor: React.FC<RegionEditorProps> = ({
  imageUrl,
  initialCandidates,
  onSave,
  onEditDiagram,
  imageWidth,
  imageHeight,
}) => {
  const [candidates, setCandidates] = useState<DiagramCandidate[]>(initialCandidates);
  const [drawing, setDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentBox, setCurrentBox] = useState<BoundingBox | null>(null);
  const [hoveredCandidateId, setHoveredCandidateId] = useState<string | null>(null);
  
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const getSvgCoordinates = (e: MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const CTM = svgRef.current.getScreenCTM();
    if (!CTM) return { x: 0, y: 0 };
    
    const pt = svgRef.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(CTM.inverse());
    
    return { x: svgP.x, y: svgP.y };
  };

  const handleMouseDown = (e: MouseEvent<SVGSVGElement>) => {
    if (e.button !== 0) return;
    const coords = getSvgCoordinates(e);
    setStartPoint(coords);
    setDrawing(true);
    setCurrentBox({
      x: coords.x,
      y: coords.y,
      width: 0,
      height: 0,
      unit: 'px'
    });
  };

  const handleMouseMove = (e: MouseEvent<SVGSVGElement>) => {
    if (!drawing || !startPoint) return;
    const coords = getSvgCoordinates(e);
    
    setCurrentBox({
      x: Math.min(startPoint.x, coords.x),
      y: Math.min(startPoint.y, coords.y),
      width: Math.abs(coords.x - startPoint.x),
      height: Math.abs(coords.y - startPoint.y),
      unit: 'px'
    });
  };

  const handleMouseUp = () => {
    if (!drawing || !currentBox) return;
    
    if (currentBox.width > 10 && currentBox.height > 10) {
      const newCandidate: DiagramCandidate = {
        id: crypto.randomUUID(),
        bbox: currentBox,
        confidence: 1.0,
        features: {
          edge_density: 0,
          text_density: 0,
          component_density: 0,
          contour_count: 0,
          has_enclosed_regions: false,
        },
        classification_reason: 'manual_draw',
        accepted: true,
        rejected: false,
      };
      setCandidates(prev => [...prev, newCandidate]);
    }
    
    setDrawing(false);
    setStartPoint(null);
    setCurrentBox(null);
  };

  const toggleAccept = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, accepted: !c.accepted, rejected: false } : c));
  };

  const toggleReject = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, rejected: !c.rejected, accepted: false } : c));
  };

  const deleteCandidate = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setCandidates(prev => prev.filter(c => c.id !== id));
  };

  // Sort candidates by Y coordinate for logical ordering
  const sortedCandidates = [...candidates].sort((a, b) => a.bbox.y - b.bbox.y);
  const acceptedCount = candidates.filter(c => c.accepted).length;

  return (
    <div className="flex h-full bg-slate-50 overflow-hidden text-slate-900 rounded-b-xl">
      
      {/* Left Sidebar: Candidates List */}
      <div className="w-80 border-r border-slate-200 bg-white flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900">Detected Regions</h3>
            <p className="text-xs text-slate-500 mt-1">{candidates.length} regions found • {acceptedCount} accepted</p>
          </div>
          <button 
            onClick={() => onSave(candidates)}
            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
            title="Save regions manually"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {sortedCandidates.length === 0 ? (
            <div className="text-center p-6 text-sm text-slate-500">
              No regions detected. Draw boxes on the image to create them manually.
            </div>
          ) : (
            sortedCandidates.map((c, i) => (
              <div 
                key={c.id}
                onMouseEnter={() => setHoveredCandidateId(c.id)}
                onMouseLeave={() => setHoveredCandidateId(null)}
                className={`p-3 rounded-lg border transition-all ${
                  hoveredCandidateId === c.id 
                    ? 'border-indigo-400 shadow-md bg-indigo-50/30' 
                    : c.accepted 
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : c.rejected
                        ? 'border-rose-200 bg-rose-50/30 opacity-60'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                      #{i + 1}
                    </span>
                    <span className="text-sm font-semibold truncate max-w-[120px]" title={c.classification_reason}>
                      {c.classification_reason.replace('_', ' ')}
                    </span>
                  </div>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                    c.confidence > 0.8 ? 'text-emerald-700 bg-emerald-100' : 
                    c.confidence > 0.5 ? 'text-amber-700 bg-amber-100' : 'text-slate-600 bg-slate-100'
                  }`}>
                    {(c.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div className="flex flex-col gap-2 mt-3">
                  <div className="grid grid-cols-2 gap-1.5">
                    <button 
                      onClick={(e) => toggleAccept(c.id, e)}
                      className={`py-1 text-xs font-medium rounded border transition-colors ${
                        c.accepted ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {c.accepted ? '✓ Accepted' : 'Accept'}
                    </button>
                    <button 
                      onClick={(e) => toggleReject(c.id, e)}
                      className={`py-1 text-xs font-medium rounded border transition-colors ${
                        c.rejected ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {c.rejected ? '✕ Rejected' : 'Reject'}
                    </button>
                  </div>
                  
                  {c.accepted && onEditDiagram && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditDiagram(c.id);
                      }}
                      className="w-full py-1.5 text-xs font-bold text-white bg-indigo-600 rounded shadow-sm hover:bg-indigo-700 transition-colors flex items-center justify-center gap-1"
                    >
                      Process & Edit
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Canvas Area */}
      <div 
        ref={containerRef}
        className="flex-1 relative overflow-auto bg-slate-200/50 p-8 flex items-start justify-center shadow-inner"
      >
        <div 
          className="relative shadow-xl bg-white border border-slate-200"
          style={{ 
            width: '100%', 
            maxWidth: imageWidth,
            aspectRatio: `${imageWidth}/${imageHeight}`
          }}
        >
          {/* Image */}
          <img 
            src={imageUrl} 
            alt="Scanned Page"
            className="absolute top-0 left-0 w-full h-full object-contain pointer-events-none"
            draggable="false"
          />
          
          {/* SVG Overlay */}
          <svg
            ref={svgRef}
            viewBox={`0 0 ${imageWidth} ${imageHeight}`}
            className="absolute top-0 left-0 w-full h-full cursor-crosshair z-10"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{ touchAction: 'none' }}
          >
            {sortedCandidates.map((candidate, i) => {
              const { x, y, width, height } = candidate.bbox;
              const isHovered = hoveredCandidateId === candidate.id;
              
              let strokeColor = '#6366f1'; // indigo
              let fillColor = 'rgba(99, 102, 241, 0.1)';
              
              if (candidate.accepted) {
                strokeColor = '#10b981'; // emerald
                fillColor = 'rgba(16, 185, 129, 0.1)';
              } else if (candidate.rejected) {
                strokeColor = '#f43f5e'; // rose
                fillColor = 'rgba(244, 63, 94, 0.05)';
              }

              if (isHovered) {
                fillColor = candidate.accepted ? 'rgba(16, 185, 129, 0.25)' : 'rgba(99, 102, 241, 0.25)';
                strokeColor = candidate.accepted ? '#059669' : '#4f46e5';
              }

              return (
                <g 
                  key={candidate.id} 
                  onMouseEnter={() => setHoveredCandidateId(candidate.id)}
                  onMouseLeave={() => setHoveredCandidateId(null)}
                  onClick={(e) => {
                    if (!drawing) {
                      toggleAccept(candidate.id, e as unknown as React.MouseEvent);
                    }
                  }}
                  className="cursor-pointer"
                >
                  <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    stroke={strokeColor}
                    strokeWidth={isHovered ? "4" : "2"}
                    fill={fillColor}
                    className="transition-all duration-200"
                  />
                  {isHovered && (
                    <>
                      <rect x={x} y={y - 24} width="40" height="24" fill={strokeColor} />
                      <text x={x + 6} y={y - 7} fill="white" fontSize="14" fontWeight="bold" fontFamily="monospace">
                        #{i + 1}
                      </text>
                      
                      {/* Delete icon handle on SVG */}
                      <g transform={`translate(${x + width - 24}, ${y - 24})`} onClick={(e) => { e.stopPropagation(); deleteCandidate(candidate.id); }} className="cursor-pointer hover:opacity-80">
                        <rect width="24" height="24" fill="#ef4444" />
                        <path d="M7 9h10l-1 9H8L7 9zm2-3h6v2H9V6zm1 4v5h2v-5h-2zm3 0v5h2v-5h-2z" fill="white" />
                      </g>
                    </>
                  )}
                </g>
              );
            })}

            {/* Current drawing box */}
            {drawing && currentBox && (
              <rect
                x={currentBox.x}
                y={currentBox.y}
                width={currentBox.width}
                height={currentBox.height}
                stroke="#f59e0b" // amber
                strokeWidth="2"
                strokeDasharray="6 4"
                fill="rgba(245, 158, 11, 0.2)"
                style={{ pointerEvents: 'none' }}
              />
            )}
          </svg>
        </div>
      </div>
    </div>
  );
};
