// API Client SDK [M4]
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async getHealth(): Promise<{ status: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    return res.json();
  }
}
