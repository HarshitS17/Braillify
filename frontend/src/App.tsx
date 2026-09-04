import { useState } from 'react';
import { HealthCheck } from './components/HealthCheck';
import { PageViewer } from './components/PageViewer';
import InteractiveEditor from './components/editor/InteractiveEditor';
import { LandingPage } from './components/LandingPage';

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'dashboard' | 'editor'>('home');
  const [projectData, setProjectData] = useState<{projectId: string, pageId: string, diagramId: string} | null>(null);

  return (
    <div className="h-screen w-full bg-slate-50 flex flex-col font-sans overflow-hidden text-slate-900">
      {/* Top Application Shell Header */}
      <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-4 sm:px-6 shrink-0 z-10">
        <div className="flex items-center gap-6">
          <div 
            className="flex items-center gap-2 cursor-pointer group"
            onClick={() => setActiveTab('home')}
          >
            <div className="w-8 h-8 rounded bg-indigo-600 flex items-center justify-center text-white font-bold shadow-sm group-hover:bg-indigo-700 transition-colors">
              B
            </div>
            <div>
              <h1 className="text-lg font-bold leading-none tracking-tight group-hover:text-indigo-600 transition-colors">Braillify</h1>
            </div>
          </div>
          
          <nav className="hidden sm:flex items-center gap-1 text-sm font-medium">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                activeTab === 'dashboard' ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Workspace
            </button>
            <button
              onClick={() => setActiveTab('editor')}
              disabled={!projectData}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                activeTab === 'editor' ? 'bg-slate-100 text-slate-900' : 
                !projectData ? 'text-slate-300 cursor-not-allowed' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              Editor
            </button>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {/* We embed HealthCheck as a subtle indicator in the top right, instead of a big block */}
          <div className="hidden sm:block scale-75 origin-right">
            <HealthCheck />
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-500 text-xs font-medium">
            US
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col relative">
        {activeTab === 'home' && (
          <main className="absolute inset-0 bg-white overflow-y-auto">
            <LandingPage onGetStarted={() => setActiveTab('dashboard')} />
          </main>
        )}
        
        {activeTab === 'dashboard' && (
          <main className="absolute inset-0 overflow-y-auto bg-slate-50">
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
              <PageViewer onDiagramSelected={(pid, pgid, did) => {
                setProjectData({ projectId: pid, pageId: pgid, diagramId: did });
                setActiveTab('editor');
              }} />
            </div>
          </main>
        )}
        
        {activeTab === 'editor' && projectData && (
          <main className="absolute inset-0 flex flex-col bg-slate-100">
            <InteractiveEditor
              key={projectData.diagramId}
              projectId={projectData.projectId}
              pageId={projectData.pageId}
              diagramId={projectData.diagramId}
              initialElements={[]}
              initialLabels={[]}
              canvasWidth={800}
              canvasHeight={600}
            />
          </main>
        )}
        
        {activeTab === 'editor' && !projectData && (
          <main className="absolute inset-0 flex items-center justify-center bg-slate-50">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-1">No Diagram Selected</h3>
              <p className="text-slate-500 mb-4">Upload and extract a diagram from the workspace first.</p>
              <button 
                onClick={() => setActiveTab('dashboard')}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
              >
                Go to Workspace
              </button>
            </div>
          </main>
        )}
      </div>
    </div>
  );
}

export default App;
