const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiClient {
  static async executeGraph(payload: any): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_URL}/execute-graph`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error('Failed to start execution');
    }
    
    return response.json();
  }

  static async getJobStatus(jobId: string): Promise<any> {
    const response = await fetch(`${API_URL}/job-status/${jobId}`);
    if (!response.ok) {
      throw new Error('Failed to get job status');
    }
    return response.json();
  }
}
