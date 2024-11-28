<template>
  <div style="height: 400px; width: 600px;">
    <Bar :chart-data="chartData" :options="chartOptions" />
  </div>
</template>

<script>
import { defineComponent, ref } from 'vue';
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

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

export default defineComponent({
  name: 'BarChartExample',
  components: {
    Bar,
  },
  setup() {
    const chartData = ref({
      labels: ['January', 'February', 'March', 'April', 'May'],
      datasets: [
        {
          label: 'Sales',
          backgroundColor: '#42A5F5',
          data: [150, 200, 180, 220, 170],
        },
      ],
    });

    const chartOptions = ref({
      responsive: true,
      maintainAspectRatio: false,
    });

    return {
      chartData,
      chartOptions,
    };
  },
});
</script>
