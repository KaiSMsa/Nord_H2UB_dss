<template>
  <div class="container">
    <h3>Adjust possible fuel tank sizes</h3>

    <b-card no-body>
      <b-tabs card>
        <b-tab v-for="(fuel) in fuels" :key="fuel.name" :title="fuel.name"
          :title-item-class="'d-flex align-items-center'">
          <!-- Tab Title with Fuel Name and Colored Square -->
          <template #title>
            <span class="fuel-square" :class="fuel.class"></span>
            {{ fuel.name }}
          </template>

          <!-- Content within each tab -->
          <div class="content-container">
            <!-- Wrap table in container -->
            <div class="table-container">
              <!-- Capacity and Cost Table -->
              <table class="fuel-table">
                <thead>
                  <tr>
                    <th>Capacity (tonnes)</th>
                    <th>Storage Volume (m³)</th>
                    <th>Estimation Cost ($)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in fuel.rows" :key="rowIndex">
                    <td>
                      <input type="number" v-model.number="row.capacity" placeholder="Tonnes" min="0" step="100"
                        :disabled="disabled || trueCondition" @input="updateCalculations(fuel, row)" />
                    </td>

                    <!-- Display storage volume for Liquid Hydrogen -->
                    <td>{{ row.storageVolume.toFixed(0) }} m³</td>

                    <td>{{ formatCost(row.cost) }} $</td>
                    <td>
                      <b-button size="sm" variant="danger" :disabled="disabled || trueCondition"
                        @click="removeRow(fuel, rowIndex)">
                        Remove
                      </b-button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Add Row Button -->
            <b-button size="sm" variant="success" class="mt-2" :disabled="disabled || trueCondition"
              @click="addRow(fuel)">
              New tanker capacity
            </b-button>

            <!-- Optional Change Rate Input -->
            <div class="cost-inputs">
              <div class="change-rate">
                <label>Change Rate (%):</label>
                <input type="number" v-model.number="fuel.changeRate" placeholder="Percentage" min="-100" max="100"
                  :disabled="disabled || trueCondition" />
              </div>
              <div class="change-rate">
                <label>Maintenance cost (%):</label>
                <input type="number" v-model.number="fuel.maintenanceCost" placeholder="4" min="0" max="10"
                  :disabled="disabled || trueCondition" />
              </div>
              <div class="change-rate">
                <label>Decommissioning cost (%):</label>
                <input type="number" v-model.number="fuel.decommissioningCost" placeholder="10" min="0" max="10"
                  :disabled="disabled || trueCondition" />
              </div>
            </div>
          </div>
        </b-tab>
      </b-tabs>
    </b-card>
  </div>
  <!-- <pre class="mt-4">{{ localData }}</pre> -->
</template>



<script>
export default {
  name: 'FuelCapacityEditor',
  props: {
    capacitySelection: { type: Object, required: true },
    disabled: { type: Boolean, default: false }
  },
  data() {
    return {
      localData: JSON.parse(JSON.stringify(this.capacitySelection)),
      stepSize: 100,
    };
  },
  computed: {
    fuels() {
      return this.localData.fuels;
    },
  },
  watch: {
    // Watch for changes in localPorts and emit updates to the parent
    localData: {
      handler(newVal) {
        this.$emit('update:capacitySelection', newVal);
      },
      deep: true
    },
    'fuels': {
      handler(newFuels) {
        // Recalculate costs whenever capacities change
        newFuels.forEach((fuel) => {
          fuel.rows.forEach((row) => {
            this.updateCalculations(fuel, row);
          });
        });
      },
      deep: true,
    },
  },
  mounted() {
    // Perform initial calculations for Liquid Hydrogen on component load
    this.fuels.forEach((fuel) => {
      fuel.rows.forEach((row) => {
        this.updateCalculations(fuel, row);
      });
    });
  },
  methods: {
    addRow(fuel) {
      fuel.rows.push({ capacity: 0, cost: 0 });
    },
    removeRow(fuel, index) {
      fuel.rows.splice(index, 1);
    },
    // Placeholder for cost calculation
    scaledShellCost(storageVolumeM3, baseUSDperM3, alpha = 0.65) {
      const V_REF = 1000;                                // m³
      const k = baseUSDperM3 * Math.pow(V_REF, 1 - alpha); // keeps cost equal at V_REF
      return k * Math.pow(storageVolumeM3, alpha);
    },

    /* --- main calculation ------------------------------------------------- */
    updateCalculations(fuel, row) {
      const fixedCostPerTank = {
        'MGO': 500000,
        'Liquid Hydrogen': 2000000,
        'Compressed Hydrogen': 20000000,
        'Ammonia': 3000000,
        'Methanol': 2500000,
        'LNG': 500000
      };

      /* per-fuel constants -------------------------------------------------- */
      const FUEL_PROPS = {
        'MGO': { ρ: 850, EC: 42.8, cShell: 1000 },
        'Liquid Hydrogen': { ρ: 70.8, EC: 120, cShell: 50, cLiquef: 1.2 },
        'Compressed Hydrogen': { ρ: 70.8, EC: 120, cShell: 600 },
        'Ammonia': { ρ: 682, EC: 18.6, cShell: 2000 },
        'Methanol': { ρ: 792, EC: 19.9, cShell: 1000 },
        'LNG': { ρ: 450, EC: 50, cShell: 2000 }
      };

      /* shortcut for unspecified fuels ------------------------------------- */
      if (!FUEL_PROPS[fuel.name]) {
        row.cost = Math.round(row.capacity * 100);
        return;
      }

      const { ρ, EC, cShell, cLiquef } = FUEL_PROPS[fuel.name];
      const capacityMJ = row.capacity * 42.8 * 1000;           // diesel-eq energy (MJ)

      /* derive storage volume ---------------------------------------------- */
      if (fuel.name === 'MGO') {
        row.storageVolume = Math.round((row.capacity * 1000) / ρ);
      } else {
        const tonnesAlt = Math.round(capacityMJ / EC / 1000);  // t of alt fuel
        row.storageVolume = Math.round((tonnesAlt * 1000) / ρ);
      }

      /* variable shell cost with economies-of-scale ------------------------ */
      const shellCost = this.scaledShellCost(row.storageVolume, cShell);

      /* extra linear part for Liquid H₂ ------------------------------------ */
      const liquefactionCost =
        fuel.name === 'Liquid Hydrogen'
          ? (capacityMJ / EC) * cLiquef       // kg × USD/kg  (MJ/EC = kg)
          : 0;

      /* total -------------------------------------------------------------- */
      row.cost =
        fixedCostPerTank[fuel.name] +
        shellCost +
        liquefactionCost;
    },

    formatCost(value) {
      return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
    }
  },
};

