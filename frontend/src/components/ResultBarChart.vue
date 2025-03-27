<template>
  <div class="main-container">
    <!-- Capacities Chart using VueApexChart -->
    <div class="chart-container">
      <h3>Optimized Tank Capacities by Fuel and Year</h3>
      <div class="chart-wrapper">
        <apexchart type="bar" height="400" :options="chartOptions" :series="transformedData.series">
        </apexchart>
      </div>
    </div>

    <!-- Costs Chart using the CostChart component -->
    <div class="chart-container">
      <h3>Fuel Costs by Year</h3>
      <div class="chart-wrapper">
        <CostChart :chartData="parsedCostChartData" :chartOptions="chartCostOptions" />
      </div>
    </div>

    <!-- Pie chart for cost distribution -->
    <div class="chart-container pie-chart-container">
      <h3>Cost Distribution</h3>
      <div class="chart-wrapper">
        <PieChart :data="costDistributionData" :options="pieChartOptions" />
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import VueApexChart from 'vue3-apexcharts';
import CostChart from './CostChart.vue';
import { Pie } from 'vue-chartjs';

export default defineComponent({
  name: 'ResultBarChart',
  components: {
    apexchart: VueApexChart,
    CostChart,
    PieChart: Pie,
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
    costDistributionData: {
      type: Object,
      required: true,
    },
  },
  computed: {
    // Capacities chart transformation (unchanged)
    transformedData() {
      const years = this.chartData.labels; // e.g., ['2025','2030','2035','2040','2045']
      const baseColors = {
        MGO: '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        Ammonia: '#ffc107',
        Methanol: '#dc3545',
        LNG: '#6f42c1',
      };

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
        return '#' + ((1 << 24) + (R << 16) + (G << 8) + B)
          .toString(16)
          .slice(1);
      }

      const fuelCounters = {};
      const series = this.chartData.datasets.map(ds => {
        const fuel = ds.stack;
        if (!fuelCounters[fuel]) {
          fuelCounters[fuel] = 1;
        } else {
          fuelCounters[fuel]++;
        }
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
          name: `${fuel} - ${formattedTankId}`,
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
            formatter: val => val + ' tonnes',
          },
        },
      };
    },
    parsedCostChartData() {
      return {
        labels: this.costChartData.labels,
        datasets: this.costChartData.datasets.map(ds => {
          // Map each data object to a total (replacing 0 with 1) and attach the details.
          const totals = ds.data.map(item => {
            const totalValue = item.total === 0 ? 1 : item.total;
            return totalValue;
          });
          return {
            label: ds.label,
            data: totals,
            backgroundColor: ds.backgroundColor,
            stack: ds.stack,
            details: ds.data,
          };
        }),
      };
    },
    // Chart.js options for the cost chart – using a logarithmic y-axis.
    chartCostOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
          },
          y: {
            stacked: true,
            type: 'logarithmic',
            min: 1,
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                const dataset = context.dataset;
                const index = context.dataIndex;
                const detail = dataset.details ? dataset.details[index] : null;
                if (detail) {
                  return [
                    `${dataset.label}: $${detail.total}`,
                    `Opening: $${detail.opening}`,
                    `Maintenance: $${detail.operating}`,
                    `Decommissioning: $${detail.decommissioning}`
                  ];
                }
                return `${dataset.label}: $${context.raw}`;
              },
            },
          },
          legend: {
            position: 'right',
          },
        },
      };
    },
    // Chart.js options for the pie chart
    pieChartOptions: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 0,
          right: 50, // add extra padding on the right so the legend appears there
          bottom: 0,
          left: 0,
        },
      },
      elements: {
        arc: {
          borderWidth: 2,
          // Uncomment the following line if your Chart.js version supports a minimum angle:
          minAngle: 5,
        },
      },
      plugins: {
        legend: {
          position: 'right',
          align: 'center',
          labels: {
            boxWidth: 20,
            padding: 10,
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const label = context.chart.data.labels[context.dataIndex];
              const value = context.parsed;
              return `${label}: $${value.toLocaleString()}`;
            },
          },
        },
      },
    },
  },
});
</script>

<style scoped>
.chart-container {
  width: 70%;
  margin: auto;
  padding: 1rem 0;
  overflow: hidden;
}

.chart-wrapper {
  position: relative;
  height: 400px;
  /* Adjust this value as needed */
  width: 100%;
}

/* Adjust pie chart container height to match the bar charts */
.chart-wrapper canvas {
  display: block;
  max-width: 100%;
  max-height: 100%;
  height: 100%;
}
</style>
