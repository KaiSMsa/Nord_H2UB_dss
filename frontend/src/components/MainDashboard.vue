<template>
  <div class="stepper-container">
    <!-- Stepper Header -->
    <div class="stepper">
      <div v-for="(step, index) in steps" :key="index" class="step-container">
        <!-- Make step circle and label clickable -->
        <div class="step-clickable" @click="goToStep(index)" :class="{ 'disabled-step': index > currentStep }">
          <!-- Step Circle -->
          <div class="step" :class="{ active: currentStep === index, completed: index < currentStep }">
            <span v-if="index >= currentStep">{{ index + 1 }}</span>
            <span v-else-if="currentStep > index" class="completed-tick">✔</span>
          </div>
          <!-- Step Label next to the step number -->
          <div class="step-label">{{ step.label }}</div>
        </div>
        <!-- Line between steps (add line except after the last step) -->
        <div v-if="index < steps.length - 1" class="step-line"></div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="step-content" :class="{ 'results-step': currentStep === steps.length - 1 }">
      <div v-if="currentStep === 0">
        <!-- Step 1: Port Fuel Capacity -->
        <PortFuelInformation v-model:globalData="globalData" />
      </div>
      <div v-else-if="currentStep === 1">
        <!-- Step 2: Fuel Selection -->
        <FuelBarSelection v-model:globalData="globalData" />
      </div>
      <div v-else-if="currentStep === 2">
        <!-- Step 3: Capacity Selection -->
        <FuelCapacitySelection v-model:globalData="globalData" />
      </div>
      <div v-if="currentStep === steps.length - 1">
        <div v-if="resultData">
          <!-- <ResultBarChart
            :chart-data="chartData"
            :cost-chart-data="costChartData"
            :cost-distribution-data="costDistributionData"
            :chart-options="chartOptions" 
          /> -->
          <ResultBarChart
            :chart-data="chartData"
            :cost-chart-data="costChartData"
          />
        </div>
        <div v-else>
          <p>No results available.</p>
        </div>
      </div>
    </div>
    <!-- Display globalData content -->
    <!-- <div class="global-data-display">
      <h3>Global Data</h3>
      <pre>{{ JSON.stringify(globalData, null, 2) }}</pre>
    </div> -->

    <!-- Step Footer -->
    <div class="step-footer" :class="{ 'align-right': currentStep === 0 }">
      <b-button v-if="currentStep > 0" @click="previousStep" variant="secondary">
        Previous
      </b-button>
      <b-button v-if="currentStep < steps.length - 2" @click="nextStep" variant="primary">
        Next
      </b-button>
      <b-button v-if="currentStep === steps.length - 2" @click="submit" variant="success">
        Plan
      </b-button>
    </div>
  </div>
</template>

<script>
import FuelBarSelection from './FuelBarSelection.vue';
import PortFuelInformation from './PortFuelInformation.vue';
import FuelCapacitySelection from './FuelCapacitySelection.vue';
import ResultBarChart from './ResultBarChart.vue';

