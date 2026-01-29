/**
 * Clima-scope API Client
 * 
 * Type-safe API client for interacting with the Clima-scope backend.
 * Provides methods for all API endpoints with proper TypeScript types.
 */

// Base Types
export interface County {
  id: string;
  name: string;
  region: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface WeatherReport {
  id: number;
  county_id: string;
  period_start: string;
  period_end: string;
  raw_data: Record<string, any>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PDFReport {
  id: number;
  complete_report_id?: number;
  file_path: string;
  file_size_bytes: number;
  generation_method: string;
  status: string;
  created_at: string;
}

export interface PipelineExecution {
  pipeline_id: string;
  county_id: string;
  period_start: string;
  period_end: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  current_stage: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  artifacts?: {
    weather_report_id?: number;
    complete_report_id?: number;
    pdf_report_id?: number;
  };
}

export interface MapMetadata {
  county_id: string;
  variable: 'rainfall' | 'temperature' | 'wind';
  period_start: string;
  period_end: string;
  file_path: string;
  format: 'png' | 'svg' | 'jpeg';
  resolution_dpi: number;
  width_px: number;
  height_px: number;
  generated_at: string;
}

// Request Types
export interface CreateReportRequest {
  county_id: string;
  period_start: string;
  period_end: string;
  raw_data: Record<string, any>;
}

export interface ProcessPipelineRequest {
  county_id: string;
  period_start: string;
  period_end: string;
  raw_data: Record<string, any>;
  async_mode?: boolean;
}

export interface ReportFilters {
  county_id?: string;
  status?: string;
  period_start?: string;
  period_end?: string;
  skip?: number;
  limit?: number;
}

// API Client Class
export class ClimascopeAPI {
  private baseURL: string;

  constructor(baseURL?: string) {
    this.baseURL = baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  // Helper method for fetch with error handling
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // County Methods
  async getCounties(): Promise<{ counties: County[]; total: number }> {
    return this.request('/api/v1/counties');
  }

  async getCounty(id: string): Promise<County> {
    return this.request(`/api/v1/counties/${id}`);
  }

  async updateCountyNotes(id: string, notes: string): Promise<County> {
    return this.request(`/api/v1/counties/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ notes }),
    });
  }

  // Report Methods
  async createReport(data: CreateReportRequest): Promise<WeatherReport> {
    return this.request('/api/v1/reports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReport(id: number): Promise<WeatherReport> {
    return this.request(`/api/v1/reports/${id}`);
  }

  async listReports(filters?: ReportFilters): Promise<{
    reports: WeatherReport[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams();
    if (filters?.county_id) params.append('county_id', filters.county_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const queryString = params.toString();
    return this.request(`/api/v1/reports${queryString ? `?${queryString}` : ''}`);
  }

  async deleteReport(id: number): Promise<void> {
    await this.request(`/api/v1/reports/${id}`, { method: 'DELETE' });
  }

  // PDF Methods
  async generatePDF(reportId: number): Promise<PDFReport> {
    return this.request(`/api/v1/pdf/generate/${reportId}`, {
      method: 'POST',
    });
  }

  async getPDF(pdfId: number): Promise<PDFReport> {
    return this.request(`/api/v1/pdf/${pdfId}`);
  }

  async downloadPDF(pdfId: number): Promise<Blob> {
    const url = `${this.baseURL}/api/v1/pdf/${pdfId}/download`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to download PDF: ${response.status}`);
    }
    
    return await response.blob();
  }

  // Pipeline Methods
  async startPipeline(request: ProcessPipelineRequest): Promise<PipelineExecution> {
    return this.request('/api/v1/pipeline/process', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getPipelineStatus(pipelineId: string): Promise<PipelineExecution> {
    return this.request(`/api/v1/pipeline/${pipelineId}/status`);
  }

  async cancelPipeline(pipelineId: string): Promise<{ message: string }> {
    return this.request(`/api/v1/pipeline/${pipelineId}/cancel`, {
      method: 'POST',
    });
  }

  async listPipelineHistory(filters?: {
    county_id?: string;
    status?: string;
    limit?: number;
  }): Promise<{ total: number; pipelines: PipelineExecution[] }> {
    const params = new URLSearchParams();
    if (filters?.county_id) params.append('county_id', filters.county_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const queryString = params.toString();
    return this.request(`/api/v1/pipeline/history${queryString ? `?${queryString}` : ''}`);
  }

  // Map Methods
  async uploadMap(formData: FormData): Promise<{ message: string; map: MapMetadata }> {
    const url = `${this.baseURL}/api/v1/maps/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData, // Don't set Content-Type, browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }

    return await response.json();
  }

  async listCountyMaps(countyId: string, filters?: {
    variable?: 'rainfall' | 'temperature' | 'wind';
    year?: number;
    week?: number;
  }): Promise<{ county_id: string; total: number; maps: MapMetadata[] }> {
    const params = new URLSearchParams();
    if (filters?.variable) params.append('variable', filters.variable);
    if (filters?.year) params.append('year', filters.year.toString());
    if (filters?.week) params.append('week', filters.week.toString());
    
    const queryString = params.toString();
    return this.request(`/api/v1/maps/${countyId}${queryString ? `?${queryString}` : ''}`);
  }

  async downloadMap(
    countyId: string,
    variable: 'rainfall' | 'temperature' | 'wind',
    periodStart: string,
    periodEnd: string
  ): Promise<Blob> {
    const params = new URLSearchParams({
      period_start: periodStart,
      period_end: periodEnd,
    });
    
    const url = `${this.baseURL}/api/v1/maps/${countyId}/${variable}/download?${params}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to download map: ${response.status}`);
    }
    
    return await response.blob();
  }

  // Upload Methods
  async uploadWeatherData(formData: FormData): Promise<{
    message: string;
    pipeline_id?: string;
    pipeline_status_url?: string;
  }> {
    const url = `${this.baseURL}/api/v1/uploads/weather-data`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }

    return await response.json();
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/api/v1/health');
  }
}

// Export singleton instance
export const api = new ClimascopeAPI();

// Export class for custom instances
export default ClimascopeAPI;
