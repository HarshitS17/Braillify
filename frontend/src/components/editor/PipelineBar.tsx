interface PipelineStage {
  id: string;
  name: string;
  status: 'complete' | 'processing' | 'pending' | 'error';
}

const stages: PipelineStage[] = [
  { id: 'extract', name: 'Extract', status: 'pending' },
  { id: 'analyze', name: 'Analyze', status: 'pending' },
  { id: 'simplify', name: 'Simplify', status: 'pending' },
  { id: 'semantics', name: 'Semantics', status: 'pending' },
  { id: 'ocr', name: 'OCR', status: 'pending' },
  { id: 'translate', name: 'Translate', status: 'pending' },
  { id: 'place', name: 'Place', status: 'pending' },
  { id: 'validate', name: 'Validate', status: 'pending' },
];

interface PipelineBarProps {
  currentStage?: string;
  completedStages?: string[];
}

export default function PipelineBar({
  currentStage,
  completedStages = [],
}: PipelineBarProps) {
  const getStageStatus = (stageId: string): PipelineStage['status'] => {
    if (completedStages.includes(stageId)) return 'complete';
    if (currentStage === stageId) return 'processing';
    return 'pending';
  };

  return (
    <div className="flex items-center text-[10px] uppercase tracking-wider font-bold overflow-x-auto no-scrollbar py-1">
      <div className="flex items-center gap-1.5 mr-4 text-slate-400">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span>Pipeline Status</span>
      </div>

      <div className="flex items-center bg-slate-50 border border-slate-200 rounded-md px-2 py-1 shadow-sm">
        {stages.map((stage, index) => {
          const status = getStageStatus(stage.id);
          
          let icon = null;
          let colorClass = '';
          
          if (status === 'complete') {
            colorClass = 'text-emerald-600';
            icon = <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>;
          } else if (status === 'processing') {
            colorClass = 'text-indigo-600 animate-pulse';
            icon = <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>;
          } else if (status === 'error') {
            colorClass = 'text-rose-600';
            icon = <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>;
          } else {
            colorClass = 'text-slate-400';
            icon = <div className="w-1.5 h-1.5 rounded-full bg-slate-300 mx-0.5"></div>;
          }

          return (
            <div key={stage.id} className="flex items-center">
              <div className={`flex items-center gap-1 ${colorClass}`}>
                {icon}
                <span className={status === 'pending' ? 'text-slate-400 font-medium' : ''}>{stage.name}</span>
              </div>
              
              {index < stages.length - 1 && (
                <div className="mx-2 w-3 h-[1px] bg-slate-300"></div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}