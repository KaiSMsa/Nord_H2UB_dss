<!-- <template>
  <div class="main-container">
    Bar Chart for Capacities
    <div class="chart-container">
      <h3>Optimal Fuel Capacities by Year</h3>
      <BarChart :data="chartData" :options="chartOptionsCapacities" />
    </div>
  </div>
</template> -->

<!-- <script>
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

function shadeColor(color, percent) {
  // Ensure the color is in the format "#rrggbb"
  let R = parseInt(color.substring(1, 3), 16);
  let G = parseInt(color.substring(3, 5), 16);
  let B = parseInt(color.substring(5, 7), 16);
  // Increase each channel by the percentage of 255.
  R = Math.min(255, Math.max(0, R + Math.round((255 * percent) / 100)));
  G = Math.min(255, Math.max(0, G + Math.round((255 * percent) / 100)));
  B = Math.min(255, Math.max(0, B + Math.round((255 * percent) / 100)));
  // Convert back to hex with leading zeros if necessary.
  const RR = R.toString(16).padStart(2, '0');
  const GG = G.toString(16).padStart(2, '0');
  const BB = B.toString(16).padStart(2, '0');
  return `#${RR}${GG}${BB}`;
} -->

<!-- export default defineComponent({
  name: 'ResultBarChart',
  components: {
    BarChart: Bar,
  },
  props: {
    chartData: { type: Object, required: true },
  },
  computed: {
    localChartData() {
      // Clone the incoming chartData so we don't modify the prop.
      const newData = JSON.parse(JSON.stringify(this.chartData));
      // Define a base color for each fuel type.
      const baseColors = {
        'MGO': '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        'Ammonia': '#ffc107',
        'Methanol': '#dc3545',
        'LNG': '#6f42c1',
      };

      // To assign tank indexes if missing, we keep track per fuel.
      const fuelCounts = {};

      newData.datasets.forEach(ds => {
        // Ensure ds.stack (fuel name) exists.
        const fuel = ds.stack;
        const baseColor = baseColors[fuel] || '#000000';
        // If tankId is not provided, assign one incrementally.
        if (!ds.tankId) {
          fuelCounts[fuel] = (fuelCounts[fuel] || 0) + 1;
          ds.tankId = `Tank_${fuelCounts[fuel]}`;
        }
        // Parse the tank index from ds.tankId assuming format "Tank_X"
        let tankIndex = 0;
        const match = ds.tankId.match(/Tank_(\d+)/);
        if (match) {
          // Subtract 1 so that Tank_1 is index 0.
          tankIndex = parseInt(match[1], 10) - 1;
        }
        // Lighten the base color by 10% per tank index.
        ds.backgroundColor = shadeColor(baseColor, tankIndex * 10);
        // Also save the base color for legend generation.
        ds.baseColor = baseColor;
      });
      return newData;
    },
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
              // Group datasets by fuel (stack) so only one legend item per fuel is shown.
              generateLabels: (chart) => {
                const datasets = chart.data.datasets;
                const fuelGroups = {};
                datasets.forEach(ds => {
                  if (!fuelGroups[ds.stack]) {
                    fuelGroups[ds.stack] = ds.baseColor;
                  }
                });
                return Object.keys(fuelGroups).map(fuel => ({
                  text: fuel,
                  fillStyle: fuelGroups[fuel],
                  strokeStyle: fuelGroups[fuel],
                  hidden: false,
                  index: fuel,
                }));
              },
              boxWidth: 20,
              padding: 10,
              usePointStyle: true,
            },
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const ds = context.dataset;
                return `${ds.stack} (Tank: ${ds.tankId}): ${context.raw} tonnes`;
              },
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
</script> -->

<!-- <style scoped>
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
  margin-top: 50px;
  text-align: center;
}
</style> -->
<template>
  <div class="chart-container">
    <h3>Optimized tank capacities by Fuel and Year</h3>
    <apexchart type="bar" height="400" :options="chartOptions" :series="transformedData.series"></apexchart>
    <div class="chart-container">
      <h3>Costs by Fuel and Year</h3>
      <canvas ref="costCanvas"></canvas>
      </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue';
import VueApexChart from 'vue3-apexcharts';
import {
  Chart,
  BarElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

Chart.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend);

