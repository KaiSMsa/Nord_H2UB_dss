<template>
  <div class="container">
    <h3>Adjust possible fuel tank sizes</h3>

    <b-card no-body>
      <b-tabs card>
        <b-tab
          v-for="(fuel) in fuels"
          :key="fuel.name"
          :title="fuel.name"
          :title-item-class="'d-flex align-items-center'"
        >
          <!-- Tab Title with Fuel Name and Colored Square -->
          <template #title>
            <span class="fuel-square" :class="fuel.class"></span>
            {{ fuel.name }}
          </template>

          <!-- Content within each tab -->
          <div class="content-container">
            <div class="table-container">
              <table class="fuel-table">
                <thead>
                  <tr>
                    <th>Capacity (t&nbsp;MGO‑eq)</th>
                    <th>Storage Volume (m³)</th>
                    <th>Estimation Cost ($)</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in fuel.rows" :key="rowIndex">
                    <td class="input-cell">
                      <input
                        type="number"
                        v-model.number="row.capacity"
                        placeholder="Tonnes"
                        :class="{ 'is-invalid': row.isInvalid }"
                        min="0"
                        step="100"
                        :disabled="disabled || trueCondition"
                        @input="onCapacityInput(fuel, row)"
                        @blur="onCapacityBlur(fuel)"
                      />
                      <transition name="fade">
                        <div v-if="row.isInvalid" class="error-box">
                          {{ row.error }}
                        </div>
                      </transition>
                    </td>

                    <td>{{ row.storageVolume.toFixed(0) }} m³</td>
                    <td>{{ formatCost(row.cost) }} $</td>
                    <td>
                      <b-button
                        size="sm"
                        variant="danger"
                        :disabled="disabled || trueCondition || fuel.rows.length === 1"
                        @click="removeRow(fuel, rowIndex)"
                      >
                        Remove
                      </b-button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <b-button
              size="sm"
              variant="success"
              class="mt-2"
              :disabled="disabled || trueCondition"
              @click="addRow(fuel)"
            >
              New tanker capacity
            </b-button>

            <div class="cost-inputs">
              <div class="change-rate">
                <label>Change Rate (%):</label>
                <input
                  type="number"
                  v-model.number="fuel.changeRate"
                  placeholder="Percentage"
                  min="-100"
                  max="100"
                  :disabled="disabled || trueCondition"
                />
              </div>
              <div class="change-rate">
                <label>Maintenance cost (%):</label>
                <input
                  type="number"
                  v-model.number="fuel.maintenanceCost"
                  placeholder="4"
                  min="0"
                  max="10"
                  :disabled="disabled || trueCondition"
                />
              </div>
              <div class="change-rate">
                <label>Decommissioning cost (%):</label>
                <input
                  type="number"
                  v-model.number="fuel.decommissioningCost"
                  placeholder="10"
                  min="0"
                  max="10"
                  :disabled="disabled || trueCondition"
                />
              </div>
            </div>
          </div>
        </b-tab>
      </b-tabs>
    </b-card>
  </div>
</template>

