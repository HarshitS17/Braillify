import { useRef, useState } from 'react';
import type { DiagramElement, Label } from '../../types';
import type { LayerConfig } from '../../hooks/useEditorState';

interface CanvasProps {
  elements: DiagramElement[];
  labels: Label[];
  selectedId: string | null;
  canvasWidth: number;
  canvasHeight: number;
  layers: LayerConfig[];
  zoom: number;
  panX: number;
  panY: number;
  onSelect: (id: string | null, type: 'element' | 'label' | null) => void;
  onMoveLabel: (labelId: string, dx: number, dy: number) => void;
  onPushHistory: (elements: DiagramElement[], labels: Label[]) => void;
  /** Fired when a label drag actually moved the label (drag end) — used to persist the new placement. */
  onLabelDragEnd?: (labelId: string) => void;
}

function renderElement(el: DiagramElement, isSelected: boolean) {
  const g = el.geometry;
  const style: React.CSSProperties = {
    stroke: isSelected ? '#60a5fa' : '#f8fafc',
    strokeWidth: isSelected ? 3 : 2,
    fill: 'none',
    cursor: 'pointer',
  };
  if (el.type === 'line' && 'x1' in g) {
    return <line key={el.id} data-id={el.id} x1={g.x1 as number} y1={g.y1 as number} x2={g.x2 as number} y2={g.y2 as number} style={style} />;
  }
  if (el.type === 'circle' && 'cx' in g) {
    return <circle key={el.id} data-id={el.id} cx={g.cx as number} cy={g.cy as number} r={g.r as number} style={style} />;
  }
  if ((el.type === 'polygon' || el.type === 'filled_region') && 'points' in g) {
    const pts = (g.points as { x: number; y: number }[]).map(p => `${p.x},${p.y}`).join(' ');
    const fillStyle = el.type === 'filled_region' ? { ...style, fill: isSelected ? '#93c5fd' : '#334155' } : style;
    return <polygon key={el.id} data-id={el.id} points={pts} style={fillStyle} />;
  }
  if (el.type === 'curve' && 'points' in g) {
    const pts = (g.points as { x: number; y: number }[]).map(p => `${p.x},${p.y}`).join(' ');
    return <polyline key={el.id} data-id={el.id} points={pts} style={style} />;
  }
  return null;
}

function renderLabel(lbl: Label, isSelected: boolean) {
  if (!lbl.placement) return null;
  const p = lbl.placement;
  const text = lbl.braille?.braille_unicode || lbl.text;
  return (
    <g key={lbl.id} data-id={lbl.id} data-type="label">
      {p.leader_line && (
        <line x1={p.leader_line.start.x} y1={p.leader_line.start.y} x2={p.leader_line.end.x} y2={p.leader_line.end.y} stroke="#94a3b8" strokeWidth={1} strokeDasharray="4,4" />
      )}
      <rect x={p.position.x} y={p.position.y} width={p.width} height={p.height} fill={isSelected ? '#3b82f6' : '#1e293b'} stroke={isSelected ? '#60a5fa' : '#475569'} strokeWidth={isSelected ? 2 : 1} rx={3} style={{ cursor: 'grab' }} />
      <text x={p.position.x + 4} y={p.position.y + p.height - 5} fontSize={11} fill="#f8fafc" style={{ pointerEvents: 'none', userSelect: 'none' }}>{text}</text>
    </g>
  );
}

export default function Canvas({ elements, labels, selectedId, canvasWidth, canvasHeight, layers, zoom, panX, panY, onSelect, onMoveLabel, onPushHistory, onLabelDragEnd }: CanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<{ id: string; startX: number; startY: number; moved: boolean } | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const showGeometry = layers.find(l => l.id === 'geometry')?.visible ?? true;
  const showLabels = layers.find(l => l.id === 'labels')?.visible ?? true;
  const showGrid = layers.find(l => l.id === 'grid')?.visible ?? false;

  const handlePointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    if (e.button === 1 || (e.button === 0 && e.altKey)) { setIsPanning(true); return; }
    const target = e.target as SVGElement;
    const id = target.getAttribute('data-id') || target.closest('[data-id]')?.getAttribute('data-id');
    const isLabel = target.getAttribute('data-type') === 'label' || target.closest('[data-type="label"]') !== null;
    if (id) {
      onSelect(id, isLabel ? 'label' : 'element');
      if (isLabel) {
        const svg = e.currentTarget;
        const pt = svg.createSVGPoint();
        pt.x = e.clientX; pt.y = e.clientY;
        const svgPt = pt.matrixTransform(svg.getScreenCTM()?.inverse());
        dragRef.current = { id, startX: svgPt.x, startY: svgPt.y, moved: false };
        // Snapshot the PRE-drag state so Undo restores the original position.
        onPushHistory(elements, labels);
        (e.target as Element).setPointerCapture(e.pointerId);
      }
    } else { onSelect(null, null); }
  };

  const handlePointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!dragRef.current) return;
    const svg = e.currentTarget;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const svgPt = pt.matrixTransform(svg.getScreenCTM()?.inverse());
    const dx = svgPt.x - dragRef.current.startX;
    const dy = svgPt.y - dragRef.current.startY;
    if (dx !== 0 || dy !== 0) dragRef.current.moved = true;
    onMoveLabel(dragRef.current.id, dx, dy);
    dragRef.current.startX = svgPt.x;
    dragRef.current.startY = svgPt.y;
  };

  const handlePointerUp = () => {
    if (dragRef.current && dragRef.current.moved) {
      // Drag finished: persist the new placement so it survives export/reload.
      onLabelDragEnd?.(dragRef.current.id);
    }
    dragRef.current = null;
    setIsPanning(false);
  };

  return (
    <svg ref={svgRef} width="100%" height="100%" viewBox={`${-panX} ${-panY} ${canvasWidth / zoom} ${canvasHeight / zoom}`} style={{ background: '#0f172a', cursor: isPanning ? 'grabbing' : 'default' }} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp}>
      {showGrid && <defs><pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M 20 0 L 0 0 0 20" fill="none" stroke="#334155" strokeWidth="0.5" /></pattern></defs>}
      {showGrid && <rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#grid)" />}
      {showGeometry && elements.map(el => renderElement(el, el.id === selectedId))}
      {showLabels && labels.map(lbl => renderLabel(lbl, lbl.id === selectedId))}
    </svg>
  );
}