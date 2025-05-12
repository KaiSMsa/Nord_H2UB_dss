<template>
  <!-- Show HowItWorks first -->
  <HowItWorks v-if="showHowItWorks" @started="onStarted" />

  <!-- Main Dashboard -->
  <div v-else class="stepper-container">
    <!-- Stepper Header -->
    <div class="stepper">
      <div v-for="(step, index) in steps" :key="index" class="step-container">
        <!-- Make step circle and label clickable -->
        <div class="step-clickable" @click="goToStep(index)"
          :class="{ 'disabled-step': index > currentStep }">
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
      <!-- Step 1 -->
      <PortFuelInformation
        v-if="currentStep === 0"
        v-model:scenarioData="activeData"
        :locked="scenarios.length > 1"
        
      />
      <!-- Step 2 -->
      <FuelBarSelection
        v-else-if="currentStep === 1"
        :scenarios="scenarios"
        @update-scenario="updateFuelSelection"
      />
      <!-- Step 3 -->
      <FuelCapacitySelection
        v-else-if="currentStep === 2"
        v-model:scenarios="scenarios"
        @update-scenario="updateCapacitySelection"
      />
      <!-- Step 4 (results) -->
      <div v-else>
        <!-- Each scenario’s charts will live in its own tab (child comp to be added) -->
        <!-- <ResultBarChart v-if="activeScenario.resultData" :chart-data="chartData" :cost-chart-data="chartCostData"
          :cost-distribution-data="costDistributionData" />
        <p v-else>No results available.</p> -->
        <ResultBarChart v-if="currentStep === steps.length - 1" :scenarios="scenarios" />
        <p v-else>No results available.</p>
      </div>
    </div>
    <!-- Display globalData content -->
    <!-- <div class="global-data-display">
      <h3>Global Data</h3>
      <pre>{{ JSON.stringify(scenarios, null, 2) }}</pre>
    </div> -->

    <!-- Step Footer -->
    <div class="step-footer" :class="{ 'align-right': currentStep === 0}">
      <b-button v-if="currentStep > 0" @click="previousStep" variant="secondary">
        Previous
      </b-button>
      <b-button v-if="currentStep < steps.length - 2" @click="nextStep" variant="primary">
        Next
      </b-button>
      <b-button v-if="currentStep === steps.length - 2" @click="submit" variant="success">
        Plan
      </b-button>
      <div v-if="currentStep === steps.length - 1" class="step-footer results-footer">
        <b-button v-if="currentStep === steps.length - 1" :disabled="scenarios.length >= MAX_SCENARIOS"
          @click="createNewScenario" variant="primary"
          class="mr-2"
          >
          New scenario
        </b-button>
        <span style="width: 10px; display: inline-block;"></span>
        <b-button v-if="currentStep === steps.length - 1" @click="startOver" variant="primary">
          Start over
        </b-button>
      </div>
    </div>
  </div>
</template>

<script>
import cloneDeep from 'lodash.clonedeep';
import HowItWorks from './HowItWorks.vue';
import PortFuelInformation from './PortFuelInformation.vue';
import FuelCapacitySelection from './FuelCapacitySelection.vue';
import FuelBarSelection from './FuelBarSelection.vue';
import ResultBarChart from './ResultBarChart.vue';
import {
  buildChartData,
  buildCostChartData,
  buildCostDistData
} from '@/utils/chartUtils.js';