// // Placeholder formula constants
// const storageCostPerKgLH2 = 50; // USD/kg for Liquefied Hydrogen storage
// const liquefactionCostPerKgLH2 = 1.2; // USD/kg for liquefaction

// // const densities = {
// //   'Compressed Hydrogen': 70.8, // kg/m3
// //   Ammonia: 682,
// //   Methanol: 792,
// //   LNG: 450,
// // };

// // const unitInstallationCosts = {
// //   'Compressed Hydrogen': 600, // USD/m3
// //   Ammonia: 2000,
// //   Methanol: 1000,
// //   LNG: 2000,
// // };

// // Compute installation cost based on fuel type and capacity
// function computeCost(fuel, capacity) {
//   if (capacity <= 0) return 0; // No cost for 0 capacity

//   let cost = 0;

//   switch (fuel.name) {
//     case 'Liquid Hydrogen':
//       cost =
//         capacity * 1000 * (storageCostPerKgLH2 + liquefactionCostPerKgLH2);
//       break;

//     case 'Compressed Hydrogen':
//       //const volumeCH2 = (capacity * 1000) / densities['Compressed Hydrogen']; // m3
//       //cost = volumeCH2 * unitInstallationCosts['Compressed Hydrogen'];
//       break;

//     case 'Ammonia':
//       //const volumeAmmonia = (capacity * 1000) / densities.Ammonia; // m3
//       //cost = volumeAmmonia * unitInstallationCosts.Ammonia;
//       break;

//     case 'Methanol':
//       //const volumeMethanol = (capacity * 1000) / densities.Methanol; // m3
//       //cost = volumeMethanol * unitInstallationCosts.Methanol;
//       break;

//     case 'LNG':
//       //const volumeLNG = (capacity * 1000) / densities.LNG; // m3
//       //cost = volumeLNG * unitInstallationCosts.LNG;
//       break;

//     default:
//       cost = capacity * 1000; // Fallback cost (e.g., for MGO)
//   }

//   return Math.round(cost); // Return rounded cost in USD
// }
// </script>

<style scoped>
.container {
  margin-top: 20px;
}

/* Remove the tabs-content-container flex styling */
.tabs-content-container {
  display: flex;
}

.b-tabs .nav-link.active {
  background-color: #fff !important;
  color: black !important;
}

/* Content Container */
.content-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* Centers items horizontally */
  padding: 20px;
}

/* Center the table */
.table-container {
  width: 100%;
  max-width: 600px;
  /* Limits the table width */
}

.fuel-table {
  width: 100%;
  border-collapse: collapse;
}

.fuel-table th,
.fuel-table td {
  padding: 10px;
  text-align: center;
  border: 1px solid #ddd;
}

.fuel-table th {
  background-color: #f2f2f2;
}

/* Set specific width for Storage Volume column */
.storage-volume-header,
.storage-volume-cell {
  width: 100%;
  /* Adjust width as needed */
  text-align: center;
}

.fuel-table input[type="number"] {
  width: 100px;
}

.cost-inputs {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 20px;
}

.change-rate label {
  margin-right: 10px;
  white-space: nowrap;
}

.change-rate input[type="number"] {
  width: 80px;
}

.change-rate {
  margin-top: 20px;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 600px;
}

/* Fuel Bar Colors */
.fuel-square {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border: 1px solid black;
  vertical-align: middle;
}

.mgo-bar {
  background-color: #007bff;
}

.lh2-bar {
  background-color: #28a745;
}

.ch2-bar {
  background-color: #17a2b8;
}

.ammonia-bar {
  background-color: #ffc107;
}

.methanol-bar {
  background-color: #dc3545;
}

.lng-bar {
  background-color: #6f42c1;
}
</style>
