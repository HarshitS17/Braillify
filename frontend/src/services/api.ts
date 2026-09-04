import type { HealthResponse, ProjectCreate, ProjectSummary, DiagramCandidate, Diagram, DiagramElement, Label, LabelPlacement, ValidationResult, ExportConfig, ApiError } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      let errorData: ApiError;
      try {
        errorData = await response.json() as ApiError;
      } catch {
        errorData = {
          error: 'NetworkError',
          message: `Request failed with status ${response.status}`,
        };
      }
      const msg = errorData.detail ? `${errorData.message} (${errorData.detail})` : errorData.message;
      throw new ApiRequestError(msg, response.status, errorData);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  // Health
  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Projects
  async createProject(data: ProjectCreate): Promise<ProjectSummary> {
    return this.request<ProjectSummary>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listProjects(): Promise<ProjectSummary[]> {
    return this.request<ProjectSummary[]>('/api/projects');
  }

  async getProject(id: string): Promise<ProjectSummary> {
    return this.request<ProjectSummary>(`/api/projects/${id}`);
  }

  async deleteProject(id: string): Promise<void> {
    return this.request<void>(`/api/projects/${id}`, {
      method: 'DELETE',
    });
  }

  // Upload
  async uploadPage(projectId: string, file: File): Promise<{ page_id: string; project_id: string; filename: string; format: string; width: number; height: number; status: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/api/projects/${projectId}/pages`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Do NOT set Content-Type header — browser sets multipart boundary automatically
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText, message: response.statusText }));
      // Backend TactileEd errors carry a human-readable `message`; prefer it over
      // the raw status text so users see e.g. "Failed to open PDF: ..." instead of
      // a generic "Unsupported Media Type".
      throw new Error(err.message || err.detail || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /** URL of the backend-served page image (rasterized PDF page or original image). */
  getPageImageUrl(projectId: string, pageId: string): string {
    return `${this.baseUrl}/api/projects/${projectId}/pages/${pageId}/image`;
  }

  // Preprocessing
  async preprocessPage(projectId: string, pageId: string): Promise<{ page_id: string; status: string; stages_completed: number }> {
    return this.request(`/api/projects/${projectId}/pages/${pageId}/preprocess`, {
      method: 'POST',
    });
  }

  // Detection
  async detectDiagrams(projectId: string, pageId: string): Promise<DiagramCandidate[]> {
    return this.request<DiagramCandidate[]>(`/api/projects/${projectId}/pages/${pageId}/detect`, {
      method: 'POST',
    });
  }

  async saveDiagrams(projectId: string, pageId: string, diagrams: DiagramCandidate[]): Promise<void> {
    return this.request<void>(`/api/projects/${projectId}/pages/${pageId}/diagrams`, {
      method: 'POST',
      body: JSON.stringify(diagrams),
    });
  }

  // --- Editor API ---

  async getDiagram(projectId: string, pageId: string, diagramId: string): Promise<Diagram> {
    return this.request<Diagram>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}`);
  }

  async getLabels(projectId: string, pageId: string, diagramId: string): Promise<Label[]> {
    return this.request<Label[]>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/labels`);
  }

  /**
   * Persist a human-in-the-loop label correction (text / braille / placement).
   * The backend re-translates Braille server-side when `text` changes, so the
   * exported tactile output always matches the corrected text.
   */
  async updateLabel(
    projectId: string,
    pageId: string,
    diagramId: string,
    labelId: string,
    updates: { text?: string; braille_unicode?: string; braille_dots?: string; placement?: LabelPlacement | null }
  ): Promise<Label> {
    return this.request<Label>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/labels/${labelId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /** Replace the diagram's full label set (editor sync: deletes, undo/redo). */
  async replaceLabels(projectId: string, pageId: string, diagramId: string, labels: Label[]): Promise<Label[]> {
    return this.request<Label[]>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/labels`, {
      method: 'PUT',
      body: JSON.stringify({ labels }),
    });
  }

  /** Persist element-level diagram corrections (e.g. deleted elements). */
  async updateDiagramElements(projectId: string, pageId: string, diagramId: string, elements: DiagramElement[]): Promise<Diagram> {
    return this.request<Diagram>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}`, {
      method: 'PUT',
      body: JSON.stringify({ elements }),
    });
  }

  async runValidation(projectId: string, pageId: string, diagramId: string): Promise<ValidationResult> {
    return this.request<ValidationResult>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/validate`);
  }

  async exportSvg(projectId: string, pageId: string, diagramId: string, config?: Partial<ExportConfig>): Promise<Blob> {
    const url = `${this.baseUrl}/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/export/svg`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: config ?? {} }),
    });
    if (!response.ok) throw new Error('SVG export failed');
    return response.blob();
  }

  async exportPdf(projectId: string, pageId: string, diagramId: string, config?: Partial<ExportConfig>): Promise<Blob> {
    const url = `${this.baseUrl}/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/export/pdf`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: config ?? {} }),
    });
    if (!response.ok) throw new Error('PDF export failed');
    return response.blob();
  }

  async runWorkflow(projectId: string, pageId: string, diagramId: string, options: any): Promise<Diagram> {
    return this.request<Diagram>(`/api/projects/${projectId}/pages/${pageId}/diagrams/${diagramId}/workflow`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }
}

export class ApiRequestError extends Error {
  status: number;
  errorData: ApiError;

  constructor(message: string, status: number, errorData: ApiError) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.errorData = errorData;
  }
}

export const apiClient = new ApiClient();
