<template>
  <div class="main-container">
    <!-- Bar Chart for Capacities -->
    <div class="chart-container">
      <h3>Optimal Fuel Capacities by Year</h3>
      <BarChart :data="chartData" :options="chartOptionsCapacities" />
    </div>

    <!-- Bar Chart for Costs -->
    <div class="chart-container">
      <h3>Fuel Costs by Year</h3>
      <BarChart :data="chartCostData" :options="chartOptionsCosts" />
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { Bar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

export default defineComponent({
  name: 'ResultBarChart',
  components: {
    BarChart: Bar,
  },
  props: {
    chartData: { type: Object, required: true },
    chartCostData: { type: Object, required: true },
  },
  data() {
    return {
      chartOptionsCapacities: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: { display: true, text: 'Year' },
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Fuel Capacity (in tonnes)' },
            ticks: {
              stepSize: this.calculateStepSize(this.chartData),
            },
          },
        },
        plugins: {
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 20, // Size of the colored square
              padding: 10, // Space between items
              usePointStyle: true, // Use round or square boxes
            },
          },
          tooltip: {
            callbacks: {
              label: context => `${context.dataset.label}: ${context.raw} tonnes`,
            },
          },
        },
      },

      chartOptionsCosts: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: { display: true, text: 'Year' },
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Fuel Costs (in $)' },
            ticks: {
              stepSize: this.calculateStepSize(this.chartCostData),
            },
          },
        },
        plugins: {
          legend: {
            display: true,
            position: 'right',
            labels: {
              boxWidth: 20, // Size of the colored square
              padding: 10, // Space between items
              usePointStyle: true, // Use round or square boxes
            },
          },
          tooltip: {
            callbacks: {
              label: context => `${context.dataset.label}: $${context.raw.toLocaleString()}`,
            },
          },
        },
      },
    };
  },
  methods: {
    calculateStepSize(data) {
      if (!data || !data.datasets) return 1000;
      const maxValue = Math.max(...data.datasets.flatMap(dataset => dataset.data));
      return Math.ceil(maxValue / 10);
    },
  },
});
</script>

<style scoped>
.main-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-container {
  position: relative;
  height: 400px;
  width: 70%;
  margin: 20px auto;
}

h3 {
  text-align: center;
}
</style>
