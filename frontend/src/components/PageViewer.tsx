import React, { useState, useRef } from 'react';
import { apiClient } from '../services/api';
import { RegionEditor } from './RegionEditor';
import { DiagramCandidate, ProjectSummary } from '../types';

export const PageViewer: React.FC<{onDiagramSelected?: (projectId: string, pageId: string, diagramId: string) => void}> = ({ onDiagramSelected }) => {
  const [file, setFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<DiagramCandidate[]>([]);
  
  // Pipeline status tracking
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  
  const [imageDims, setImageDims] = useState({ width: 0, height: 0 });
  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [pageId, setPageId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const objectUrlRef = useRef<string | null>(null);

  const steps = [
    'Create Workspace',
    'Upload Page',
    'Preprocess Image',
    'Detect Diagrams'
  ];

  const handleFileChange = async (selectedFile: File | null) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError(null);
    setCurrentStep(-1);
    setStatusMessage('');

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    objectUrlRef.current = objectUrl;
    setImageUrl(objectUrl);
    
    const img = new Image();
    img.onload = () => {
      setImageDims({ width: img.width, height: img.height });
    };
    img.src = objectUrl;
  };

  const processFile = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    try {
      // Step 0: Create Project
      setCurrentStep(0);
      setStatusMessage('Initializing secure workspace...');
      let currentProject = project;
      if (!currentProject) {
        currentProject = await apiClient.createProject({
          name: `Project for ${file.name}`,
          description: 'Auto-generated project for testing'
        });
        setProject(currentProject);
      }

      // Step 1: Upload
      setCurrentStep(1);
      setStatusMessage('Uploading document securely...');
      const uploadResult = await apiClient.uploadPage(currentProject.id, file);
      setPageId(uploadResult.page_id);

      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
      objectUrlRef.current = null;
      setImageUrl(apiClient.getPageImageUrl(currentProject.id, uploadResult.page_id));
      setImageDims({ width: uploadResult.width, height: uploadResult.height });
      
      // Step 2: Preprocess
      setCurrentStep(2);
      setStatusMessage('Enhancing contrast, deskewing, and removing noise...');
      await apiClient.preprocessPage(currentProject.id, uploadResult.page_id);
      
      // Step 3: Detect
      setCurrentStep(3);
      setStatusMessage('Running CV models to locate diagram bounds...');
      const detectedCandidates = await apiClient.detectDiagrams(currentProject.id, uploadResult.page_id);
      setCandidates(detectedCandidates);
      
      setCurrentStep(4);
      setStatusMessage('Complete');
    } catch (err: any) {
      console.error(err);
      setError(`Failed: ${err.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRegions = async (updatedCandidates: DiagramCandidate[]) => {
    if (!project || !pageId) return;
    
    setLoading(true);
    try {
      await apiClient.saveDiagrams(project.id, pageId, updatedCandidates);
    } catch (err: any) {
      console.error(err);
      setError(`Error saving: ${err.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Drag handlers
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const onDragLeave = () => setIsDragging(false);
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0] || null);
    }
  };

  return (
    <div className="flex flex-col space-y-6">
      
      {/* Upload & Processing Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Upload Source Document</h2>
            <p className="text-sm text-slate-500">Supported formats: PDF, PNG, JPEG</p>
          </div>
          
          {file && currentStep === -1 && (
            <button
              onClick={processFile}
              disabled={loading}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-semibold text-sm hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50"
            >
              Start Extraction Pipeline
            </button>
          )}
        </div>

        <div className="p-6 grid md:grid-cols-2 gap-8">
          
          {/* Dropzone */}
          <div 
            className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-8 transition-colors ${
              isDragging ? 'border-indigo-500 bg-indigo-50/50' : 'border-slate-300 bg-slate-50 hover:bg-slate-100 hover:border-slate-400'
            } ${file ? 'border-solid border-indigo-200 bg-indigo-50/30' : ''}`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => !file && fileInputRef.current?.click()}
          >
            <input
              type="file"
              accept="image/png, image/jpeg, application/pdf"
              ref={fileInputRef}
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
              className="hidden"
            />
            
            {file ? (
              <div className="text-center">
                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-3 text-indigo-600">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-slate-900 truncate max-w-[200px] mx-auto">{file.name}</p>
                <p className="text-xs text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                {currentStep === -1 && (
                  <button onClick={(e) => { e.stopPropagation(); setFile(null); setImageUrl(null); }} className="text-xs text-red-500 font-medium mt-3 hover:underline">
                    Remove file
                  </button>
                )}
              </div>
            ) : (
              <div className="text-center cursor-pointer">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <p className="text-sm font-semibold text-slate-900">Click to upload or drag and drop</p>
                <p className="text-xs text-slate-500 mt-1">SVG, PNG, JPG or PDF (max. 10MB)</p>
              </div>
            )}
          </div>

          {/* Processing Visualizer */}
          <div className="flex flex-col justify-center">
            {currentStep >= 0 ? (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Extraction Pipeline</h3>
                {steps.map((step, idx) => {
                  const isActive = currentStep === idx;
                  const isPast = currentStep > idx;
                  
                  return (
                    <div key={idx} className="flex items-center gap-4">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        isPast ? 'bg-emerald-500 text-white' : 
                        isActive ? 'bg-indigo-600 text-white animate-pulse' : 
                        'bg-slate-100 text-slate-400'
                      }`}>
                        {isPast ? '✓' : idx + 1}
                      </div>
                      <span className={`text-sm font-medium ${isActive ? 'text-indigo-600' : isPast ? 'text-slate-900' : 'text-slate-400'}`}>
                        {step}
                      </span>
                    </div>
                  );
                })}

                <div className="mt-6 p-3 bg-slate-50 rounded text-xs font-mono text-slate-600 border border-slate-200">
                  {statusMessage || 'Awaiting input...'}
                </div>
                
                {error && (
                  <div className="mt-2 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200 flex items-start gap-2">
                    <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{error}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-100 rounded-xl bg-slate-50/50">
                <p className="text-sm text-slate-400 text-center px-8">
                  Upload a file to begin the automatic extraction pipeline.
                </p>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Region Editor Section */}
      {imageUrl && currentStep === 4 && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[800px] max-h-[85vh]">
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Review Detected Regions</h2>
              <p className="text-xs text-slate-500">Select a region below to proceed to the tactile editor.</p>
            </div>
          </div>
          
          <div className="flex-1 relative bg-slate-100">
            <RegionEditor
              imageUrl={imageUrl}
              initialCandidates={candidates}
              imageWidth={imageDims.width}
              imageHeight={imageDims.height}
              onSave={handleSaveRegions}
              onEditDiagram={async (diagramId) => {
                if (onDiagramSelected && project && pageId) {
                  await handleSaveRegions(candidates);
                  
                  setError(null);
                  setCurrentStep(0);
                  setStatusMessage('Executing downstream vectorization & braille pipeline...');
                  setLoading(true);
                  try {
                    await apiClient.runWorkflow(project.id, pageId, diagramId, {
                      start_stage: 'extract',
                      end_stage: 'place'
                    });
                    onDiagramSelected(project.id, pageId, diagramId);
                  } catch (e: any) {
                    console.error(e);
                    setError(`Workflow error: ${e.message}`);
                    setCurrentStep(4);
                  } finally {
                    setLoading(false);
                  }
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
