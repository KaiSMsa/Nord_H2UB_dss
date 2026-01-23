<template>
    <div class="cost-chart-container">
      <canvas ref="costCanvas"></canvas>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, onMounted, watch } from 'vue';
  import {
    Chart,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
    Legend,
  } from 'chart.js';
  
  Chart.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend);
  
  export default defineComponent({
    name: 'CostChart',
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
      const costCanvas = ref(null);
      const costChart = ref(null);
  
      const initChart = () => {
        if (costCanvas.value) {
          costChart.value = new Chart(costCanvas.value, {
            type: 'bar',
            data: props.chartData,
            options: props.chartOptions,
          });
        }
      };
  
      onMounted(() => {
        initChart();
      });
  
      // Watch for changes in chartData
      watch(
        () => props.chartData,
        (newData) => {
          if (costChart.value) {
            costChart.value.data = newData;
            costChart.value.update();
          }
        },
        { deep: true }
      );
  
      // Watch for changes in chartOptions
      watch(
        () => props.chartOptions,
        (newOptions) => {
          if (costChart.value) {
            costChart.value.options = newOptions;
            costChart.value.update();
          }
        },
        { deep: true }
      );
  
      return {
        costCanvas,
      };
    },
  });
  </script>
  
  <style scoped>
  .cost-chart-container {
    width: 100%;
    height: 100%;
  }
  .cost-chart-container canvas {
    width: 100% !important;
    height: 100% !important;
  }
  </style>
  