export default {
  name: 'MainDashboard',
  components: {
    FuelBarSelection,
    PortFuelInformation,
    FuelCapacitySelection,
    ResultBarChart,
  },
  data() {
    return {
      currentStep: 0,
      resultData: [],
      resultCosts: [],
      steps: [
        { label: 'Port Fuel Capacity' },
        { label: 'Fuel Selection' },
        { label: 'Capacity Selection' },
        { label: 'Results' },
      ],
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
          },
          title: {
            display: true,
            text: 'Total Capacity and Fuel Capacities per Year',
          },
        },
        scales: {
          x: {
            stacked: true,
            title: {
              display: true,
              text: 'Year',
            },
          },
          y: {
            stacked: true,
            beginAtZero: true,
            title: {
              display: true,
              text: 'Capacity (Units)',
            },
          },
        },
      },
      globalData: {
        isStep1Initial: true,
        portFuelInformation: {
          totalMGOEquivalent: 10000,
          fuelAmounts: {
            MGO: 10000,
            MDO: 0,
            IFO: 0,
            VLSFO: 0,
            HFO: 0,
          },
        },
        fuelBarSelection: {
          intervals: [
            {
              name: '2025',
              totalAmount: 10000,
              fuelValues: {
                MGO: 10000,
                'Liquid Hydrogen': 0,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 0,
              }
            },
            {
              name: '2030-2035',
              totalAmount: 10000,
              fuelValues: {
                MGO: 10000,
                'Liquid Hydrogen': 0,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 0,
              }
            },
            {
              name: '2035-2040',
              totalAmount: 10000,
              fuelValues: {
                MGO: 10000,
                'Liquid Hydrogen': 0,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 0,
              }
            },
            {
              name: '2040-2045',
              totalAmount: 10000,
              fuelValues: {
                MGO: 10000,
                'Liquid Hydrogen': 0,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 0,
              }
            },
            {
              name: '2045-2050',
              totalAmount: 10000,
              fuelValues: {
                MGO: 10000,
                'Liquid Hydrogen': 0,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 0,
              }
            },
          ]
        },
        fuelCapacitySelection: {
          fuels: [
            {
              name: 'MGO',
              class: 'mgo-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 10000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
            {
              name: 'Liquid Hydrogen',
              class: 'lh2-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 7000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
            {
              name: 'Compressed Hydrogen',
              class: 'ch2-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 7000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
            {
              name: 'Ammonia',
              class: 'ammonia-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 7000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
            {
              name: 'Methanol',
              class: 'methanol-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 7000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
            {
              name: 'LNG',
              class: 'lng-bar',
              rows: [
                { capacity: 3000, storageVolume: 0, cost: 0 },
                { capacity: 5000, storageVolume: 0, cost: 0 },
                { capacity: 7000, storageVolume: 0, cost: 0 },
              ],
              changeRate: -2,
              maintenanceCost: 4,
              decommissioningCost: 10
            },
          ]
        }
      },
    };
  },
  computed: {
    /* chartData() {
      //if (!this.resultData || !this.resultData.solution) return null;

      // Define the years (x-axis) and fuels (categories)
      const years = ['2025', '2030', '2035', '2040', '2045'];
      const fuels = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];

      // Define colors for each fuel
      const fuelColors = {
        'MGO': '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        'Ammonia': '#ffc107',
        'Methanol': '#dc3545',
        'LNG': '#6f42c1',
      };

      // Initialize datasets for each fuel
      const datasets = fuels.map((fuel) => {
        return {
          label: fuel,
          data: years.map((year) => {
            // Check if the fuel has data for the year
            if (this.resultData[fuel] && this.resultData[fuel][year]) {
              // Extract the capacities for the current fuel and year
              const capacitiesForYear = this.resultData[fuel][year];

              // Calculate the total capacity for 'opened' or 'operating'
              return Object.keys(capacitiesForYear)
                .filter((capacity) => {
                  const status = capacitiesForYear[capacity];
                  return status.opened || status.operating;
                })
                .reduce((sum, capacity) => sum + parseInt(capacity, 10), 0);
            }
            return 0; // Default to 0 if no data for the year
          }),
          backgroundColor: fuelColors[fuel],
        };
      });

      // Return the Chart.js data format
      return {
        labels: years, // X-axis labels
        datasets, // Y-axis datasets
      };
    },*/
    chartData() {
      // Define the x-axis labels and fuels in a specific order.
      const years = ['2025', '2030', '2035', '2040', '2045'];
      const fuelList = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];
      const fuelColors = {
        'MGO': '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        'Ammonia': '#ffc107',
        'Methanol': '#dc3545',
        'LNG': '#6f42c1',
      };

      const datasets = [];

      // For each fuel, process its tank data across the years.
      fuelList.forEach(fuel => {
        if (!this.resultData[fuel]) return; // skip if no data for the fuel

        // Collect unique tank identifiers for this fuel across all years.
        const tanks = new Set();
        years.forEach(year => {
          if (this.resultData[fuel][year]) {
            Object.keys(this.resultData[fuel][year]).forEach(tankId => tanks.add(tankId));
          }
        });

        // For each tank, build a dataset.
        tanks.forEach(tankId => {
          const data = years.map(year => {
            let value = 0;
            if (this.resultData[fuel][year] && this.resultData[fuel][year][tankId]) {
              // The tank object has a single key representing capacity (e.g., "3000" or "5000")
              const tankData = this.resultData[fuel][year][tankId];
              Object.keys(tankData).forEach(capacityStr => {
                const status = tankData[capacityStr];
                // Only count capacity if "opened" or "operating" is truthy.
                if (status.opened || status.operating) {
                  value += parseInt(capacityStr, 10);
                }
              });
            }
            return value;
          });

          datasets.push({
            label: `${fuel} - ${tankId}`,
            data,
            backgroundColor: fuelColors[fuel],
            stack: fuel, // ensures that all tanks for the same fuel are stacked together
          });
        });
      });

      return {
        labels: years,
        datasets,
      };
    },
    /* costChartData() {
      const years = ["2025", "2030", "2035", "2040", "2045"];
      const fuels = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];

      const fuelColors = {
        MGO: "#007bff",
        "Liquid Hydrogen": "#28a745",
        "Compressed Hydrogen": "#17a2b8",
        Ammonia: "#ffc107",
        Methanol: "#dc3545",
        LNG: "#6f42c1",
      };

      const datasets = fuels.map((fuel) => {
        return {
          label: fuel,
          backgroundColor: fuelColors[fuel],
          data: years.map((year) => {
            // Check if the fuel has data for the year
            if (this.resultCosts[fuel] && this.resultCosts[fuel][year]) {
              // Extract the costs for the current fuel and year
              const costForYear = this.resultCosts[fuel][year];

              // Calculate the total capacity for 'opened' or 'operating'
              return Object.keys(costForYear).reduce((totalCost, capacity) => {
                const costData = costForYear[capacity];
                const openedCost = costData.opened || 0;
                const operatingCost = costData.operating || 0;
                const closedCost = costData.closed || 0;
                return totalCost + openedCost + operatingCost + closedCost;
              }, 0);
            }
            // If no data for this fuel/year, return 0
            return 0;
          }),
        };
      });

      return {
        labels: years,
        datasets: datasets,
      };
    }, */
    costChartData() {
      const years = ['2025', '2030', '2035', '2040', '2045'];
      const fuelList = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];
      const fuelColors = {
        'MGO': '#007bff',
        'Liquid Hydrogen': '#28a745',
        'Compressed Hydrogen': '#17a2b8',
        'Ammonia': '#ffc107',
        'Methanol': '#dc3545',
        'LNG': '#6f42c1',
      };

      const datasets = [];

      fuelList.forEach(fuel => {
        if (!this.resultCosts[fuel]) return;

        // For each year, sum costs from all tanks for the current fuel.
        const data = years.map(year => {
          let totalCostForYear = 0;
          if (this.resultCosts[fuel][year]) {
            // Iterate over all tanks for that fuel in this year.
            Object.values(this.resultCosts[fuel][year]).forEach(tankCostData => {
              // Each tankCostData is an object where each key represents a capacity,
              // and its value contains the cost breakdown.
              Object.values(tankCostData).forEach(costValues => {
                totalCostForYear += (costValues.opened || 0) +
                  (costValues.operating || 0) +
                  (costValues.closed || 0);
              });
            });
          }
          return totalCostForYear;
        });

        datasets.push({
          label: fuel,
          data,
          backgroundColor: fuelColors[fuel],
          stack: fuel, // all series with the same fuel will stack together
        });
      });

      return {
        labels: years,
        datasets,
      };
    },

    /*  costDistributionData() {
        const fuels = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];
        const years = ['2025', '2030', '2035', '2040', '2045'];
  
        // Initialize totals
        const totalCosts = {
          opened: 0,
          operating: 0,
          closed: 0,
        };
  
        // Sum up costs across all fuels and years
        fuels.forEach((fuel) => {
          if (this.resultCosts[fuel]) {
            years.forEach((year) => {
              if (this.resultCosts[fuel][year]) {
                Object.values(this.resultCosts[fuel][year]).forEach((costData) => {
                  totalCosts.opened += costData.opened || 0;
                  totalCosts.operating += costData.operating || 0;
                  totalCosts.closed += costData.closed || 0;
                });
              }
            });
          }
        });
  
        // Format for Chart.js bar or pie chart
        return {
          labels: ['Opening Costs', 'Maintenance Costs', 'Closing Costs'],
          datasets: [
            {
              data: [
                totalCosts.opened,
                totalCosts.operating,
                totalCosts.closed,
              ],
              backgroundColor: ['#007bff', '#28a745', '#dc3545'], // Colors for bars/slices
            },
          ],
        };
      },
    }, */
    costDistributionData() {
      // This computed property sums all costs over fuels, years, and tanks.
      const fuelList = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];
      const years = ['2025', '2030', '2035', '2040', '2045'];

      const totalCosts = { opened: 0, operating: 0, closed: 0 };

      fuelList.forEach(fuel => {
        if (!this.resultCosts[fuel]) return;
        years.forEach(year => {
          if (this.resultCosts[fuel][year]) {
            Object.keys(this.resultCosts[fuel][year]).forEach(tankId => {
              const tankCostData = this.resultCosts[fuel][year][tankId];
              Object.keys(tankCostData).forEach(capacityStr => {
                const costValues = tankCostData[capacityStr];
                totalCosts.opened += costValues.opened || 0;
                totalCosts.operating += costValues.operating || 0;
                totalCosts.closed += costValues.closed || 0;
              });
            });
          }
        });
      });

      return {
        labels: ['Opening Costs', 'Maintenance Costs', 'Closing Costs'],
        datasets: [
          {
            data: [totalCosts.opened, totalCosts.operating, totalCosts.closed],
            backgroundColor: ['#007bff', '#28a745', '#dc3545'],
          },
        ],
      };
    },
  },
  methods: {
    nextStep() {
      if (this.currentStep < this.steps.length - 1) {
        if (this.currentStep === 1) // fuel selection
          this.adjustCapacities();
        this.currentStep++;
      }
      else
        console.log(this.costDistributionData);
    },
    previousStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },
    goToStep(index) {
      // Allow navigation to previous steps or the current step
      if (index <= this.currentStep) {
        this.currentStep = index;
      }
    },
    // Implement the processGlobalData function
    processGlobalData(globalData) {
      // Initialize the dataSubmit object
      const dataSubmit = {};

      // 1. Extract Time Intervals (T)
      const T = globalData.fuelBarSelection.intervals.map((interval) => {
        // Extract the starting year from interval names (e.g., "2025", "2030-2035")
        const match = interval.name.match(/^\d{4}/);
        return match ? match[0] : interval.name;
      });
      dataSubmit.T = T;

      // 2. Extract List of Fuels
      const fuels = globalData.fuelCapacitySelection.fuels.map((fuel) => fuel.name);
      dataSubmit.Fuels = fuels;

      // 3. Extract Capacities and Costs
      dataSubmit.Capacities = {};
      dataSubmit.Costs = {};

      globalData.fuelCapacitySelection.fuels.forEach((fuel) => {
        const fuelName = fuel.name;

        // Capacities
        const capacities = fuel.rows.map((row) => row.capacity);

        // Costs
        const costs = fuel.rows.map((row) => row.cost);

        // Other cost parameters
        const changeRate = fuel.changeRate;
        const maintenanceCost = fuel.maintenanceCost;
        const decommissioningCost = fuel.decommissioningCost;

        dataSubmit.Capacities[fuelName] = capacities;
        dataSubmit.Costs[fuelName] = {
          costs: costs,
          changeRate: changeRate,
          maintenanceCost: maintenanceCost,
          decommissioningCost: decommissioningCost,
        };
      });

      // 4. Extract Demand Data
      dataSubmit.Demand = {};

      // Initialize demand object for each fuel
      fuels.forEach((fuelName) => {
        dataSubmit.Demand[fuelName] = {};
      });

      globalData.fuelBarSelection.intervals.forEach((interval) => {
        const intervalName = interval.name;
        // Extract the starting year for consistent keys
        const match = intervalName.match(/^\d{4}/);
        const intervalYear = match ? match[0] : intervalName;

        const fuelValues = interval.fuelValues;

        Object.keys(fuelValues).forEach((fuelName) => {
          if (fuels.includes(fuelName)) {
            dataSubmit.Demand[fuelName][intervalYear] = fuelValues[fuelName];
          }
        });
      });

      return dataSubmit;
    },
    adjustCapacities() {
      const fuelTypes = Object.keys(this.globalData.fuelBarSelection.intervals[0].fuelValues);

      fuelTypes.forEach((fuelType) => {
        // Calculate the max fuel value across all intervals
        const maxFuelValue = Math.max(
          ...this.globalData.fuelBarSelection.intervals.map(
            (interval) => interval.fuelValues[fuelType] || 0
          )
        );
        const fuelEntry = this.globalData.fuelCapacitySelection.fuels.find((fuel) => fuel.name === fuelType);
        if (!fuelEntry) return;

        // Find the current max capacity in fuelCapacitySelection
        const currentCapacities = fuelEntry.rows.map((row) => row.capacity);
        const maxCapacity = Math.max(...currentCapacities);

        // If maxFuelValue exceeds maxCapacity, add a new rounded capacity
        if (maxFuelValue > maxCapacity) {
          const newCapacity = Math.ceil(maxFuelValue / 1000) * 1000; // Round to upper thousand
          fuelEntry.rows.push({
            capacity: newCapacity,
            storageVolume: 0,
            cost: 0,
          });
        }
      });
    },
    submit() {
      const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:3000';
      const dataSubmit = this.processGlobalData(this.globalData);

      fetch(`${API_BASE}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataSubmit),
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          // Log the returned JSON response in the console.
          // console.log('Server Response:', data);
          // Optionally, show the response in an alert.
          // alert(JSON.stringify(data, null, 2));

          if (data.status === 0) {
            // Display the optimal solution
            this.resultData = data.solution;
            this.resultCosts = data.costs;
            console.log(JSON.stringify(this.resultData, null, 2));
            console.log(JSON.stringify(this.resultCosts, null, 2));
            console.log(JSON.stringify(this.costChartData, null, 2));

            // Navigate to the "Results" step
            this.currentStep = this.steps.length - 1;
          } else {
            // Display non-optimal solution
            alert(`Non-optimal solution:\nStatus: ${data.status}`);
          }
        })
        .catch(error => {
          console.error('Submission Error:', error);
          alert(`An error occurred while submitting data.\n${error}`);
        });
    },
  },
};
</script>

<style scoped>
.stepper-container {
  margin: 2rem 0;
}

.stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding: 0 20px;
}

.step-container {
  display: flex;
  align-items: center;
  position: relative;
  flex-grow: 1;
  text-align: center;
}

/* New class for clickable steps */
.step-clickable {
  display: flex;
  align-items: center;
  cursor: pointer;
  /* Indicates the element is clickable */
}

.disabled-step {
  cursor: not-allowed;
  /* Change cursor for disabled steps */
  opacity: 0.6;
  /* Visually indicate the step is disabled */
  pointer-events: none;
  /* Prevent click events on disabled steps */
}

.step {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 2px solid #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, border-color 0.3s;
  flex-shrink: 0;
  background-color: #fff;
  z-index: 2;
  margin: 0 auto;
}

.step.active {
  border-color: #007bff;
  background-color: #007bff;
  color: white;
}

.step.completed {
  border-color: #28a745;
}

.completed-tick {
  color: #28a745;
  font-size: 1.5rem;
  font-weight: bold;
}

.step-label {
  margin-left: 10px;
  font-size: 1rem;
  color: #555;
  max-width: 100px;
  text-align: center;
}

.step-line {
  flex-grow: 1;
  height: 4px;
  background-color: #ccc;
  z-index: 1;
}

.step-content {
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  background-color: #f9f9f9;
  margin-top: 2rem;
  min-height: 300px;
  height: auto;
  display: flex;
  justify-content: center;
  align-items: center;
}

.results-step {
  display: block;
  /* Reset flex layout for ResultBarChart */
  padding: 0;
  /* Optional: Adjust padding for consistent appearance */
  justify-content: center;
  align-items: center;
}

/* Step footer styles */
.step-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding: 1rem 0;
}

/* Align right only for the first step */
.step-footer.align-right {
  justify-content: flex-end;
}
</style>