<script>
export default {
  name: "FuelCapacityEditor",
  props: {
    capacitySelection: { type: Object, required: true },
    disabled: { type: Boolean, default: false },
  },
  data() {
    return {
      localData: JSON.parse(JSON.stringify(this.capacitySelection)),
      stepSize: 100,
      // capacity limits in t MGO‑eq
      capacityLimits: {
        MGO: { min: 200, max: 10000 },
        "Liquid Hydrogen": { min: 2000, max: 7000 },
        "Compressed Hydrogen": { min: 4000, max: 6000 },
        Ammonia: { min: 500, max: 2000 },
        Methanol: { min: 500, max: 8000 },
        LNG: { min: 500, max: 10000 },
      },
    };
  },
  computed: {
    fuels() {
      return this.localData.fuels;
    },
  },
  watch: {
    localData: {
      handler() {
        this.emitCleanData();
      },
      deep: true,
    },
  },
  mounted() {
    this.fuels.forEach((fuel) => {
      if (fuel.rows.length === 0) this.addRow(fuel);
      fuel.rows.forEach((row) => {
        this.updateCalculations(fuel, row);
        this.validateCapacity(fuel, row);
      });
      this.sortRows(fuel);
    });
    this.emitCleanData(); // initial push
  },
  methods: {
    emitCleanData() {
      // deep clone then strip invalid rows
      const clean = JSON.parse(JSON.stringify(this.localData));
      clean.fuels.forEach((fuel) => {
        fuel.rows = fuel.rows.filter((r) => !r.isInvalid);
        if (fuel.rows.length === 0) {
          // ensure at least a placeholder so parent has slot
          fuel.rows.push({ capacity: null, cost: 0, storageVolume: 0 });
        }
      });
      this.$emit("update:capacitySelection", clean);
    },

    addRow(fuel) {
      fuel.rows.push({ capacity: 0, cost: 0, storageVolume: 0, isInvalid: false, error: "" });
    },
    removeRow(fuel, index) {
      if (fuel.rows.length > 1) {
        fuel.rows.splice(index, 1);
        this.emitCleanData();
      }
    },

    onCapacityInput(fuel, row) {
      this.validateCapacity(fuel, row);
      if (!row.isInvalid) {
        this.updateCalculations(fuel, row);
      } else {
        row.cost = 0;
        row.storageVolume = 0;
      }
    },
    onCapacityBlur(fuel) {
      this.sortRows(fuel);
      this.emitCleanData();
    },

    sortRows(fuel) {
      fuel.rows.sort((a, b) => Number(a.capacity || 0) - Number(b.capacity || 0));
    },

    validateCapacity(fuel, row) {
      row.isInvalid = false;
      row.error = "";
      const limits = this.capacityLimits[fuel.name] || null;
      if (
        limits &&
        (row.capacity < limits.min || row.capacity > limits.max || row.capacity === null)
      ) {
        row.isInvalid = true;
        row.error = `Allowed range: ${limits.min} – ${limits.max}`;
      } else {
        const dup = fuel.rows.some(
          (r) => r !== row && Number(r.capacity) === Number(row.capacity)
        );
        if (dup) {
          row.isInvalid = true;
          row.error = "Capacity duplicates another entry";
        }
      }
    },

    /* cost helpers */
    scaledShellCost(storageVolumeM3, baseUSDperM3, alpha = 0.65) {
      const V_REF = 1000;
      const k = baseUSDperM3 * Math.pow(V_REF, 1 - alpha);
      return k * Math.pow(storageVolumeM3, alpha);
    },

    updateCalculations(fuel, row) {
      const fixedCostPerTank = {
        MGO: 500000,
        "Liquid Hydrogen": 2000000,
        "Compressed Hydrogen": 20000000,
        Ammonia: 3000000,
        Methanol: 2500000,
        LNG: 500000,
      };

      const FUEL_PROPS = {
        MGO: { ρ: 850, EC: 42.8, cShell: 1000 },
        "Liquid Hydrogen": { ρ: 70.8, EC: 120, cShell: 50, cLiquef: 1.2 },
        "Compressed Hydrogen": { ρ: 70.8, EC: 120, cShell: 600 },
        Ammonia: { ρ: 682, EC: 18.6, cShell: 2000 },
        Methanol: { ρ: 792, EC: 19.9, cShell: 1000 },
        LNG: { ρ: 450, EC: 50, cShell: 2000 },
      };

      if (!FUEL_PROPS[fuel.name]) {
        row.cost = Math.round(row.capacity * 100);
        return;
      }

      const { ρ, EC, cShell, cLiquef } = FUEL_PROPS[fuel.name];
      const capacityMJ = row.capacity * 42.8 * 1000;

      if (fuel.name === "MGO") {
        row.storageVolume = Math.round((row.capacity * 1000) / ρ);
      } else {
        const tonnesAlt = Math.round(capacityMJ / EC / 1000);
        row.storageVolume = Math.round((tonnesAlt * 1000) / ρ);
      }

      const shellCost = this.scaledShellCost(row.storageVolume, cShell);
      const liquefactionCost =
        fuel.name === "Liquid Hydrogen" ? (capacityMJ / EC) * cLiquef : 0;

      row.cost = fixedCostPerTank[fuel.name] + shellCost + liquefactionCost;
    },

    formatCost(value) {
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
    },
  },
};
</script>

<style scoped>
.container {
  margin-top: 20px;
}

/* Tabs */
.b-tabs .nav-link.active {
  background-color: #fff !important;
  color: black !important;
}

/* Content Container */
.content-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.table-container {
  width: 100%;
  max-width: 700px;
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

.input-cell {
  position: relative;
}

.fuel-table input[type="number"] {
  width: 120px;
}

/* new error box */
.error-box {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  margin-top: 4px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 0.75rem;
  z-index: 2;
}

.is-invalid {
  border-color: #dc3545 !important;
}

.cost-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 20px;
}

.change-rate {
  display: flex;
  align-items: center;
  gap: 8px;
}

.change-rate input[type="number"] {
  width: 80px;
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
