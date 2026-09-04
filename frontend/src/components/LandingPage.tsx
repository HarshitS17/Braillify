import React, { useEffect, useState } from 'react';

interface LandingPageProps {
  onGetStarted: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  const [animationStep, setAnimationStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationStep((prev) => (prev + 1) % 3);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white w-full text-slate-900 font-sans">
      {/* Hero Section */}
      <div className="relative isolate pt-14 lg:pt-24 px-6 lg:px-8 max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center min-h-[85vh]">
        <div className="text-left pb-16 lg:pb-0 z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-6">
            <span className="flex h-2 w-2 rounded-full bg-indigo-600 animate-pulse"></span>
            Computer Vision for Accessibility
          </div>
          <h1 className="text-4xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight">
            Textbooks into <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
              Tactile Graphics
            </span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-slate-600 max-w-lg">
            Transform standard educational diagrams into embossable, tactile-ready graphics instantly. Braillify uses advanced computer vision to extract, simplify, and add Braille labels with collision-free placement.
          </p>
          <div className="mt-10 flex items-center gap-x-6">
            <button
              onClick={onGetStarted}
              className="rounded-lg bg-indigo-600 px-6 py-3.5 text-base font-semibold text-white shadow-sm hover:bg-indigo-500 hover:shadow transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Open Workspace
            </button>
            <a href="https://github.com/HarshitS17/Braillify" target="_blank" rel="noopener noreferrer" className="text-sm font-semibold leading-6 text-slate-900 flex items-center gap-2 hover:text-indigo-600 transition-colors">
              View Documentation <span aria-hidden="true">→</span>
            </a>
          </div>
        </div>

        {/* Interactive Visualization Hero */}
        <div className="relative w-full aspect-square max-w-lg mx-auto bg-slate-50 rounded-3xl border border-slate-200 shadow-xl overflow-hidden flex flex-col">
          <div className="h-10 bg-slate-100 border-b border-slate-200 flex items-center px-4 gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-rose-400"></div>
              <div className="w-3 h-3 rounded-full bg-amber-400"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
            </div>
            <div className="mx-auto bg-white border border-slate-200 rounded-md px-24 py-1 text-[10px] text-slate-400 font-mono">
              tactile-pipeline.exe
            </div>
          </div>
          <div className="flex-1 relative bg-white p-8 flex items-center justify-center">
            
            {/* Step 0: Original Diagram */}
            <div className={`absolute inset-0 p-12 transition-opacity duration-700 flex flex-col items-center justify-center ${animationStep === 0 ? 'opacity-100' : 'opacity-0'}`}>
              <div className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-8">1. Original Scan</div>
              <div className="w-full h-full border-2 border-dashed border-slate-300 bg-slate-50 rounded-xl relative overflow-hidden">
                <div className="absolute top-1/4 left-1/4 w-32 h-32 rounded-full bg-slate-300 blur-sm"></div>
                <div className="absolute top-1/2 left-1/2 w-24 h-24 bg-slate-400 transform -rotate-12 blur-[2px]"></div>
                <div className="absolute top-20 right-20 text-slate-400 font-serif text-lg blur-[1px]">Figure 4.2</div>
                {/* Simulated noise */}
                <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(#000 1px, transparent 1px)', backgroundSize: '8px 8px' }}></div>
              </div>
            </div>

            {/* Step 1: Computer Vision Extraction */}
            <div className={`absolute inset-0 p-12 transition-opacity duration-700 flex flex-col items-center justify-center ${animationStep === 1 ? 'opacity-100' : 'opacity-0'}`}>
              <div className="text-xs font-bold text-indigo-500 tracking-widest uppercase mb-8">2. Computer Vision</div>
              <div className="w-full h-full border-2 border-indigo-200 bg-indigo-50/30 rounded-xl relative overflow-hidden">
                {/* Extracted precise geometry */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <circle cx="40" cy="45" r="25" fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="4 2" className="animate-[spin_10s_linear_infinite]" />
                  <rect x="45" y="45" width="25" height="25" fill="none" stroke="#6366f1" strokeWidth="1" transform="rotate(-12 57 57)" />
                  <path d="M 10,90 L 90,90 M 10,10 L 10,90" stroke="#cbd5e1" strokeWidth="0.5" />
                  
                  {/* Bounding boxes */}
                  <rect x="13" y="18" width="54" height="54" fill="none" stroke="#22c55e" strokeWidth="0.5" />
                  <rect x="70" y="15" width="20" height="8" fill="none" stroke="#eab308" strokeWidth="0.5" />
                </svg>
                <div className="absolute top-4 left-4 bg-indigo-600 text-white text-[9px] px-1.5 py-0.5 rounded font-mono">DETECTING...</div>
              </div>
            </div>

            {/* Step 2: Tactile Graphic & Braille */}
            <div className={`absolute inset-0 p-12 transition-opacity duration-700 flex flex-col items-center justify-center ${animationStep === 2 ? 'opacity-100' : 'opacity-0'}`}>
              <div className="text-xs font-bold text-slate-800 tracking-widest uppercase mb-8">3. Tactile Graphic</div>
              <div className="w-full h-full border-2 border-slate-900 bg-white rounded-xl relative overflow-hidden shadow-inner">
                {/* High contrast, simplified, Braille */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <circle cx="40" cy="45" r="25" fill="none" stroke="#000" strokeWidth="3" />
                  <rect x="45" y="45" width="25" height="25" fill="none" stroke="#000" strokeWidth="3" transform="rotate(-12 57 57)" />
                  <path d="M 57,57 L 80,75" stroke="#000" strokeWidth="1.5" strokeDasharray="2 2" />
                  
                  {/* Braille dots simulation */}
                  <g transform="translate(75, 75)">
                    <circle cx="0" cy="0" r="1.5" fill="#000" />
                    <circle cx="0" cy="4" r="1.5" fill="#000" />
                    <circle cx="4" cy="0" r="1.5" fill="#000" />
                    <circle cx="4" cy="8" r="1.5" fill="#000" />
                    <circle cx="8" cy="4" r="1.5" fill="#000" />
                    <circle cx="12" cy="0" r="1.5" fill="#000" />
                  </g>
                  
                  <g transform="translate(65, 18)">
                    <circle cx="0" cy="0" r="1.5" fill="#000" />
                    <circle cx="0" cy="4" r="1.5" fill="#000" />
                    <circle cx="0" cy="8" r="1.5" fill="#000" />
                    <circle cx="4" cy="4" r="1.5" fill="#000" />
                    <circle cx="8" cy="8" r="1.5" fill="#000" />
                  </g>
                </svg>
                <div className="absolute bottom-4 right-4 bg-slate-900 text-white text-[9px] px-2 py-1 rounded font-mono">READY FOR EMBOSSER</div>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 sm:py-32 bg-slate-50 border-t border-slate-200">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-indigo-600">Complete Toolchain</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Professional accessibility infrastructure
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-4xl">
            <dl className="grid max-w-xl grid-cols-1 gap-x-12 gap-y-16 lg:max-w-none lg:grid-cols-2">
              
              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-slate-200 shadow-sm text-indigo-600">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 013.75 9.375v-4.5zM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5z" />
                    </svg>
                  </div>
                  Diagram Region Extraction
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">
                  Automatically isolate diagrams from body text on noisy scanned textbook pages. Ranked candidates allow for rapid human-in-the-loop review.
                </dd>
              </div>

              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-slate-200 shadow-sm text-indigo-600">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" />
                    </svg>
                  </div>
                  Tactile Geometry Simplification
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">
                  Vectorizes raster images and cleanly removes shading, gradients, and overly fine details to produce crisp, embossable line art.
                </dd>
              </div>

              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-slate-200 shadow-sm text-indigo-600">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
                    </svg>
                  </div>
                  Automated Braille Translation
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">
                  OCR extracts labels, automatically translates them to Grade 1 Braille, and uses collision-detection to place them optimally around geometry.
                </dd>
              </div>

              <div className="relative pl-16">
                <dt className="text-base font-semibold leading-7 text-slate-900">
                  <div className="absolute left-0 top-0 flex h-12 w-12 items-center justify-center rounded-xl bg-white border border-slate-200 shadow-sm text-indigo-600">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  Embosser-Ready Physical Export
                </dt>
                <dd className="mt-2 text-base leading-7 text-slate-600">
                  Exports final diagrams to standard formats like SVG and PDF, maintaining strict physical dimensions (mm/cm) required by tactile embossers.
                </dd>
              </div>

            </dl>
          </div>
        </div>
      </div>

      {/* Subtle Footer */}
      <footer className="py-8 border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 text-center">
          <p className="text-xs leading-5 text-slate-400">
            &copy; {new Date().getFullYear()} Braillify. <span className="opacity-60">Formerly known as Project TactileEd.</span>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
