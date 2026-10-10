// EcoCampus AI - Centralized REST API Service
const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('ecocampus_token') || null;
    this.user = JSON.parse(localStorage.getItem('ecocampus_user') || 'null');
  }

  getHeaders(isFormData = false) {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const isFormData = options.body instanceof FormData;
    const headers = { ...this.getHeaders(isFormData), ...(options.headers || {}) };

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP error ${response.status}`);
      }
      return data;
    } catch (error) {
      console.error(`API Error on [${endpoint}]:`, error);
      throw error;
    }
  }

  // Auth
  async login(email, password) {
    const res = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (res.success && res.token) {
      this.token = res.token;
      this.user = res.user;
      localStorage.setItem('ecocampus_token', res.token);
      localStorage.setItem('ecocampus_user', JSON.stringify(res.user));
    }
    return res;
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('ecocampus_token');
    localStorage.removeItem('ecocampus_user');
  }

  // Buildings
  async getBuildings() {
    return this.request('/buildings');
  }

  async getBuildingDetail(id) {
    return this.request(`/buildings/${id}`);
  }

  // Energy & Water
  async getEnergyOverview(range = '24h', buildingId = 'ALL') {
    return this.request(`/energy?range=${range}&building_id=${buildingId}`);
  }

  async getWaterOverview(range = '24h', buildingId = 'ALL') {
    return this.request(`/water?range=${range}&building_id=${buildingId}`);
  }

  // Anomalies & XAI
  async getAnomalies(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/anomalies?${query}`);
  }

  async getAnomalyDetail(id) {
    return this.request(`/anomalies/${id}`);
  }

  async triggerAnomalyScan() {
    return this.request('/anomalies/analyze', { method: 'POST' });
  }

  async updateAnomalyStatus(id, status) {
    return this.request(`/anomalies/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
  }

  // Predictions
  async getPredictions(buildingId = 'ALL', resource = 'electricity', hours = 24) {
    return this.request(`/predictions?building_id=${buildingId}&resource=${resource}&hours=${hours}`);
  }

  // Recommendations
  async getRecommendations(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/recommendations?${query}`);
  }

  async generateRecommendations() {
    return this.request('/recommendations/generate', { method: 'POST' });
  }

  async applyRecommendation(id) {
    return this.request(`/recommendations/${id}/apply`, { method: 'POST' });
  }

  async dismissRecommendation(id) {
    return this.request(`/recommendations/${id}/dismiss`, { method: 'PUT' });
  }

  // What-If Simulator
  async getSimulationPresets() {
    return this.request('/simulator/presets');
  }

  async runSimulation(payload) {
    return this.request('/simulator/run', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async compareScenarios(payload) {
    return this.request('/simulator/compare', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // Sustainability
  async getSustainabilityOverview() {
    return this.request('/sustainability');
  }

  async getBuildingSustainability(buildingId) {
    return this.request(`/sustainability/${buildingId}`);
  }

  // Alerts
  async getAlerts() {
    return this.request('/alerts');
  }

  async markAlertRead(id) {
    return this.request(`/alerts/${id}/read`, { method: 'PUT' });
  }

  async markAllAlertsRead() {
    return this.request('/alerts/read-all', { method: 'PUT' });
  }

  // Reports
  async getReports() {
    return this.request('/reports');
  }

  async getImpactSummary() {
    return this.request('/reports/impact-summary');
  }

  async generateReport(reportType, format = 'PDF') {
    return this.request('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({ report_type: reportType, format })
    });
  }

  // Data Upload & Ingestion
  async uploadCSV(formData) {
    return this.request('/data/upload', {
      method: 'POST',
      body: formData
    });
  }

  async getDataStats() {
    return this.request('/data/stats');
  }

  // Chatbot
  async sendChatMessage(message) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  }

  // Demo Mode
  async getDemoStatus() {
    return this.request('/demo/status');
  }

  async toggleDemoMode(demoMode = null) {
    return this.request('/demo/toggle', {
      method: 'POST',
      body: JSON.stringify({ demo_mode: demoMode })
    });
  }

  async triggerDemoTick() {
    return this.request('/demo/tick', { method: 'POST' });
  }

  async injectAnomaly(buildingId, resource = 'electricity', spikePct = 42.0) {
    return this.request('/demo/inject-anomaly', {
      method: 'POST',
      body: JSON.stringify({ building_id: buildingId, resource, spike_pct: spikePct })
    });
  }
}

window.api = new ApiClient();