function initialGlobalData() {
  return {
    isStep1Initial: true,
    portFuelInformation: {
      totalMGOEquivalent: 10000,
      fuelAmounts: { MGO: 10000, MDO: 0, IFO: 0, VLSFO: 0, HFO: 0 }
    },
    fuelBarSelection: {
      intervals: [
        { name: '2025', totalAmount: 10000, fuelValues: { MGO: 10000, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 0, LNG: 0 } },
        { name: '2030-2035', totalAmount: 10000, fuelValues: { MGO: 10000, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 0, LNG: 0 } },
        { name: '2035-2040', totalAmount: 10000, fuelValues: { MGO: 10000, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 0, LNG: 0 } },
        { name: '2040-2045', totalAmount: 10000, fuelValues: { MGO: 10000, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 0, LNG: 0 } },
        { name: '2045-2050', totalAmount: 10000, fuelValues: { MGO: 10000, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 0, LNG: 0 } }
      ]
    },
    fuelCapacitySelection: {
      fuels: [
        { name: 'MGO', class: 'mgo-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 10000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 },
        { name: 'Liquid Hydrogen', class: 'lh2-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 7000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 },
        { name: 'Compressed Hydrogen', class: 'ch2-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 7000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 },
        { name: 'Ammonia', class: 'ammonia-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 7000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 },
        { name: 'Methanol', class: 'methanol-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 7000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 },
        { name: 'LNG', class: 'lng-bar', rows: [{ capacity: 3000, storageVolume: 0, cost: 0 }, { capacity: 5000, storageVolume: 0, cost: 0 }, { capacity: 7000, storageVolume: 0, cost: 0 }], changeRate: -2, maintenanceCost: 4, decommissioningCost: 10 }
      ]
    }
  };
}

export default {
  name: 'MainDashboard',
  components: {
    HowItWorks,
    FuelBarSelection,
    PortFuelInformation,
    FuelCapacitySelection,
    ResultBarChart,
  },
  data() {
    return {
      MAX_SCENARIOS: 3,         // upper limit
      showHowItWorks: true,     // whether intro page is shown
      currentScenarioIndex: 0,  // which scenario is active
      currentStep: 0,           // 0..3 in the stepper

      /* stepper labels */
      steps: [
        { label: 'Port Fuel Capacity' },
        { label: 'Fuel Selection' },
        { label: 'Tank Capacities' },
        { label: 'Operational Schedule' }
      ],

      /* array of scenario objects */
      scenarios: [
        {
          id: 1,
          name: 'Scenario 1',
          editable: true,
          data: initialGlobalData(),
          resultData: null,
          resultCosts: null,
          /* chart cache */
          cachedChartData: null,
          cachedCostChart: null,
          cachedCostDist: null,
          viewerReady: false
        }
      ]
    };
  },
  computed: {
    activeScenario() { return this.scenarios[this.currentScenarioIndex]; },
    activeData() { return this.activeScenario.data; },
    chartData() {
      //display a messagbox for activeScenario index
      alert(`Active Scenario Index: ${this.currentScenarioIndex}`);
      const res = this.activeScenario.resultData;
      if (!res) return { labels: [], datasets: [] };
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
        if (!res[fuel]) return; // skip if no data for the fuel

        // Collect unique tank identifiers for this fuel across all years.
        const tanks = new Set();
        years.forEach(year => {
          if (res[fuel][year]) {
            Object.keys(res[fuel][year]).forEach(tankId => tanks.add(tankId));
          }
        });

        // For each tank, build a dataset.
        tanks.forEach(tankId => {
          const data = years.map(year => {
            let value = 0;
            if (res[fuel][year] && res[fuel][year][tankId]) {
              // The tank object has a single key representing capacity (e.g., "3000" or "5000")
              const tankData = res[fuel][year][tankId];
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
    chartCostData() {
      const costs = this.activeScenario.resultCosts;
      if (!costs) return { labels: [], datasets: [] };

      const years = ['2025', '2030', '2035', '2040', '2045'];
      const fuelList = ['MGO', 'Liquid Hydrogen', 'Compressed Hydrogen', 'Ammonia', 'Methanol', 'LNG'];
      const fuelColors = {
        MGO: '#007bff', 'Liquid Hydrogen': '#28a745', 'Compressed Hydrogen': '#17a2b8',
        Ammonia: '#ffc107', Methanol: '#dc3545', LNG: '#6f42c1'
      };
      const datasets = [];

      fuelList.forEach(fuel => {
        if (!costs[fuel]) return;
        const data = years.map(y => {
          let open = 0, op = 0, dec = 0;
          if (costs[fuel][y]) {
            Object.values(costs[fuel][y]).forEach(tank =>
              Object.values(tank).forEach(c => {
                open += c.opened || 0; op += c.operating || 0; dec += c.closed || 0;
              })
            );
          }
          return { total: open + op + dec, opening: open, operating: op, decommissioning: dec };
        });
        datasets.push({ label: fuel, data, backgroundColor: fuelColors[fuel], stack: fuel });
      });

      return { labels: years, datasets };
    },
    costDistributionData() {
      const costs = this.activeScenario.resultCosts;
      if (!costs) return { labels: [], datasets: [] };

      const fuels = Object.keys(costs);
      const years = ['2025', '2030', '2035', '2040', '2045'];
      const total = { opened: 0, operating: 0, closed: 0 };

      fuels.forEach(f => {
        years.forEach(y => {
          if (costs[f][y]) {
            Object.values(costs[f][y]).forEach(tank =>
              Object.values(tank).forEach(c => {
                total.opened += c.opened || 0;
                total.operating += c.operating || 0;
                total.closed += c.closed || 0;
              })
            );
          }
        });
      });

      return {
        labels: ['Opening Costs', 'Maintenance Costs', 'Decommissioning Costs'],
        datasets: [
          {
            data: [total.opened, total.operating, total.closed],
            backgroundColor: ['#007bff', '#28a745', '#dc3545']
          }
        ]
      };
    }
  },
  methods: {
    onStarted() {
      // Hide the HowItWorks component and show the main dashboard.
      this.showHowItWorks = false;
    },
    startOver() {
      // keep only Scenario 1 and reset to intro
      this.scenarios = [this.scenarios[0]];
      this.currentScenarioIndex = 0;
      this.currentStep = 0;
      this.showHowItWorks = true;
    },

    // Navigation methods
    nextStep() {
      if (this.currentStep < this.steps.length - 1) {
        if (this.currentStep === 1) // fuel selection
          this.adjustCapacities();
        this.currentStep++;
      }
    },
    previousStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },
    goToStep(idx) {
      // prevent jumping into locked Step 1 when on Scenario 2/3
      if (idx <= this.currentStep) this.currentStep = idx;
    },
    createNewScenario() {
      if (this.scenarios.length >= this.MAX_SCENARIOS) return;

      const base = this.scenarios[0];
      this.scenarios.push({
        id: this.scenarios.length,
        name: `Scenario ${this.scenarios.length + 1}`,
        editable: true,
        data: cloneDeep(base.data),   // start from the initial scenario
        resultData: null,
        resultCosts: null,

        cachedChartData: null,
        cachedCostChart: null,
        cachedCostDist:  null,
        viewerReady: false
      });
      this.currentScenarioIndex = this.scenarios.length - 1;
      this.currentStep = 1;         // jump straight to Step 2
    },
    adjustCapacities() {
      /* ensures tank-size table always includes a row ≥ max demand */
      // const fuelTypes = Object.keys(this.activeData.fuelBarSelection.intervals[0].fuelValues);

      // fuelTypes.forEach(ft => {
      //   const maxDemand = Math.max(
      //     ...this.activeData.fuelBarSelection.intervals.map(i => i.fuelValues[ft] || 0)
      //   );

      //   const fuel = this.activeData.fuelCapacitySelection.fuels.find(f => f.name === ft);
      //   if (!fuel) return;

      //   const currentMax = Math.max(...fuel.rows.map(r => r.capacity));
      //   if (maxDemand > currentMax) {
      //     fuel.rows.push({
      //       capacity: Math.ceil(maxDemand / 1000) * 1000,
      //       storageVolume: 0,
      //       cost: 0
      //     });
      //   }
      // });
    },
    updateFuelSelection({ index, value }) {
      this.scenarios[index].data.fuelBarSelection = value;
    },
    updateCapacitySelection({ index, value }) {
      this.scenarios[index].data.fuelCapacitySelection = value;
    },
    // Implement the processGlobalData function
    processGlobalData(sData) {
      // Initialize the dataSubmit object
      const dataSubmit = {};

      // 1. Extract Time Intervals (T)
      const T = sData.fuelBarSelection.intervals.map((interval) => {
        // Extract the starting year from interval names (e.g., "2025", "2030-2035")
        const match = interval.name.match(/^\d{4}/);
        return match ? match[0] : interval.name;
      });
      dataSubmit.T = T;

      // 2. Extract List of Fuels
      const fuels = sData.fuelCapacitySelection.fuels.map((fuel) => fuel.name);
      dataSubmit.Fuels = fuels;

      // 3. Extract Capacities and Costs
      dataSubmit.Capacities = {};
      dataSubmit.Costs = {};

      sData.fuelCapacitySelection.fuels.forEach((fuel) => {
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

      sData.fuelBarSelection.intervals.forEach((interval) => {
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
    submit() {
      const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:3000';
      const dataSubmit = this.processGlobalData(this.activeData);

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
            // save reults in the active scenario
            this.activeScenario.resultData = data.solution;
            this.activeScenario.resultCosts = data.costs;
            this.activeScenario.cachedChartData = buildChartData(this.activeScenario);
            this.activeScenario.cachedCostChart = buildCostChartData(this.activeScenario);
            this.activeScenario.cachedCostDist = buildCostDistData(this.activeScenario)
            this.activeScenario.editable = false; // lock the scenario
            this.activeScenario.viewerReady = true;
            // Display the optimal solution
            // this.resultData = data.solution;
            // this.resultCosts = data.costs;
            //console.log(JSON.stringify(this.resultData, null, 2));
            //console.log(JSON.stringify(this.chartCostData, null, 2));
            // console.log(JSON.stringify(this.costDistributionData, null, 2));

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

.step-footer.results-footer {
  justify-content: flex-start;   /* could also use flex-end */
}

/* Align right only for the first step */
.step-footer.align-right {
  justify-content: flex-end;
}

.start-over-container {
  text-align: center;
  margin-top: 30px;
}
</style>