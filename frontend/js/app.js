// EcoCampus AI - Main Application Controller
document.addEventListener('DOMContentLoaded', () => {
  window.app = new EcoCampusApp();
  window.app.init();
});

class EcoCampusApp {
  constructor() {
    this.currentView = 'dashboard';
    this.activeBuildingId = 'ALL';
    this.activeTimeRange = '24h';
    this.isDemoMode = true;
    this.demoTimer = null;
    this.buildingsCache = [];
  }

  async init() {
    this.bindEvents();
    this.setupAuthUI();
    this.checkLandingRoute();
    await this.loadInitialData();
    this.startDemoTicker();
  }

  checkLandingRoute() {
    const hasVisited = sessionStorage.getItem('ecocampus_entered');
    const landing = document.getElementById('landing-view');
    if (hasVisited) {
      landing.classList.add('hidden');
    } else {
      landing.classList.remove('hidden');
    }
  }

  enterDashboard() {
    sessionStorage.setItem('ecocampus_entered', 'true');
    const landing = document.getElementById('landing-view');
    landing.classList.add('hidden');
    this.navigateTo('dashboard');
  }

  showLanding() {
    const landing = document.getElementById('landing-view');
    landing.classList.remove('hidden');
  }

  bindEvents() {
    // Navigation items
    document.querySelectorAll('[data-view]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = el.getAttribute('data-view');
        this.navigateTo(targetView);
      });
    });

    // Time range tabs
    document.querySelectorAll('.time-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const parent = tab.parentElement;
        parent.querySelectorAll('.time-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.activeTimeRange = tab.getAttribute('data-range') || '24h';
        this.refreshCurrentView();
      });
    });

    // Building selector in topbar
    const bldgSelect = document.getElementById('topbar-building-select');
    if (bldgSelect) {
      bldgSelect.addEventListener('change', (e) => {
        this.activeBuildingId = e.target.value;
        this.refreshCurrentView();
      });
    }

    // Demo Mode toggle
    const demoLiveToggle = document.getElementById('demo-mode-toggle');
    if (demoLiveToggle) {
      demoLiveToggle.addEventListener('click', () => this.toggleDemoMode());
    }

    // Chatbot floating triggers
    const chatBtn = document.getElementById('chatbot-toggle-btn');
    const chatWindow = document.getElementById('chatbot-window');
    const chatClose = document.getElementById('chat-close-btn');
    if (chatBtn && chatWindow) {
      chatBtn.addEventListener('click', () => chatWindow.classList.toggle('open'));
      chatClose?.addEventListener('click', () => chatWindow.classList.remove('open'));
    }

    // Chat input
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.sendChatMessage();
      });
    }

    // Quick chip questions
    document.querySelectorAll('.chat-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.innerText;
        const input = document.getElementById('chat-input');
        if (input) {
          input.value = text;
          this.sendChatMessage();
        }
      });
    });

    // Mobile sidebar toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    if (mobileMenuBtn && sidebar) {
      mobileMenuBtn.addEventListener('click', () => sidebar.classList.toggle('mobile-open'));
    }

    // CSV Drag & Drop
    this.setupCsvUploadEvents();
  }

  setupAuthUI() {
    const user = window.api.user;
    const nameEl = document.getElementById('current-user-name');
    const roleEl = document.getElementById('current-user-role');
    const avatarEl = document.getElementById('current-user-avatar');

    if (user && nameEl) {
      nameEl.innerText = user.name;
      roleEl.innerText = user.role === 'admin' ? 'Facility Director (Admin)' : 'Campus Manager';
      avatarEl.innerText = user.name.charAt(0);
    }
  }

  async loadInitialData() {
    try {
      const bRes = await window.api.getBuildings();
      if (bRes.success) {
        this.buildingsCache = bRes.buildings;
        this.populateBuildingDropdown(bRes.buildings);
      }
      await this.loadDashboard();
      await this.loadAlertsBadge();
    } catch (err) {
      console.warn('Initialization notice:', err);
    }
  }

  populateBuildingDropdown(buildings) {
    const select = document.getElementById('topbar-building-select');
    if (!select) return;
    select.innerHTML = '<option value="ALL">🏢 All Buildings (Campus)</option>';
    buildings.forEach(b => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.innerText = `${b.name} (${b.id})`;
      select.appendChild(opt);
    });
  }

  navigateTo(viewName, meta = null) {
    this.currentView = viewName;
    document.querySelectorAll('.sidebar .nav-item').forEach(item => {
      if (item.getAttribute('data-view') === viewName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
      targetSection.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Close mobile drawer
    document.querySelector('.sidebar')?.classList.remove('mobile-open');

    // Route-specific loader
    switch (viewName) {
      case 'dashboard': this.loadDashboard(); break;
      case 'buildings': this.loadBuildingsView(meta); break;
      case 'energy': this.loadEnergyView(); break;
      case 'water': this.loadWaterView(); break;
      case 'anomalies': this.loadAnomaliesView(); break;
      case 'predictions': this.loadPredictionsView(); break;
      case 'recommendations': this.loadRecommendationsView(); break;
      case 'simulator': this.loadSimulatorView(meta); break;
      case 'sustainability': this.loadSustainabilityView(); break;
      case 'reports': this.loadReportsView(); break;
      case 'data': this.loadDataView(); break;
      case 'alerts': this.loadAlertsView(); break;
    }
  }

  refreshCurrentView() {
    this.navigateTo(this.currentView);
  }

  // --- 1. DASHBOARD MODULE ---
  async loadDashboard() {
    try {
      const [energyData, waterData, anomaliesData, susData, recsData] = await Promise.all([
        window.api.getEnergyOverview(this.activeTimeRange, this.activeBuildingId),
        window.api.getWaterOverview(this.activeTimeRange, this.activeBuildingId),
        window.api.getAnomalies({ status: 'ACTIVE' }),
        window.api.getSustainabilityOverview(),
        window.api.getRecommendations({ status: 'PENDING' })
      ]);

      // KPIs
      this.animateValue('kpi-elec-val', energyData.kpis.total_consumption_kwh, ' kWh');
      this.animateValue('kpi-water-val', waterData.kpis.daily_water_usage_liters, ' L');
      this.animateValue('kpi-anom-val', anomaliesData.total, '');
      this.animateValue('kpi-waste-val', energyData.kpis.predicted_waste_kwh, ' kWh');
      this.animateValue('kpi-cost-val', '₹' + Math.round(energyData.kpis.estimated_cost_inr).toLocaleString(), '');
      this.animateValue('kpi-sus-val', susData.sustainability.overall_score, '/100');

      // Trend Chart
      window.ChartManager.renderTrendChart(
        'dashboard-trend-chart',
        energyData.charts.labels,
        energyData.charts.actual,
        energyData.charts.predicted,
        energyData.charts.baseline,
        'kWh'
      );

      // Distribution Chart
      const bNames = energyData.building_comparison.map(b => b.building_name);
      const bKwh = energyData.building_comparison.map(b => b.total_kwh);
      window.ChartManager.renderDistributionChart('dashboard-dist-chart', bNames, bKwh, 'kWh');

      // Campus Electricity Losses & Wastage Intelligence
      if (energyData.loss_intelligence) {
        this.renderLossIntelligence(energyData.loss_intelligence);
      }

      // Render Top Recommendations
      this.renderDashboardRecommendations(recsData.recommendations.slice(0, 3));

      // Render Campus Map Status
      this.renderCampusMap();

    } catch (err) {
      console.error('Failed loading dashboard:', err);
    }
  }

  // --- 1.1 LOSS INTELLIGENCE & WASTAGE MODULE ---
  renderLossIntelligence(lossIntel) {
    if (!lossIntel) return;

    // 1. Core Financial Wastage KPIs
    const dailyKwh = lossIntel.total_loss_kwh || 0;
    const dailyInr = lossIntel.daily_financial_loss_inr || 0;
    const monthlyInr = lossIntel.monthly_financial_loss_inr || 0;
    const annualInr = lossIntel.annual_financial_loss_inr || 0;

    const elKwh = document.getElementById('loss-daily-kwh');
    const elDailyInr = document.getElementById('loss-daily-inr');
    const elMonthlyInr = document.getElementById('loss-monthly-inr');
    const elAnnualInr = document.getElementById('loss-annual-inr');

    if (elKwh) elKwh.innerText = Number(dailyKwh).toFixed(1);
    if (elDailyInr) elDailyInr.innerText = '₹' + Math.round(dailyInr).toLocaleString();
    if (elMonthlyInr) elMonthlyInr.innerText = '₹' + Math.round(monthlyInr).toLocaleString();
    if (elAnnualInr) {
      elAnnualInr.innerText = annualInr >= 100000 
        ? '₹' + (annualInr / 100000).toFixed(2) + ' Lakhs' 
        : '₹' + Math.round(annualInr).toLocaleString();
    }

    // 2. Primary Causes / Categories Breakdown Cards
    const catContainer = document.getElementById('loss-categories-container');
    if (catContainer && lossIntel.categories && lossIntel.categories.length > 0) {
      const borderColors = ['#ef4444', '#f97316', '#f59e0b', '#60a5fa'];
      catContainer.innerHTML = lossIntel.categories.map((c, i) => {
        const borderColor = borderColors[i % borderColors.length];
        return `
          <div class="factor-card" style="border-left: 3px solid ${borderColor};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="factor-name">${c.category}</span>
              <span class="factor-weight" style="color:${borderColor}; font-weight:800;">${c.loss_pct}%</span>
            </div>
            <div style="font-size:0.82rem; font-weight:700; color:#f8fafc; margin:4px 0;">
              ${c.loss_kwh} kWh/day • ₹${Math.round(c.loss_inr).toLocaleString()}/day loss
            </div>
            <p style="font-size:0.72rem; color:#94a3b8; margin:0;">${c.cause}</p>
          </div>
        `;
      }).join('');
    }

    // 3. Facility Financial Loss Leaderboard Table
    const tbody = document.getElementById('loss-leaderboard-tbody');
    if (tbody && lossIntel.building_loss_rankings) {
      tbody.innerHTML = lossIntel.building_loss_rankings.map((b, idx) => {
        const rank = idx + 1;
        const rankBadge = rank === 1 
          ? '<span style="background:rgba(239,68,68,0.25); color:#f87171; font-weight:800; padding:2px 8px; border-radius:4px;">#1 HIGH LOSS</span>'
          : (rank === 2 ? '<span style="background:rgba(249,115,22,0.25); color:#fb923c; font-weight:700; padding:2px 8px; border-radius:4px;">#2</span>'
          : `<span style="color:#94a3b8; font-weight:600;">#${rank}</span>`);

        const severityBadge = b.severity === 'CRITICAL'
          ? '<span class="badge-status badge-critical">CRITICAL</span>'
          : (b.severity === 'HIGH' ? '<span class="badge-status badge-warning">HIGH</span>' : '<span class="badge-status badge-normal">MODERATE</span>');

        return `
          <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
            <td style="padding:10px;">${rankBadge}</td>
            <td style="padding:10px;">
              <div style="font-weight:700; color:#f8fafc;">${b.building_name}</div>
              <div style="font-size:0.72rem; color:#64748b;">${b.building_id}</div>
            </td>
            <td style="padding:10px; color:#cbd5e1;">${b.total_kwh.toLocaleString()} kWh</td>
            <td style="padding:10px; font-weight:700; color:#f87171;">${b.wasted_kwh.toLocaleString()} kWh</td>
            <td style="padding:10px;">
              <div style="display:flex; align-items:center; gap:6px;">
                <span style="font-weight:700; color:${b.waste_pct >= 13 ? '#ef4444' : '#f59e0b'};">${b.waste_pct}%</span>
                <div style="width:50px; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden;">
                  <div style="width:${Math.min(100, b.waste_pct * 5)}%; height:100%; background:${b.waste_pct >= 13 ? '#ef4444' : '#f59e0b'};"></div>
                </div>
              </div>
            </td>
            <td style="padding:10px; font-weight:700; color:#ef4444;">₹${Math.round(b.daily_loss_inr).toLocaleString()}</td>
            <td style="padding:10px; color:#fb923c;">₹${Math.round(b.monthly_loss_inr).toLocaleString()}</td>
            <td style="padding:10px;">${severityBadge}</td>
            <td style="padding:10px; text-align:right;">
              <button class="btn btn-purple btn-sm" onclick="app.navigateTo('simulator', { buildingId: '${b.building_id}' })" style="padding:4px 10px; font-size:0.75rem;">
                ⚡ Fix / Simulate
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }
  }

  renderDashboardRecommendations(recs) {
    const container = document.getElementById('dashboard-recs-container');
    if (!container) return;

    if (!recs || recs.length === 0) {
      container.innerHTML = '<p class="text-muted">No pending recommendations. All systems optimal.</p>';
      return;
    }

    container.innerHTML = recs.map(r => `
      <div class="recommendation-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h4 style="font-size:0.92rem; font-weight:700; color:#f8fafc;">${r.action}</h4>
          <span class="badge badge-normal" style="background:rgba(124,58,237,0.15); color:#c084fc;">AI Confidence: ${r.confidence}%</span>
        </div>
        <p style="font-size:0.8rem; color:#94a3b8; margin: 6px 0;">${r.reason}</p>
        <div class="impact-strip">
          <div class="impact-box"><div class="lbl">Energy Saved</div><div class="val">${r.energy_saving} kWh/day</div></div>
          <div class="impact-box"><div class="lbl">Cost Saved</div><div class="val">₹${r.cost_saving}/day</div></div>
          <div class="impact-box"><div class="lbl">CO₂ Reduction</div><div class="val">${r.co2_reduction} kg/mo</div></div>
          <div class="impact-box"><div class="lbl">Building</div><div class="val" style="color:#60a5fa;">${r.building_name}</div></div>
        </div>
        <div style="display:flex; gap:8px; margin-top:10px;">
          <button class="btn btn-purple btn-sm" onclick="app.navigateTo('simulator', { buildingId: '${r.building_id}' })">
            <i data-lucide="play-circle"></i> Simulate Action
          </button>
          <button class="btn btn-primary btn-sm" onclick="app.applyRecommendation(${r.id})">
            <i data-lucide="check"></i> Apply Decision
          </button>
        </div>
      </div>
    `).join('');
  }

  // --- 2. CAMPUS MAP MODULE ---
  renderCampusMap() {
    const container = document.getElementById('campus-map-interactive');
    if (!container || !this.buildingsCache.length) return;

    const bldgs = this.buildingsCache;
    const cols = 4;
    const cardW = 175;
    const cardH = 75;
    const gapX = 18;
    const gapY = 18;
    const startX = 20;
    const startY = 25;
    const totalRows = Math.ceil(bldgs.length / cols);
    const svgHeight = Math.max(370, startY + totalRows * (cardH + gapY) + 20);

    let svgHtml = `
      <svg viewBox="0 0 800 ${svgHeight}" class="campus-map-svg" style="min-height:370px;">
        <defs>
          <linearGradient id="grid-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#10b981" stop-opacity="0.05"/>
            <stop offset="1%" stop-color="#064e3b" stop-opacity="0.02"/>
          </linearGradient>
        </defs>
        <rect width="800" height="${svgHeight}" fill="url(#grid-grad)"/>
    `;

    bldgs.forEach((bData, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      const posX = startX + col * (cardW + gapX);
      const posY = startY + row * (cardH + gapY);

      let statusColor = '#10b981'; // normal
      if (bData.status === 'critical') {
        statusColor = '#ef4444';
      } else if (bData.status === 'warning') {
        statusColor = '#f59e0b';
      }

      const shortName = bData.name.length > 22 ? bData.name.substring(0, 20) + '...' : bData.name;

      svgHtml += `
        <g class="map-building-node" onclick="app.showBuildingModal('${bData.id}')">
          <rect x="${posX}" y="${posY}" width="${cardW}" height="${cardH}" rx="10" 
            fill="rgba(16, 27, 30, 0.9)" stroke="${statusColor}" stroke-width="1.8" filter="drop-shadow(0 4px 10px rgba(0,0,0,0.5))"/>
          <circle cx="${posX + 16}" cy="${posY + 18}" r="5" fill="${statusColor}"/>
          <text x="${posX + 28}" y="${posY + 22}" fill="#f8fafc" font-size="10" font-weight="700" font-family="Inter">${shortName}</text>
          <text x="${posX + 14}" y="${posY + 44}" fill="#94a3b8" font-size="8.5" font-family="Inter">⚡ ${bData.current_electricity_kwh || 0} kWh | 💧 ${bData.current_water_liters || 0} L</text>
          <text x="${posX + 14}" y="${posY + 60}" fill="${statusColor}" font-size="8" font-weight="700" font-family="Inter">${(bData.status || 'NORMAL').toUpperCase()}</text>
        </g>
      `;
    });

    svgHtml += `</svg>`;
    container.innerHTML = svgHtml;
  }

  // --- 3. BUILDINGS MODULE ---
  async loadBuildingsView(filterId = null) {
    try {
      const res = await window.api.getBuildings();
      if (!res.success) return;
      const container = document.getElementById('buildings-cards-grid');
      if (!container) return;

      container.innerHTML = res.buildings.map(b => {
        let badgeClass = 'badge-normal';
        if (b.status === 'critical') badgeClass = 'badge-critical';
        else if (b.status === 'warning') badgeClass = 'badge-warning';

        return `
          <div class="card building-card" onclick="app.showBuildingModal('${b.id}')">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <h3 style="font-size:1.05rem; font-weight:700; color:#f8fafc;">${b.name}</h3>
                <span style="font-size:0.75rem; color:#64748b;">${b.building_type} • ${b.area_sqft.toLocaleString()} sq ft</span>
              </div>
              <span class="badge-status ${badgeClass}">${b.status}</span>
            </div>
            
            <div class="building-card-metrics">
              <div class="metric-item-mini">
                <span class="label">Electricity</span>
                <span class="val">⚡ ${b.current_electricity_kwh} kWh</span>
              </div>
              <div class="metric-item-mini">
                <span class="label">Water</span>
                <span class="val">💧 ${b.current_water_liters} L</span>
              </div>
              <div class="metric-item-mini">
                <span class="label">Occupancy</span>
                <span class="val">👥 ${b.current_occupancy} (${b.occupancy_percentage}%)</span>
              </div>
              <div class="metric-item-mini">
                <span class="label">Sustainability</span>
                <span class="val" style="color:#10b981;">🌿 ${b.sustainability_score}/100</span>
              </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; color:#94a3b8; border-top: 1px solid var(--border-color); padding-top:10px;">
              <span>Active Anomalies: <b style="color:${b.active_anomalies > 0 ? '#ef4444' : '#10b981'}">${b.active_anomalies}</b></span>
              <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); app.showBuildingModal('${b.id}')">
                Inspect Details →
              </button>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error(err);
    }
  }

  async showBuildingModal(buildingId) {
    try {
      const data = await window.api.getBuildingDetail(buildingId);
      if (!data.success) return;

      const modal = document.getElementById('building-detail-modal');
      const content = document.getElementById('building-modal-content');
      if (!modal || !content) return;

      const b = data.building;
      const k = data.kpis;

      content.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <div>
            <h2 style="font-size:1.35rem; font-weight:800; color:#f8fafc;">${b.name} (${b.id})</h2>
            <span style="font-size:0.8rem; color:#94a3b8;">${b.building_type} | Floors: ${b.floors} | Capacity: ${b.capacity} occupants</span>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('building-detail-modal').classList.remove('open')">✕ Close</button>
        </div>

        <div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom:16px;">
          <div class="kpi-card" style="padding:12px;"><div class="kpi-label">Current Load</div><div class="kpi-value" style="font-size:1.25rem;">${k.current_electricity_kwh} <span class="kpi-unit">kWh</span></div></div>
          <div class="kpi-card" style="padding:12px;"><div class="kpi-label">Daily Load</div><div class="kpi-value" style="font-size:1.25rem;">${k.daily_electricity_kwh} <span class="kpi-unit">kWh</span></div></div>
          <div class="kpi-card" style="padding:12px;"><div class="kpi-label">Peak Demand</div><div class="kpi-value" style="font-size:1.25rem;">${k.peak_load_kw} <span class="kpi-unit">kW</span></div></div>
          <div class="kpi-card" style="padding:12px;"><div class="kpi-label">Daily Water</div><div class="kpi-value" style="font-size:1.25rem;">${k.daily_water_liters} <span class="kpi-unit">L</span></div></div>
        </div>

        <div style="display:flex; gap:10px; margin-top:16px;">
          <button class="btn btn-purple" onclick="app.navigateTo('simulator', { buildingId: '${b.id}' }); document.getElementById('building-detail-modal').classList.remove('open');">
            ⚡ Run What-If Simulator for ${b.name}
          </button>
          <button class="btn btn-secondary" onclick="app.navigateTo('anomalies', { buildingId: '${b.id}' }); document.getElementById('building-detail-modal').classList.remove('open');">
            🔍 View Anomalies (${data.anomalies.length})
          </button>
        </div>
      `;

      modal.classList.add('open');
    } catch (err) {
      console.error(err);
    }
  }

  // --- 4. ENERGY MODULE ---
  async loadEnergyView() {
    try {
      const data = await window.api.getEnergyOverview(this.activeTimeRange, this.activeBuildingId);
      if (!data.success) return;

      this.animateValue('energy-current-load', data.kpis.current_load_kw, ' kW');
      this.animateValue('energy-peak-load', data.kpis.peak_load_kw, ' kW');
      this.animateValue('energy-avg-load', data.kpis.average_load_kw, ' kW');
      this.animateValue('energy-waste-val', data.kpis.predicted_waste_kwh, ' kWh');
      this.animateValue('energy-cost-val', '₹' + Math.round(data.kpis.estimated_cost_inr).toLocaleString(), '');

      // Loss KPIs in Energy View
      if (data.kpis.daily_loss_inr !== undefined) {
        this.animateValue('energy-daily-loss-val', '₹' + Math.round(data.kpis.daily_loss_inr).toLocaleString(), '');
        this.animateValue('energy-monthly-loss-val', '₹' + Math.round(data.kpis.monthly_loss_inr).toLocaleString(), '');
      }

      window.ChartManager.renderTrendChart(
        'energy-main-chart',
        data.charts.labels,
        data.charts.actual,
        data.charts.predicted,
        data.charts.baseline,
        'kWh'
      );

      // Hourly Electricity Loss Bleed Chart
      if (data.charts.loss && document.getElementById('energy-loss-chart')) {
        window.ChartManager.renderLossChart(
          'energy-loss-chart',
          data.charts.labels,
          data.charts.loss,
          'kWh'
        );
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- 5. WATER MODULE ---
  async loadWaterView() {
    try {
      const data = await window.api.getWaterOverview(this.activeTimeRange, this.activeBuildingId);
      if (!data.success) return;

      this.animateValue('water-daily-val', data.kpis.daily_water_usage_liters, ' L');
      this.animateValue('water-peak-val', data.kpis.peak_usage_liters, ' L');
      this.animateValue('water-flow-rate', data.kpis.current_flow_rate_lpm, ' L/min');
      this.animateValue('water-risk-level', data.kpis.leakage_risk_level, '');

      window.ChartManager.renderTrendChart(
        'water-main-chart',
        data.charts.labels,
        data.charts.actual,
        data.charts.predicted,
        data.charts.baseline,
        'L'
      );
    } catch (err) {
      console.error(err);
    }
  }

  // --- 6. ANOMALIES & EXPLAINABLE AI MODULE ---
  async loadAnomaliesView() {
    try {
      const res = await window.api.getAnomalies();
      if (!res.success) return;

      const container = document.getElementById('anomalies-timeline-container');
      if (!container) return;

      if (!res.anomalies.length) {
        container.innerHTML = '<p class="text-muted">No anomalies flagged. All readings are nominal.</p>';
        return;
      }

      container.innerHTML = res.anomalies.map(a => {
        const factors = a.contributing_factors || [];
        const causes = a.possible_causes || [];

        return `
          <div class="anomaly-item ${a.severity.toLowerCase()} card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
              <div>
                <span class="badge-status badge-${a.severity.toLowerCase()}">${a.severity}</span>
                <h3 style="font-size:1.1rem; font-weight:800; color:#f8fafc; margin-top:6px;">
                  ${a.building_name} (${a.resource_type.toUpperCase()})
                </h3>
                <span style="font-size:0.75rem; color:#94a3b8;">Detected: ${a.detected_at} • Status: <b>${a.status}</b></span>
              </div>
              <div style="text-align:right;">
                <div style="font-size:1.35rem; font-weight:800; color:${a.deviation > 0 ? '#ef4444' : '#10b981'};">
                  ${a.deviation > 0 ? '+' : ''}${a.deviation}%
                </div>
                <span style="font-size:0.75rem; color:#94a3b8;">Expected: ${a.expected_value} vs Actual: ${a.actual_value}</span>
              </div>
            </div>

            <!-- Explainable AI Trigger Section -->
            <button class="explain-toggle-btn" onclick="app.toggleExplainDrawer('explain-${a.id}')">
              <i data-lucide="brain-circuit"></i> WHY DID AI DETECT THIS? (Explain Prediction)
            </button>

            <!-- Expandable XAI Drawer -->
            <div id="explain-${a.id}" class="explain-drawer">
              <div style="background:rgba(124, 58, 237, 0.08); border: 1px solid rgba(124, 58, 237, 0.2); border-radius:8px; padding:12px; margin-bottom:12px;">
                <h4 style="font-size:0.85rem; font-weight:700; color:#c084fc; margin-bottom:4px;">
                  🤖 AI Diagnostic Breakdown & Root Cause:
                </h4>
                <p style="font-size:0.82rem; color:#cbd5e1; line-height:1.4;">${a.ai_explanation || 'Multivariate anomaly detected by Isolation Forest with excessive baseline deviation.'}</p>
              </div>

              <h5 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:#94a3b8;">
                Contributing Factor Decomposition (Feature Weights):
              </h5>
              <div class="factors-grid">
                ${factors.map(f => `
                  <div class="factor-card">
                    <div class="factor-name">${f.factor}</div>
                    <div class="factor-weight">${f.weight_pct}%</div>
                    <div class="factor-impact impact-${f.impact}">Impact: ${f.impact}</div>
                    <div style="font-size:0.68rem; color:#94a3b8; margin-top:4px;">Expected: ${f.expected} | Actual: ${f.actual}</div>
                  </div>
                `).join('')}
              </div>

              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; padding-top:10px; border-top:1px solid var(--border-color);">
                <span style="font-size:0.75rem; color:#a78bfa; font-weight:600;">✨ Model Confidence: 92%</span>
                <button class="btn btn-purple btn-sm" onclick="app.navigateTo('simulator', { buildingId: '${a.building_id}' })">
                  Simulate Corrective Action →
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error(err);
    }
  }

  toggleExplainDrawer(drawerId) {
    const el = document.getElementById(drawerId);
    if (el) el.classList.toggle('open');
  }

  async triggerAnomalyScan() {
    this.showToast('Initiating Isolation Forest full campus scan...', 'info');
    try {
      const res = await window.api.triggerAnomalyScan();
      if (res.success) {
        this.showToast(res.message, 'success');
        await this.loadAnomaliesView();
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // --- 7. PREDICTIONS MODULE ---
  async loadPredictionsView() {
    try {
      const res = await window.api.getPredictions(this.activeBuildingId, 'electricity', 24);
      if (!res.success) return;

      const f = res.forecast;
      this.animateValue('pred-total-val', f.total_predicted, ' kWh');
      this.animateValue('pred-waste-val', f.expected_waste, ' kWh');
      this.animateValue('pred-conf-val', f.average_confidence, '%');
      this.animateValue('pred-cost-val', '₹' + Math.round(f.estimated_cost).toLocaleString(), '');

      const labels = f.hourly_forecast.map(h => h.hour_label);
      const predicted = f.hourly_forecast.map(h => h.predicted);
      const baseline = f.hourly_forecast.map(h => h.baseline);

      window.ChartManager.renderTrendChart(
        'predictions-main-chart',
        labels,
        predicted,
        predicted,
        baseline,
        'kWh'
      );
    } catch (err) {
      console.error(err);
    }
  }

  // --- 8. AI RECOMMENDATIONS MODULE ---
  async loadRecommendationsView() {
    try {
      const res = await window.api.getRecommendations();
      if (!res.success) return;
      const container = document.getElementById('recommendations-list-container');
      if (!container) return;

      container.innerHTML = res.recommendations.map(r => `
        <div class="recommendation-card">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <span class="badge" style="background:rgba(124,58,237,0.2); color:#c084fc; font-weight:700;">
                AI Confidence: ${r.confidence}%
              </span>
              <h3 style="font-size:1.1rem; font-weight:800; color:#f8fafc; margin-top:6px;">${r.action}</h3>
              <p style="font-size:0.85rem; color:#94a3b8; margin: 4px 0;">${r.reason}</p>
            </div>
            <span class="badge-status ${r.status === 'APPLIED' ? 'badge-normal' : 'badge-warning'}">${r.status}</span>
          </div>

          <div class="impact-strip">
            <div class="impact-box"><div class="lbl">Daily Energy Saved</div><div class="val">${r.energy_saving} kWh/day</div></div>
            <div class="impact-box"><div class="lbl">Daily Cost Avoidance</div><div class="val">₹${r.cost_saving}/day</div></div>
            <div class="impact-box"><div class="lbl">CO₂ Abatement</div><div class="val">${r.co2_reduction} kg/mo</div></div>
            <div class="impact-box"><div class="lbl">Facility Scope</div><div class="val" style="color:#60a5fa;">${r.building_name}</div></div>
          </div>

          <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:6px; font-size:0.78rem; color:#cbd5e1; margin-bottom:12px;">
            <b>Explanation:</b> ${r.explanation || 'Optimizes energy efficiency setpoints to match operational timetable.'}
          </div>

          <div style="display:flex; gap:10px;">
            <button class="btn btn-purple" onclick="app.navigateTo('simulator', { buildingId: '${r.building_id}' })">
              ⚡ Simulate Before Implementation
            </button>
            ${r.status === 'PENDING' ? `
              <button class="btn btn-primary" onclick="app.applyRecommendation(${r.id})">
                ✓ Apply Decision
              </button>
              <button class="btn btn-secondary" onclick="app.dismissRecommendation(${r.id})">
                Dismiss
              </button>
            ` : '<span style="color:#10b981; font-size:0.85rem; font-weight:600; padding:8px 0;">✓ Applied in Facility Logs</span>'}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  }

  async applyRecommendation(id) {
    try {
      const res = await window.api.applyRecommendation(id);
      if (res.success) {
        this.showToast(res.message, 'success');
        this.refreshCurrentView();
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async dismissRecommendation(id) {
    try {
      const res = await window.api.dismissRecommendation(id);
      if (res.success) {
        this.showToast('Recommendation dismissed', 'info');
        this.refreshCurrentView();
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // --- 9. AI WHAT-IF DECISION SIMULATOR MODULE ---
  async loadSimulatorView(meta = null) {
    try {
      const bldgSelect = document.getElementById('sim-building-select');
      if (bldgSelect && this.buildingsCache.length) {
        bldgSelect.innerHTML = this.buildingsCache.map(b => `
          <option value="${b.id}" ${meta && meta.buildingId === b.id ? 'selected' : ''}>${b.name} (${b.id})</option>
        `).join('');
      }

      // Automatically run baseline simulation on open
      this.runSimulation();
      this.runScenarioComparison();
    } catch (err) {
      console.error(err);
    }
  }

  async runSimulation() {
    const buildingId = document.getElementById('sim-building-select')?.value || 'BLK-A';
    const action = document.getElementById('sim-action-select')?.value || 'reduce_ac_1h';
    const duration = parseFloat(document.getElementById('sim-duration-slider')?.value || 1.0);
    const temperature = parseFloat(document.getElementById('sim-temp-input')?.value || 32.0);

    try {
      const res = await window.api.runSimulation({
        building_id: buildingId,
        action: action,
        duration_hours: duration,
        temperature: temperature
      });

      if (!res.success) return;
      const r = res.result;
      const tp = r.thermal_penalty || {};
      const isCoolBonus = tp.is_cool_bonus || (tp.delta_temp < 0);
      const isHeatLoss = !isCoolBonus && (tp.delta_temp > 0);

      // Calculations for dual-sided presentation
      const actionKwh = r.action_saved_kwh !== undefined ? r.action_saved_kwh : (r.energy_saved || 0);
      const actionCostDaily = r.action_cost_saved_daily !== undefined ? r.action_cost_saved_daily : (r.cost_saved_daily || 0);
      const actionAnnual = r.action_annual_saving !== undefined ? r.action_annual_saving : (r.annual_saving || 0);

      const coolKwh = isCoolBonus ? (tp.thermal_saving_kwh || 0) : 0;
      const coolCostDaily = isCoolBonus ? (tp.thermal_saving_cost_daily || 0) : 0;
      const coolCostAnnual = isCoolBonus ? (tp.thermal_saving_cost_annual || 0) : 0;

      const totalProfitDaily = r.total_daily_profit !== undefined ? r.total_daily_profit : (actionCostDaily + coolCostDaily);
      const totalProfitAnnual = r.total_annual_profit !== undefined ? r.total_annual_profit : (actionAnnual + coolCostAnnual);
      const totalSavedKwh = r.total_saved_kwh !== undefined ? r.total_saved_kwh : (actionKwh + coolKwh);

      const heatLossKwh = isHeatLoss ? (tp.thermal_loss_kwh || 0) : 0;
      const heatLossCostDaily = isHeatLoss ? (tp.thermal_loss_cost_daily || 0) : 0;

      const dailyConsumptionCost = r.daily_consumption_cost !== undefined ? r.daily_consumption_cost : Math.round(r.simulated_energy * 8.5);
      const annualConsumptionCost = r.annual_consumption_cost !== undefined ? r.annual_consumption_cost : Math.round(dailyConsumptionCost * 365.0);
      const dailyWasteLoss = r.daily_waste_loss !== undefined ? r.daily_waste_loss : Math.round(dailyConsumptionCost * 0.20);

      // 1. DYNAMIC THERMAL & ACTION AUDIT DIAGNOSTIC BANNER (ALWAYS VISIBLE)
      const thermalBanner = document.getElementById('sim-thermal-banner');
      if (thermalBanner) {
        thermalBanner.style.display = 'block';
        const icon = document.getElementById('sim-thermal-icon');
        const badge = document.getElementById('sim-thermal-severity-badge');
        const title = document.getElementById('sim-thermal-title');
        const desc = document.getElementById('sim-thermal-desc');
        const bannerLossInr = document.getElementById('sim-heat-loss-inr-banner');
        const bannerProfitInr = document.getElementById('sim-action-save-inr-banner');
        const bannerNet = document.getElementById('sim-net-balance-banner');
        const lossBoxLbl = document.getElementById('sim-thermal-loss-box-lbl');
        const profitBoxLbl = document.getElementById('sim-thermal-profit-box-lbl');

        if (isCoolBonus) {
          if (icon) icon.innerText = '❄️';
          if (badge) {
            badge.innerText = tp.severity || 'NATURAL COOLING BONUS';
            badge.style.background = '#059669';
          }
          if (title) {
            title.innerText = `Favorable Weather: +${tp.cool_bonus_pct || 0}% Cooling Bonus & Ongoing Power Loss Evaluated`;
            title.style.color = '#34d399';
          }
          if (desc) {
            desc.innerText = `At ${tp.ambient_temperature}°C ambient (${Math.abs(tp.delta_temp)}°C below 25°C design setpoint), natural economizer cooling saves +${coolKwh.toFixed(1)} kWh/day (+₹${Math.round(coolCostDaily).toLocaleString()}/day profit), alongside residual facility power expenditure.`;
          }
          if (lossBoxLbl) lossBoxLbl.innerText = 'Residual Power Loss / Bill';
          if (bannerLossInr) bannerLossInr.innerText = `-₹${Math.round(dailyConsumptionCost).toLocaleString()}/day`;
          if (profitBoxLbl) profitBoxLbl.innerText = 'Total Conservation Profit';
          if (bannerProfitInr) bannerProfitInr.innerText = `+₹${Math.round(totalProfitDaily).toLocaleString()}/day`;
        } else if (isHeatLoss) {
          if (icon) icon.innerText = '🔥';
          if (badge) {
            badge.innerText = tp.severity || 'HIGH THERMAL STRESS';
            badge.style.background = '#dc2626';
          }
          if (title) {
            title.innerText = `Ambient Heat Stress: +${tp.heat_penalty_pct || 0}% Cooling Load Surge & Action Savings Evaluated`;
            title.style.color = '#f87171';
          }
          if (desc) {
            desc.innerText = `At ${tp.ambient_temperature}°C ambient (+${tp.delta_temp}°C above 25°C baseline), HVAC draws +${heatLossKwh.toFixed(1)} kWh/day in heat power bleed (+₹${Math.round(heatLossCostDaily).toLocaleString()}/day loss penalty), weighed against action savings.`;
          }
          if (lossBoxLbl) lossBoxLbl.innerText = 'Thermal Heat Loss Penalty';
          if (bannerLossInr) bannerLossInr.innerText = `-₹${Math.round(heatLossCostDaily).toLocaleString()}/day`;
          if (profitBoxLbl) profitBoxLbl.innerText = 'Intervention Action Profit';
          if (bannerProfitInr) bannerProfitInr.innerText = `+₹${Math.round(actionCostDaily).toLocaleString()}/day`;
        } else {
          if (icon) icon.innerText = '🎯';
          if (badge) {
            badge.innerText = 'OPTIMAL 25°C DESIGN COMFORT';
            badge.style.background = '#7c3aed';
          }
          if (title) {
            title.innerText = 'Equilibrium Baseline: Both Intervention Savings (Profit) and Electricity Loss Evaluated';
            title.style.color = '#cbd5e1';
          }
          if (desc) {
            desc.innerText = `Operating at nominal 25.0°C standard comfort setpoint with 0°C thermal distortion. Action generates direct savings while facility draws regular operational power.`;
          }
          if (lossBoxLbl) lossBoxLbl.innerText = 'Facility Electricity Expense';
          if (bannerLossInr) bannerLossInr.innerText = `-₹${Math.round(dailyConsumptionCost).toLocaleString()}/day`;
          if (profitBoxLbl) profitBoxLbl.innerText = 'Intervention Action Profit';
          if (bannerProfitInr) bannerProfitInr.innerText = `+₹${Math.round(actionCostDaily).toLocaleString()}/day`;
        }

        if (bannerNet) {
          if (r.is_net_loss) {
            bannerNet.innerText = `-₹${Math.round(r.net_financial_loss_daily).toLocaleString()}/day (Deficit)`;
            bannerNet.style.color = '#ef4444';
          } else {
            bannerNet.innerText = `+₹${Math.round(r.net_cost_saved_daily || r.cost_saved_daily).toLocaleString()}/day (Surplus)`;
            bannerNet.style.color = '#10b981';
          }
        }
      }

      // 2. PROFIT / SAVINGS SECTION (GREEN CARDS)
      const elActionCost = document.getElementById('sim-action-cost-val');
      const elActionKwh = document.getElementById('sim-action-kwh-val');
      const elWeatherProfit = document.getElementById('sim-weather-profit-val');
      const elWeatherKwh = document.getElementById('sim-weather-kwh-val');
      const elActionAnnual = document.getElementById('sim-action-annual-val');
      const elTotalSavedKwh = document.getElementById('sim-total-saved-kwh-val');

      if (elActionCost) elActionCost.innerText = `+₹${Math.round(actionCostDaily).toLocaleString()}/day`;
      if (elActionKwh) elActionKwh.innerText = `+${actionKwh.toFixed(1)} kWh/day saved`;

      if (elWeatherProfit) {
        elWeatherProfit.innerText = isCoolBonus 
          ? `+₹${Math.round(coolCostDaily).toLocaleString()}/day` 
          : `₹0/day`;
        elWeatherProfit.style.color = isCoolBonus ? '#10b981' : '#94a3b8';
      }
      if (elWeatherKwh) {
        elWeatherKwh.innerText = isCoolBonus 
          ? `+${coolKwh.toFixed(1)} kWh natural cooling` 
          : `0.0 kWh (ambient ≥ 25°C)`;
        elWeatherKwh.style.color = isCoolBonus ? '#6ee7b7' : '#64748b';
      }

      const elActionAnnualCard = document.getElementById('sim-action-annual-card');
      const elActionAnnualLbl = document.getElementById('sim-action-annual-lbl');
      const netAnnualOutcome = r.net_annual_outcome !== undefined 
        ? r.net_annual_outcome 
        : (r.is_net_loss ? -r.net_financial_loss_annual : (r.net_annual_saving || r.annual_saving || 0));

      if (elActionAnnual) {
        if (netAnnualOutcome >= 0) {
          if (elActionAnnualCard) {
            elActionAnnualCard.style.borderColor = 'rgba(16,185,129,0.45)';
            elActionAnnualCard.style.background = 'rgba(16,185,129,0.05)';
          }
          if (elActionAnnualLbl) {
            elActionAnnualLbl.innerText = '🟢 Net Annual Savings';
            elActionAnnualLbl.style.color = '#10b981';
          }
          elActionAnnual.innerText = netAnnualOutcome >= 100000 
            ? `+₹${(netAnnualOutcome / 100000).toFixed(2)} Lakhs/yr` 
            : `+₹${Math.round(netAnnualOutcome).toLocaleString()}/yr`;
          elActionAnnual.style.color = '#10b981';
          if (elTotalSavedKwh) {
            const actStr = actionAnnual >= 100000 ? `${(actionAnnual / 100000).toFixed(2)}L` : `${Math.round(actionAnnual).toLocaleString()}`;
            elTotalSavedKwh.innerText = `Net Surplus (Action alone: +₹${actStr}/yr)`;
            elTotalSavedKwh.style.color = '#6ee7b7';
          }
        } else {
          const absNetAnnual = Math.abs(netAnnualOutcome);
          if (elActionAnnualCard) {
            elActionAnnualCard.style.borderColor = 'rgba(239,68,68,0.45)';
            elActionAnnualCard.style.background = 'rgba(239,68,68,0.05)';
          }
          if (elActionAnnualLbl) {
            elActionAnnualLbl.innerText = '🔴 Net Annual Savings (Deficit)';
            elActionAnnualLbl.style.color = '#f87171';
          }
          elActionAnnual.innerText = absNetAnnual >= 100000 
            ? `-₹${(absNetAnnual / 100000).toFixed(2)} Lakhs/yr` 
            : `-₹${Math.round(absNetAnnual).toLocaleString()}/yr`;
          elActionAnnual.style.color = '#ef4444';
          if (elTotalSavedKwh) {
            const actStr = actionAnnual >= 100000 ? `${(actionAnnual / 100000).toFixed(2)}L` : `${Math.round(actionAnnual).toLocaleString()}`;
            elTotalSavedKwh.innerText = `Reduced by heat load (Action: +₹${actStr}/yr)`;
            elTotalSavedKwh.style.color = '#fca5a5';
          }
        }
      }

      // 3. LOSS / EXPENDITURE SECTION (RED CARDS - ALWAYS POPULATED)
      const elThermalLossVal = document.getElementById('sim-thermal-loss-val');
      const elThermalKwhVal = document.getElementById('sim-thermal-kwh-val');
      const elConsumptionLossVal = document.getElementById('sim-consumption-loss-val');
      const elSimulatedKwhVal = document.getElementById('sim-simulated-kwh-val');
      const elAnnualLossVal = document.getElementById('sim-annual-loss-val');

      if (elThermalLossVal) {
        elThermalLossVal.innerText = isHeatLoss 
          ? `-₹${Math.round(heatLossCostDaily).toLocaleString()}/day` 
          : `₹0/day (Optimal)`;
        elThermalLossVal.style.color = isHeatLoss ? '#ef4444' : '#94a3b8';
      }
      if (elThermalKwhVal) {
        elThermalKwhVal.innerText = isHeatLoss 
          ? `+${heatLossKwh.toFixed(1)} kWh/day heat bleed` 
          : `0.0 kWh heat penalty`;
        elThermalKwhVal.style.color = isHeatLoss ? '#fca5a5' : '#64748b';
      }

      if (elConsumptionLossVal) {
        elConsumptionLossVal.innerText = `-₹${Math.round(dailyConsumptionCost).toLocaleString()}/day`;
        elConsumptionLossVal.style.color = '#ef4444';
      }
      if (elSimulatedKwhVal) {
        elSimulatedKwhVal.innerText = `${(r.simulated_energy || 0).toFixed(1)} kWh/day consumed`;
      }

      if (elAnnualLossVal) {
        elAnnualLossVal.innerText = annualConsumptionCost >= 100000 
          ? `-₹${(annualConsumptionCost / 100000).toFixed(2)} Lakhs/yr` 
          : `-₹${Math.round(annualConsumptionCost).toLocaleString()}/yr`;
      }

      // 4. NET BOTTOM LINE & SYSTEM HEALTH
      const costSavedLbl = document.getElementById('sim-cost-saved-label');
      const costSavedVal = document.getElementById('sim-cost-saved-val');
      const annualLbl = document.getElementById('sim-annual-label');
      const annualVal = document.getElementById('sim-annual-val');
      const elCopVal = document.getElementById('sim-cop-val');
      const susImpactVal = document.getElementById('sim-sus-impact-val');

      if (r.is_net_loss) {
        if (costSavedLbl) costSavedLbl.innerText = '⚖️ Net Daily Deficit';
        if (costSavedVal) {
          costSavedVal.innerText = `-₹${Math.round(r.net_financial_loss_daily).toLocaleString()}/day`;
          costSavedVal.style.color = '#ef4444';
        }
        if (annualLbl) annualLbl.innerText = '⚖️ Net Annual Deficit';
        if (annualVal) {
          annualVal.innerText = r.net_financial_loss_annual >= 100000 
            ? `-₹${(r.net_financial_loss_annual / 100000).toFixed(2)} Lakhs LOSS` 
            : `-₹${Math.round(r.net_financial_loss_annual).toLocaleString()} LOSS`;
          annualVal.style.color = '#ef4444';
        }
      } else {
        if (costSavedLbl) costSavedLbl.innerText = '⚖️ Net Daily Surplus';
        if (costSavedVal) {
          costSavedVal.innerText = `+₹${Math.round(r.net_cost_saved_daily || r.cost_saved_daily).toLocaleString()}/day`;
          costSavedVal.style.color = '#10b981';
        }
        if (annualLbl) annualLbl.innerText = '⚖️ Net Annual Surplus';
        if (annualVal) {
          const netAnn = r.annual_saving || r.net_annual_saving || 0;
          annualVal.innerText = netAnn >= 100000 
            ? `+₹${(netAnn / 100000).toFixed(2)} Lakhs/yr` 
            : `+₹${Math.round(netAnn).toLocaleString()}/yr`;
          annualVal.style.color = '#10b981';
        }
      }

      if (elCopVal) {
        if (isCoolBonus) {
          elCopVal.innerText = `+${tp.cop_boost_pct || 0}% Boost`;
          elCopVal.style.color = '#10b981';
        } else if (isHeatLoss) {
          elCopVal.innerText = `-${tp.cop_degradation_pct || 0}% Drop`;
          elCopVal.style.color = '#ef4444';
        } else {
          elCopVal.innerText = '100% (Nominal)';
          elCopVal.style.color = '#60a5fa';
        }
      }

      if (susImpactVal) {
        susImpactVal.innerText = `${r.sustainability_impact_points >= 0 ? '+' : ''}${r.sustainability_impact_points} pts`;
        susImpactVal.style.color = r.sustainability_impact_points >= 0 ? '#10b981' : '#ef4444';
      }

      // Toast notification highlighting BOTH Loss and Profit
      if (isHeatLoss) {
        this.showToast(`🔥 Heat stress burns -₹${Math.round(heatLossCostDaily).toLocaleString()}/day loss | Action preserves +₹${Math.round(actionCostDaily).toLocaleString()}/day profit!`, 'warning');
      } else if (isCoolBonus) {
        this.showToast(`❄️ Cool climate yields +₹${Math.round(totalProfitDaily).toLocaleString()}/day profit | Facility power loss is -₹${Math.round(dailyConsumptionCost).toLocaleString()}/day!`, 'success');
      } else {
        this.showToast(`⚡ Nominal 25°C: Action generates +₹${Math.round(actionCostDaily).toLocaleString()}/day profit | Daily power loss is -₹${Math.round(dailyConsumptionCost).toLocaleString()}/day`, 'info');
      }

      // 5. Render BEFORE vs AFTER chart
      window.ChartManager.renderSimulatorComparison(
        'simulator-comparison-chart',
        r.hourly_labels,
        r.hourly_before,
        r.hourly_after
      );

    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  async runScenarioComparison() {
    const buildingId = document.getElementById('sim-building-select')?.value || 'BLK-A';
    const temperature = parseFloat(document.getElementById('sim-temp-input')?.value || 32.0);
    try {
      const res = await window.api.compareScenarios({
        building_id: buildingId,
        temperature: temperature,
        scenarios: [
          { name: 'Scenario A: Reduce AC 1 hr', action: 'reduce_ac_1h', duration: 1.0 },
          { name: 'Scenario B: Reduce AC 2 hrs', action: 'reduce_ac_2h', duration: 2.0 },
          { name: 'Scenario C: Smart Thermostat + Daylight', action: 'optimize_lighting', duration: 8.0 }
        ]
      });

      if (!res.success) return;
      const c = res.comparison;

      const names = c.scenarios.map(s => s.scenario_name);
      const savings = c.scenarios.map(s => s.annual_saving);
      const energy = c.scenarios.map(s => s.energy_saved);

      window.ChartManager.renderScenarioComparisonChart('scenario-bar-chart', names, savings, energy);

      // Best scenario badge & text
      const bestBox = document.getElementById('best-scenario-highlight-box');
      if (bestBox && c.best_scenario) {
        const bestSav = c.best_scenario.annual_saving >= 0 
          ? `+₹${Math.round(c.best_scenario.annual_saving).toLocaleString()} / year`
          : `-₹${Math.round(Math.abs(c.best_scenario.annual_saving)).toLocaleString()} / year (DEFICIT)`;

        bestBox.innerHTML = `
          <div style="background:linear-gradient(135deg, rgba(16,185,129,0.2), rgba(124,58,237,0.15)); border:1px solid #10b981; border-radius:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="badge" style="background:#10b981; color:#0b1315; font-weight:800; font-size:0.8rem;">🏆 AI RECOMMENDED BEST SCENARIO</span>
              <span style="font-size:0.85rem; font-weight:700; color:#10b981;">${bestSav}</span>
            </div>
            <h3 style="font-size:1.15rem; font-weight:800; margin-top:8px; color:#f8fafc;">${c.best_scenario.scenario_name}</h3>
            <p style="font-size:0.85rem; color:#cbd5e1; margin-top:4px;">${c.recommendation_summary}</p>
          </div>
        `;
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- 10. SUSTAINABILITY MODULE ---
  async loadSustainabilityView() {
    try {
      const res = await window.api.getSustainabilityOverview();
      if (!res.success) return;
      const s = res.sustainability;

      this.animateValue('sus-score-big', s.overall_score, '/100');
      document.getElementById('sus-rating-tier').innerText = `Tier: ${s.rating} (Grade ${s.grade})`;

      // Render components breakdown
      const compsContainer = document.getElementById('sus-components-container');
      if (compsContainer) {
        compsContainer.innerHTML = Object.entries(s.components).map(([k, c]) => `
          <div class="card" style="margin-bottom:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <div>
                <h4 style="font-size:0.95rem; font-weight:700; color:#f8fafc;">${c.description}</h4>
                <span style="font-size:0.75rem; color:#64748b;">Weight: ${c.weight_pct}% • Benchmark: ${c.benchmark}</span>
              </div>
              <div style="font-size:1.4rem; font-weight:800; color:#10b981;">${c.score}</div>
            </div>
            <div style="width:100%; height:8px; background:rgba(255,255,255,0.06); border-radius:999px; overflow:hidden;">
              <div style="width:${c.score}%; height:100%; background:linear-gradient(90deg, #10b981, #6ee7b7); border-radius:999px;"></div>
            </div>
          </div>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  // --- 11. REPORTS MODULE ---
  async loadReportsView() {
    try {
      const [reportsData, impactData] = await Promise.all([
        window.api.getReports(),
        window.api.getImpactSummary()
      ]);

      if (impactData.success) {
        const imp = impactData.impact;
        this.animateValue('rep-energy-saved', imp.energy_saved_kwh_month.toLocaleString(), ' kWh');
        this.animateValue('rep-water-saved', imp.water_saved_liters_month.toLocaleString(), ' L');
        this.animateValue('rep-cost-saved', '₹' + Math.round(imp.cost_savings_inr_month).toLocaleString(), '');
        this.animateValue('rep-co2-saved', imp.co2_reduction_kg_month.toLocaleString(), ' kg');
      }

      const tableBody = document.getElementById('reports-table-body');
      if (tableBody && reportsData.success) {
        tableBody.innerHTML = reportsData.reports.map(r => `
          <tr>
            <td style="padding:12px; font-weight:600; color:#f8fafc;">${r.report_type}</td>
            <td style="padding:12px; color:#94a3b8;">${r.period_start || 'Recent'} to ${r.period_end || 'Now'}</td>
            <td style="padding:12px; color:#94a3b8;">${r.generated_by}</td>
            <td style="padding:12px; color:#94a3b8;">${r.created_at}</td>
            <td style="padding:12px;">
              <a href="/api/reports/${r.id}/download" class="btn btn-secondary btn-sm" target="_blank">
                📥 Download
              </a>
            </td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error(err);
    }
  }

  async triggerGenerateReport(type, format = 'PDF') {
    this.showToast(`Generating ${type} (${format})...`, 'info');
    try {
      const res = await window.api.generateReport(type, format);
      if (res.success) {
        this.showToast(res.message, 'success');
        this.loadReportsView();
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // --- 12. DATA MANAGEMENT MODULE ---
  async loadDataView() {
    try {
      const stats = await window.api.getDataStats();
      if (!stats.success) return;

      const grid = document.getElementById('data-stats-grid');
      if (!grid) return;

      grid.innerHTML = Object.entries(stats.categories).map(([k, c]) => `
        <div class="card" style="padding:16px;">
          <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; font-weight:600;">${c.name}</div>
          <div style="font-size:1.6rem; font-weight:800; color:#10b981; margin: 6px 0;">
            ${c.records.toLocaleString()} <span style="font-size:0.8rem; color:#64748b;">${c.unit}</span>
          </div>
          <span class="badge badge-normal">${c.status}</span>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  }

  setupCsvUploadEvents() {
    const dropzone = document.getElementById('csv-dropzone');
    const fileInput = document.getElementById('csv-file-input');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = '#10b981';
      dropzone.style.background = 'rgba(16, 185, 129, 0.08)';
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.style.borderColor = 'var(--border-color)';
      dropzone.style.background = 'none';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-color)';
      dropzone.style.background = 'none';
      if (e.dataTransfer.files.length) {
        this.uploadCsvFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        this.uploadCsvFile(fileInput.files[0]);
      }
    });
  }

  async uploadCsvFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    this.showToast('Validating CSV headers and parsing rows...', 'info');

    try {
      const res = await window.api.uploadCSV(formData);
      if (res.success) {
        this.showToast(`Import Success: ${res.records_inserted} rows ingested into database.`, 'success');
        await this.loadInitialData();
        await this.loadDashboard();
        this.loadDataView();
      }
    } catch (err) {
      this.showToast(`Upload failed: ${err.message}`, 'error');
    }
  }

  // --- 13. ALERTS & BADGES ---
  async loadAlertsBadge() {
    try {
      const res = await window.api.getAlerts();
      if (!res.success) return;
      const badge = document.getElementById('alerts-count-badge');
      if (badge) {
        badge.innerText = res.unread_count;
        badge.style.display = res.unread_count > 0 ? 'flex' : 'none';
      }
    } catch (err) {
      console.warn(err);
    }
  }

  async loadAlertsView() {
    try {
      const res = await window.api.getAlerts();
      if (!res.success) return;
      const list = document.getElementById('alerts-full-list');
      if (!list) return;

      list.innerHTML = res.alerts.map(a => `
        <div class="card" style="margin-bottom:12px; border-left: 4px solid ${a.severity === 'CRITICAL' ? '#ef4444' : (a.severity === 'HIGH' ? '#f59e0b' : '#3b82f6')};">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <span class="badge-status badge-${a.severity.toLowerCase()}">${a.severity}</span>
              <h3 style="font-size:1.05rem; font-weight:700; margin-top:4px; color:#f8fafc;">${a.title}</h3>
              <p style="font-size:0.85rem; color:#94a3b8; margin: 4px 0;">${a.message}</p>
              <span style="font-size:0.75rem; color:#64748b;">${a.created_at} • ${a.building_id}</span>
            </div>
            ${!a.is_read ? `
              <button class="btn btn-secondary btn-sm" onclick="app.markAlertRead(${a.id})">Mark as Read</button>
            ` : '<span style="font-size:0.75rem; color:#10b981;">✓ Read</span>'}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  }

  async markAlertRead(id) {
    try {
      await window.api.markAlertRead(id);
      this.loadAlertsBadge();
      this.loadAlertsView();
    } catch (err) {
      console.error(err);
    }
  }

  // --- 14. CHATBOT ASSISTANT ---
  async sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input?.value.trim();
    if (!msg) return;

    input.value = '';
    const body = document.getElementById('chat-messages-container');
    if (!body) return;

    // User message
    body.innerHTML += `<div class="chat-msg user">${msg}</div>`;
    body.scrollTop = body.scrollHeight;

    // Typing bubble
    const typingId = 'typing-' + Date.now();
    body.innerHTML += `<div id="${typingId}" class="chat-msg bot" style="opacity:0.7;">EcoAI is reasoning...</div>`;
    body.scrollTop = body.scrollHeight;

    try {
      const res = await window.api.sendChatMessage(msg);
      document.getElementById(typingId)?.remove();

      // Convert simple markdown bullets/bold to html
      const formatted = res.response
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/• (.*?)(<br\/>|$)/g, '<li>$1</li>');

      body.innerHTML += `<div class="chat-msg bot">${formatted}</div>`;
      body.scrollTop = body.scrollHeight;
    } catch (err) {
      document.getElementById(typingId)?.remove();
      body.innerHTML += `<div class="chat-msg bot" style="color:#f87171;">Sorry, I encountered an issue accessing the campus metrics engine.</div>`;
    }
  }

  // --- 15. DEMO MODE & LIVE SIMULATOR ---
  startDemoTicker() {
    // Generate new telemetry tick every 45 seconds if demo mode is enabled
    this.demoTimer = setInterval(async () => {
      if (this.isDemoMode) {
        try {
          await window.api.triggerDemoTick();
          if (this.currentView === 'dashboard') {
            this.loadDashboard();
          }
        } catch (e) {
          // Silent ticker error
        }
      }
    }, 45000);
  }

  async toggleDemoMode() {
    this.isDemoMode = !this.isDemoMode;
    const btn = document.getElementById('demo-mode-toggle');
    if (btn) {
      btn.classList.toggle('active', this.isDemoMode);
      btn.innerText = this.isDemoMode ? '● DEMO DATA' : '○ LIVE DATA';
    }
    this.showToast(`Switched to ${this.isDemoMode ? 'DEMO DATA (Simulated)' : 'LIVE DATA (Hardware/IoT)'} Mode`, 'info');
  }

  async injectDemoAnomaly() {
    this.showToast('Injecting abnormal +45% load spike into Academic Block A for presentation demo...', 'info');
    try {
      const res = await window.api.injectAnomaly('BLK-A', 'electricity', 45.0);
      if (res.success) {
        this.showToast(res.message, 'success');
        this.refreshCurrentView();
        this.loadAlertsBadge();
      }
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  }

  // Helper Utilities
  animateValue(elementId, value, unit = '') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerText = `${value}${unit}`;
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `<span>${icon}</span><span style="font-size:0.85rem; color:#f8fafc;">${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}
