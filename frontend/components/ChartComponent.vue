<template>
  <div class="shaanu-chart-wrapper" v-bind:style="{ height: height }">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
export default {
  name: 'ChartComponent',
  props: {
    // Type can be 'line', 'bar', 'pie', 'doughnut', 'polarArea', etc.
    type: { type: String, default: 'line' },
    data: { type: Object, required: true },
    options: { type: Object, default: () => ({}) },
    height: { type: String, default: '350px' }
  },
  data() {
    return {
      chartInstance: null
    }
  },
  watch: {
    // Requirement: Optimize API response times by updating existing chart data instead of re-rendering
    data: {
      handler(newData) {
        if (this.chartInstance) {
          this.chartInstance.data = newData;
          this.chartInstance.update('none'); // Update without animation for data sync
        }
      },
      deep: true
    },
    // Requirement: Single Responsive UI - handle type switching dynamically
    type(newType) {
      if (this.chartInstance) {
        this.chartInstance.destroy();
        this.renderChart();
      }
    }
  },
  methods: {
    renderChart() {
      const ctx = this.$refs.chartCanvas.getContext('2d');
      
      // Requirement: Styling and Aesthetics - Theme-aware styling
      const isDark = document.body.getAttribute('data-bs-theme') === 'dark';
      const textColor = isDark ? '#cbd5e1' : '#475569';
      const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';

      const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: textColor,
              usePointStyle: true,
              padding: 20,
              font: { family: "'Inter', sans-serif", size: 12, weight: '600' }
            }
          },
          tooltip: {
            backgroundColor: isDark ? '#1e293b' : '#ffffff',
            titleColor: isDark ? '#ffffff' : '#1e293b',
            bodyColor: isDark ? '#94a3b8' : '#64748b',
            borderColor: gridColor,
            borderWidth: 1,
            padding: 12,
            boxPadding: 6,
            usePointStyle: true,
            cornerRadius: 10,
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: gridColor, drawBorder: false },
            ticks: { 
              color: textColor,
              font: { size: 11 },
              padding: 10
            }
          },
          x: {
            grid: { display: false },
            ticks: { 
              color: textColor,
              font: { size: 11 },
              padding: 10
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
        animation: {
          duration: 1000,
          easing: 'easeOutQuart'
        }
      };

      // Merge defaults with custom options provided via props
      const finalOptions = { ...defaultOptions, ...this.options };

      // Initialize the global Chart.js instance (loaded via CDN in index.html)
      this.chartInstance = new Chart(ctx, {
        type: this.type,
        data: this.data,
        options: finalOptions
      });
    }
  },
  mounted() {
    this.renderChart();
    
    // Listen for theme toggle events to update chart aesthetics dynamically
    window.addEventListener('shaanu-theme-changed', () => {
      if (this.chartInstance) {
        this.chartInstance.destroy();
        this.renderChart();
      }
    });
  },
  beforeUnmount() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }
}
</script>

<style scoped>
.shaanu-chart-wrapper {
  width: 100%;
  position: relative;
  /* Requirement: Unified UI - padding for better mobile spacing */
  padding: 10px;
}

canvas {
  /* Fix for Chart.js container sizing issues */
  max-width: 100% !important;
}
</style>