export default defineComponent({
  name: 'ResultBarChart',
  components: {
    apexchart: VueApexChart,
  },
  props: {
    chartData: {
      type: Object,
      required: true,
    },
    costChartData: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const costChart = ref(null);
    const costCanvas = ref(null);

    // Prepare the Chart.js data directly from costChartData prop.
    const chartCostData = {
      labels: props.costChartData.labels,
      datasets: props.costChartData.datasets.map(ds => ({
        label: ds.label, // use fuel name directly
        data: ds.data,
        backgroundColor: ds.backgroundColor,
        stack: ds.stack,
      })),
    };

    // Chart.js options with a logarithmic y-axis.
    const chartCostOptions = {
      responsive: true,
      scales: {
        x: {
          stacked: true,
        },
        y: {
          stacked: true,
          type: 'logarithmic',
          beginAtZero: true,
        },
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              return `$${value}`;
            }
          }
        },
        legend: {
          position: 'right',
        }
      }
    };

    onMounted(() => {
      if (costCanvas.value) {
        costChart.value = new Chart(costCanvas.value, {
          type: 'bar',
          data: chartCostData,
          options: chartCostOptions,
        });
      }
    });

    // Update Chart.js when costChartData prop changes.
    watch(
      () => props.costChartData,
      (newVal) => {
        if (costChart.value) {
          costChart.value.data.labels = newVal.labels;
          costChart.value.data.datasets = newVal.datasets.map(ds => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: ds.backgroundColor,
            stack: ds.stack,
          }));
          costChart.value.update();
        }
      },
      { deep: true }
    );

    return {
      costCanvas,
      chartCostData,
      chartCostOptions,
    };
  },
  computed: {
    // For the capacities chart (using ApexChart)
    transformedData() {
      const years = this.chartData.labels; // e.g., ['2025','2030','2035','2040','2045']
      const baseColors = {
        'MGO': '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        'Ammonia': '#ffc107',
        'Methanol': '#dc3545',
        'LNG': '#6f42c1',
      };

      // Helper: Compute a slightly adjusted shade for each tank.
      function shadeColor(color, percent) {
        color = color.replace(/^#/, '');
        const num = parseInt(color, 16);
        const amt = Math.round(2.55 * percent);
        let R = (num >> 16) + amt;
        let G = ((num >> 8) & 0x00ff) + amt;
        let B = (num & 0x0000ff) + amt;
        R = Math.min(255, Math.max(0, R));
        G = Math.min(255, Math.max(0, G));
        B = Math.min(255, Math.max(0, B));
        return '#' + ((1 << 24) + (R << 16) + (G << 8) + B).toString(16).slice(1);
      }

      const fuelCounters = {};
      const series = this.chartData.datasets.map(ds => {
        const fuel = ds.stack;
        if (!fuelCounters[fuel]) {
          fuelCounters[fuel] = 1;
        } else {
          fuelCounters[fuel]++;
        }
        // Use the provided tankId or generate one.
        const tankId = ds.tankId ? ds.tankId : `Tank ${fuelCounters[fuel]}`;
        let tankIndex = 0;
        const match = tankId.match(/Tank[\s_-]?(\d+)/);
        const formattedTankId = tankId.replace(/_/g, ' ');
        if (match) {
          tankIndex = parseInt(match[1], 10) - 1;
        }
        const baseColor = baseColors[fuel] || '#000000';
        const backgroundColor = shadeColor(baseColor, tankIndex * 20);
        return {
          name: ds.label || `${fuel} - ${formattedTankId}`,
          group: fuel,
          fuel: fuel,
          data: ds.data,
          color: backgroundColor,
        };
      });

      let maxY = 0;
      years.forEach((_, index) => {
        const fuelSums = {};
        series.forEach(s => {
          fuelSums[s.group] = (fuelSums[s.group] || 0) + s.data[index];
        });
        Object.values(fuelSums).forEach(sum => {
          if (sum > maxY) maxY = sum;
        });
      });
      maxY = Math.ceil(maxY / 1000) * 1000;
      return { series, years, maxY };
    },
    chartOptions() {
      return {
        chart: {
          type: 'bar',
          stacked: true,
          stackType: 'normal',
          toolbar: { show: true },
        },
        plotOptions: {
          bar: {
            horizontal: false,
            columnWidth: '90%',
          },
        },
        xaxis: {
          categories: this.transformedData.years,
        },
        yaxis: {
          max: this.transformedData.maxY,
        },
        dataLabels: {
          textOrientation: 'vertical',
        },
        legend: {
          position: 'right',
          horizontalAlign: 'left',
        },
        tooltip: {
          y: {
            formatter: val => val + " tonnes",
          },
        },
      };
    },
  },
});
</script>

<style scoped>
.chart-container {
  width: 70%;
  margin: auto;
  padding: 1rem 0;
}
</style>