<template>
  <canvas ref="pieCanvas"></canvas>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue';
import { Chart, ArcElement, Tooltip, Legend } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';

Chart.register(ArcElement, Tooltip, Legend, ChartDataLabels);

export default defineComponent({
  name: 'PieChartWrapper',
  props: {
    chartData: {
      type: Object,
      required: true,
    },
    chartOptions: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const pieCanvas = ref(null);
    const pieChart = ref(null);

    const initChart = () => {
      if (pieCanvas.value) {
        pieChart.value = new Chart(pieCanvas.value, {
          type: 'pie',
          data: props.chartData,
          options: props.chartOptions,
        });
      }
    };

    onMounted(() => {
      initChart();
    });

    // Watch for data changes
    watch(
      () => props.chartData,
      newData => {
        if (pieChart.value) {
          pieChart.value.data = newData;
          pieChart.value.update();
        }
      },
      { deep: true }
    );

    // Watch for option changes
    watch(
      () => props.chartOptions,
      newOptions => {
        if (pieChart.value) {
          pieChart.value.options = newOptions;
          pieChart.value.update();
        }
      },
      { deep: true }
    );

    return { pieCanvas };
  },
});
</script>

<style scoped>
canvas {
  display: block;
  /* The parent (.pie-canvas in ResultBarChart.vue) sets width/height. */
  max-width: 100%;
  max-height: 100%;
}
</style>
