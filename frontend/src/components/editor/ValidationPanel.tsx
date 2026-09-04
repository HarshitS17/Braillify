import type { ValidationResult } from '../../types';

interface ValidationPanelProps {
  result: ValidationResult | null;
  loading: boolean;
  onRunValidation: () => void;
}

export default function ValidationPanel({ result, loading, onRunValidation }: ValidationPanelProps) {
  const issueCount = result ? result.errors.length + result.warnings.length + result.suggestions.length : 0;
  
  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 border-t border-slate-200">
      <div className="p-3 border-b border-slate-200 sticky top-0 bg-white z-10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-xs font-bold text-slate-800 tracking-wider uppercase">Pre-flight</p>
          {result && (
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
              issueCount === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
            }`}>
              {issueCount === 0 ? 'PASS' : `${issueCount} ISSUES`}
            </span>
          )}
        </div>
        <button
          onClick={onRunValidation}
          disabled={loading}
          className="flex items-center gap-1 bg-white border border-slate-200 text-slate-600 px-2.5 py-1 rounded-md text-xs font-medium hover:bg-slate-50 hover:text-slate-900 disabled:opacity-50 transition-colors shadow-sm"
        >
          {loading ? (
            <svg className="w-3 h-3 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          {loading ? 'Running...' : 'Validate'}
        </button>
      </div>

      <div className="p-3">
        {!result && !loading && (
          <div className="text-center p-6 border-2 border-dashed border-slate-200 rounded-lg">
            <svg className="w-8 h-8 text-slate-300 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <p className="text-xs text-slate-500">Run pre-flight validation to check for embosser compatibility issues.</p>
          </div>
        )}

        {result && (
          <div className="space-y-2">
            {issueCount === 0 && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-center">
                <div className="w-8 h-8 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-emerald-800 text-sm font-bold">All checks passed</p>
                <p className="text-emerald-600 text-xs mt-1">Diagram is ready for embossing.</p>
              </div>
            )}

            {result.errors.map(msg => (
              <div key={msg.id} className="bg-rose-50 border border-rose-200 rounded-lg p-2.5 flex items-start gap-2.5 shadow-sm">
                <svg className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="text-[10px] font-bold text-rose-700 tracking-wider uppercase block mb-0.5">Error</span>
                  <span className="text-xs text-slate-700 leading-tight">{msg.message}</span>
                </div>
              </div>
            ))}

            {result.warnings.map(msg => (
              <div key={msg.id} className="bg-amber-50 border border-amber-200 rounded-lg p-2.5 flex items-start gap-2.5 shadow-sm">
                <svg className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="text-[10px] font-bold text-amber-700 tracking-wider uppercase block mb-0.5">Warning</span>
                  <span className="text-xs text-slate-700 leading-tight">{msg.message}</span>
                </div>
              </div>
            ))}

            {result.suggestions.map(msg => (
              <div key={msg.id} className="bg-indigo-50 border border-indigo-200 rounded-lg p-2.5 flex items-start gap-2.5 shadow-sm">
                <svg className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <span className="text-[10px] font-bold text-indigo-700 tracking-wider uppercase block mb-0.5">Suggestion</span>
                  <span className="text-xs text-slate-700 leading-tight">{msg.message}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
