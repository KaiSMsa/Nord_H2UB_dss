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
    <div class="step-content">
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
      <div v-else-if="currentStep === 3">
        <!-- Step 4: Review & Submit -->
        <h3>Step 4: Review & Submit</h3>
        <p>Review your information and submit the form.</p>
      </div>
      <div v-if="currentStep === steps.length - 1">
        <!-- <pre>{{ chartData }}</pre> -->
        <div v-if="resultData">
          <!-- Display the bar chart -->
          <ResultBarChart :chart-data="chartData" :options="chartOptions" />
        </div>
        <div v-else>
          <p>No results available.</p>
        </div>
      </div>
    </div>

    <!-- Step Footer -->
    <div class="step-footer" :class="{ 'align-right': currentStep === 0 }">
      <b-button v-if="currentStep > 0" @click="previousStep" variant="secondary">
        Previous
      </b-button>
      <b-button v-if="currentStep < steps.length - 2" @click="nextStep" variant="primary">
        Next
      </b-button>
      <b-button v-if="currentStep === steps.length - 2" @click="submit" variant="success">
        Submit
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
      resultData:
        [
          {
            "fuel": "MGO",
            "schedule": [
              {
                "year": "2025",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2030",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  }
                ]
              },
              {
                "year": "2035",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              }
            ]
          },
          {
            "fuel": "Liquid Hydrogen",
            "schedule": [
              {
                "year": "2025",
                "capacities": []
              },
              {
                "year": "2030",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2035",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              }
            ]
          },
          {
            "fuel": "Compressed Hydrogen",
            "schedule": [
              {
                "year": "2025",
                "capacities": []
              },
              {
                "year": "2030",
                "capacities": []
              },
              {
                "year": "2035",
                "capacities": []
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  },
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              }
            ]
          },
          {
            "fuel": "Ammonia",
            "schedule": [
              {
                "year": "2025",
                "capacities": []
              },
              {
                "year": "2030",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2035",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              }
            ]
          },
          {
            "fuel": "Methanol",
            "schedule": [
              {
                "year": "2025",
                "capacities": []
              },
              {
                "year": "2030",
                "capacities": []
              },
              {
                "year": "2035",
                "capacities": []
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  }
                ]
              }
            ]
          },
          {
            "fuel": "LNG",
            "schedule": [
              {
                "year": "2025",
                "capacities": []
              },
              {
                "year": "2030",
                "capacities": [
                  {
                    "capacity": 5000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2035",
                "capacities": [
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2040",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": false,
                    "closed": true
                  },
                  {
                    "capacity": 7000,
                    "opened": true,
                    "operating": false,
                    "closed": false
                  }
                ]
              },
              {
                "year": "2045",
                "capacities": [
                  {
                    "capacity": 3000,
                    "opened": true,
                    "operating": true,
                    "closed": false
                  }
                ]
              }
            ]
          }
        ],

      steps: [
        { label: 'Port Fuel Capacity' },
        { label: 'Fuel Selection' },
        { label: 'Capacity Selection' },
        { label: 'Review & Submit' },
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
        portFuelInformation: {
          totalMGOEquivalent: 10000,
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
              totalAmount: 12000,
              fuelValues: {
                MGO: 7000,
                'Liquid Hydrogen': 4000,
                'Compressed Hydrogen': 0,
                Ammonia: 0,
                Methanol: 0,
                LNG: 1000,
              }
            },
            {
              name: '2035-2040',
              totalAmount: 12000,
              fuelValues: {
                MGO: 6000,
                'Liquid Hydrogen': 4000,
                'Compressed Hydrogen': 0,
                Ammonia: 1000,
                Methanol: 0,
                LNG: 1000,
              }
            },
            {
              name: '2040-2045',
              totalAmount: 11000,
              fuelValues: {
                MGO: 3000,
                'Liquid Hydrogen': 4000,
                'Compressed Hydrogen': 0,
                Ammonia: 3000,
                Methanol: 0,
                LNG: 1000,
              }
            },
            {
              name: '2045-2050',
              totalAmount: 10000,
              fuelValues: {
                MGO: 0,
                'Liquid Hydrogen': 4000,
                'Compressed Hydrogen': 0,
                Ammonia: 5000,
                Methanol: 0,
                LNG: 1000,
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
    chartData() {
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
    },
  },
  methods: {
    nextStep() {
      if (this.currentStep < this.steps.length - 1) {
        this.currentStep++;
      }
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
    submit() {
      // Process the data before sending it
      const dataSubmit = this.processGlobalData(this.globalData);

      // Send 'dataSubmit' to the server
      fetch('http://localhost:3000/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataSubmit),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Failed to submit data.');
          }
          // Parse the JSON response from the server
          return response.json();
        })
        .then((data) => {
          if (data.status === 0) {
            //display the optimal solution
            alert(`Optimal solution:\n${JSON.stringify(data.solution, null, 2)}`);
            this.resultData = data.solution;
            // Navigate to the "Results" step
            this.currentStep = this.steps.length - 1;
          } else {
            //Display non-optimal solution
            alert(`Non-optimal solution:\nStatus: ${data.status}`)
          }
        })
        .catch((error) => {
          console.error('Error submitting data:', error);
          alert('An error occurred while submitting data.', error.message);
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
}

.step-container {
  display: flex;
  align-items: center;
  position: relative;
  flex-grow: 1;
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