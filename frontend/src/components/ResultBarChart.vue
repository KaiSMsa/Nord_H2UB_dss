<template>
  <div>
    <!-- Bar Chart -->
    <div class="chart-container">
      <h3>Optimal Fuel Capacities by Year</h3>
      <BarChart :data="chartData" :options="chartOptions" />
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

// Register required Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

export default defineComponent({
  name: 'ResultBarChart',
  components: {
    BarChart: Bar,
  },
  props: {
    chartData: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: false, // Bars next to each other
            title: {
              display: true,
              text: 'Year',
            },
          },
          y: {
            stacked: false, // Bars next to each other
            beginAtZero: true,
            title: {
              display: true,
              text: 'Fuel Capacity (in tonnes)',
            },
            ticks: {
              stepSize: this.calculateStepSize(), // Adjust based on data
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
              label: function (context) {
                return `${context.dataset.label}: ${context.raw} tonnes`;
              },
            },
          },
        },
      },
    };
  },
  methods: {
    calculateStepSize() {
      if (!this.chartData || !this.chartData.datasets) {
        return 1000; // Default step size
      }
      // Determine the maximum data value in the datasets
      const maxValue = Math.max(
        ...this.chartData.datasets.flatMap((dataset) => dataset.data)
      );
      return Math.ceil(maxValue / 10); // Step size as 10% of max value
    },
  },
});
</script>

<style scoped>
div {
  position: relative;
  height: 400px; /* Adjust chart height */
  width: 100%; /* Make the chart responsive */
  margin: auto;
}

h3 {
  text-align: center;
  margin-bottom: 20px;
}

.chart-container {
  width: 70%; /* Set width to 70% of the parent container */
  margin: auto; /* Center the chart */
}
</style>
