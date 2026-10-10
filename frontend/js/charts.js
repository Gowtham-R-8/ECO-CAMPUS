// EcoCampus AI - Chart.js Initialization & Management
const ChartManager = {
  instances: {},

  destroyChart(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  // 1. Dashboard Trend Chart (Actual, Predicted, Baseline)
  renderTrendChart(canvasId, labels, actual, predicted, baseline, unit = 'kWh') {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    // Gradient fills
    const gradActual = ctx.createLinearGradient(0, 0, 0, 300);
    gradActual.addColorStop(0, 'rgba(16, 185, 129, 0.45)');
    gradActual.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    const gradPred = ctx.createLinearGradient(0, 0, 0, 300);
    gradPred.addColorStop(0, 'rgba(124, 58, 237, 0.35)');
    gradPred.addColorStop(1, 'rgba(124, 58, 237, 0.0)');

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual Monitored',
            data: actual,
            borderColor: '#10b981',
            backgroundColor: gradActual,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 2,
            pointHoverRadius: 6
          },
          {
            label: 'AI Predicted Forecast',
            data: predicted,
            borderColor: '#a78bfa',
            backgroundColor: gradPred,
            borderWidth: 2,
            borderDash: [5, 5],
            fill: false,
            tension: 0.35,
            pointRadius: 2
          },
          {
            label: 'Expected Green Baseline',
            data: baseline,
            borderColor: '#60a5fa',
            borderWidth: 1.5,
            borderDash: [3, 3],
            fill: false,
            tension: 0.3,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            titleColor: '#f8fafc',
            bodyColor: '#94a3b8',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toLocaleString()} ${unit}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#64748b', font: { size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b', font: { size: 10 } }
          }
        }
      }
    });
  },

  // 2. Resource Distribution Bar / Donut Chart
  renderDistributionChart(canvasId, buildingNames, values, label = 'kWh') {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    const basePalette = [
      '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b',
      '#ec4899', '#14b8a6', '#06b6d4', '#6366f1',
      '#84cc16', '#f97316', '#a855f7', '#0284c7',
      '#e11d48', '#d97706', '#059669', '#4f46e5'
    ];
    const bgColors = buildingNames.map((_, i) => basePalette[i % basePalette.length]);

    this.instances[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: buildingNames,
        datasets: [{
          data: values,
          backgroundColor: bgColors,
          borderColor: '#0b1315',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#94a3b8', font: { size: 10, family: 'Inter' }, boxWidth: 12 }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toLocaleString()} ${label}`
            }
          }
        },
        cutout: '68%'
      }
    });
  },

  // 3. What-If Simulator Before vs After 24h Comparison
  renderSimulatorComparison(canvasId, labels, beforeVals, afterVals) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Current Baseline (Before)',
            data: beforeVals,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            fill: true,
            borderWidth: 2,
            tension: 0.35,
            pointRadius: 2
          },
          {
            label: 'Simulated Load (After Intervention)',
            data: afterVals,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.25)',
            fill: true,
            borderWidth: 2.5,
            tension: 0.35,
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#94a3b8', font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y} kWh/hr`
            }
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.04)' }, ticks: { color: '#64748b' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#64748b' } }
        }
      }
    });
  },

  // 4. Scenario Bar Chart Comparison
  renderScenarioComparisonChart(canvasId, scenarioNames, annualSavings, energySaved) {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    this.instances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: scenarioNames,
        datasets: [
          {
            label: 'Annual Cost Savings (₹)',
            data: annualSavings,
            backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6'],
            borderRadius: 6,
            yAxisID: 'y'
          },
          {
            label: 'Daily Energy Saved (kWh)',
            data: energySaved,
            type: 'line',
            borderColor: '#f59e0b',
            borderWidth: 2.5,
            pointRadius: 5,
            pointBackgroundColor: '#f59e0b',
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8' } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' } },
          y: {
            position: 'left',
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#10b981', callback: (v) => '₹' + (v / 1000).toFixed(0) + 'k' }
          },
          y1: {
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { color: '#f59e0b', callback: (v) => v + ' kWh' }
          }
        }
      }
    });
  },

  // 5. Electricity Loss & Wastage Curve Chart
  renderLossChart(canvasId, labels, lossData, unit = 'kWh') {
    this.destroyChart(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    const gradLoss = ctx.createLinearGradient(0, 0, 0, 300);
    gradLoss.addColorStop(0, 'rgba(239, 68, 68, 0.5)');
    gradLoss.addColorStop(1, 'rgba(239, 68, 68, 0.02)');

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Active Electricity Loss / Bleed (kWh)',
            data: lossData,
            borderColor: '#ef4444',
            backgroundColor: gradLoss,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: 2,
            pointHoverRadius: 6,
            pointBackgroundColor: '#ef4444'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#f87171', font: { family: 'Inter', size: 11 }, usePointStyle: true }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#f8fafc',
            bodyColor: '#f87171',
            borderColor: 'rgba(239, 68, 68, 0.4)',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              label: (context) => ` Avoidable Loss: ${context.parsed.y.toLocaleString()} ${unit} (₹${(context.parsed.y * 7.5).toFixed(2)} waste)`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { color: '#64748b', font: { size: 10 } }
          },
          y: {
            grid: { color: 'rgba(239, 68, 68, 0.08)' },
            ticks: { color: '#f87171', font: { size: 10 } }
          }
        }
      }
    });
  }
};

window.ChartManager = ChartManager;
