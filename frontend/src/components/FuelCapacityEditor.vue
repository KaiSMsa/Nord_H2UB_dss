<template>
  <div class="container">
    <h3>Adjust possible fuel tank sizes</h3>

    <b-card no-body>
      <b-tabs card>
        <b-tab v-for="fuel in localData.fuels" :key="fuel.name" :title="fuel.name"
          :title-item-class="'d-flex align-items-center'">
          <template #title>
            <span class="fuel-square" :class="fuel.class"></span>
            {{ fuel.name }}
          </template>

          <div class="content-container">
            <div class="table-container">
              <table class="fuel-table">
                <thead>
                  <tr>
                    <th>Capacity (t&nbsp;MGO-eq)</th>
                    <th>Storage Volume (m³)</th>
                    <th>Estimation Cost ($)</th>
                    <th></th>
                  </tr>
                </thead>

                <tbody>
                  <tr v-for="(row, rowIndex) in fuel.rows" :key="rowIndex">
                    <td class="input-cell">
                      <input type="number" v-model.number="row.capacity" placeholder="Tonnes"
                        :class="{ 'is-invalid': row.isInvalid }" min="0" :step="stepSize" :disabled="isDisabled"
                        @input="onCapacityInput(fuel, row)" @blur="onCapacityBlur(fuel)" />
                      <transition name="fade">
                        <div v-if="row.isInvalid" class="error-box">
                          {{ row.error }}
                        </div>
                      </transition>
                    </td>

                    <td>{{ Number(row.storageVolume || 0).toFixed(0) }} m³</td>
                    <td>{{ fmtUSD(row.cost) }} $</td>

                    <td>
                      <b-button size="sm" variant="danger" :disabled="isDisabled || fuel.rows.length === 1"
                        @click="removeRow(fuel, rowIndex)">
                        Remove
                      </b-button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <b-button size="sm" variant="success" class="mt-2" :disabled="isDisabled" @click="addRow(fuel)">
              New tanker capacity
            </b-button>

            <div class="cost-inputs">
              <div class="change-rate">
                <label>Cost adjustment per planning period (%):</label>
                <input type="number" v-model.number="fuel.changeRate" placeholder="Percentage" min="-100" max="100"
                  :disabled="isDisabled" 
                  @input="emitCleanData" @blur="normalizeNumberField(fuel, 'changeRate', 0); emitCleanData()"
                  />
              </div>

              <div class="change-rate">
                <label>Maintenance per planning period (%):</label>
                <input type="number" v-model.number="fuel.maintenanceCost" placeholder="4" min="0" max="10"
                  :disabled="isDisabled"
                  @input="emitCleanData" @blur="normalizeNumberField(fuel, 'maintenanceCost', 0); emitCleanData()"
                />
              </div>

              <div class="change-rate">
                <label>Decommissioning at closure (%):</label>
                <input type="number" v-model.number="fuel.decommissioningCost" placeholder="10" min="0" max="10"
                  :disabled="isDisabled"
                  @input="emitCleanData" @blur="normalizeNumberField(fuel, 'decommissioningCost', 0); emitCleanData()"
                />
              </div>
            </div>

            <!-- Cost estimation steps hover popover -->
            <div class="cost-steps mt-3">
              <span class="cost-steps-trigger" :id="stepsLinkId(fuel.name)" tabindex="0" role="button">
                <span class="cost-steps-link">Cost estimation steps</span>
              </span>

              <b-popover :target="stepsLinkId(fuel.name)" triggers="hover focus" placement="bottom" container="body"
                boundary="window" custom-class="steps-popover">
                <div class="steps-popover-body">
                  <ul class="mb-0" v-html="fuelTooltipHtml(fuel)"></ul>
                </div>
              </b-popover>
            </div>
          </div>
        </b-tab>
      </b-tabs>
    </b-card>
  </div>
</template>

<script>
import { FUELS, FUEL_BY_NAME } from "@/constants/fuels.js";
import {
  estimateTankOption,
  fuelParameterCatalog,
  getFuelParameters,
} from "@/utils/tankCost.js";
import cloneDeep from "lodash.clonedeep";

const STEP_SIZE = 100;

export default {
  name: "FuelCapacityEditor",
  props: {
    capacitySelection: { type: Object, required: true },
    disabled: { type: Boolean, default: false },
    trueCondition: { type: Boolean, default: false },
  },
  data() {
    return {
      localData: this.clone(this.capacitySelection),
      stepSize: STEP_SIZE,
      lastEmittedSignature: "",
    };
  },
  computed: {
    isDisabled() {
      return this.disabled || this.trueCondition;
    },

    // Always render tabs in FUELS order, but keep the underlying data in localData.fuels
    fuels() {
      const byName = new Map((this.localData?.fuels || []).map(f => [f.name, f]));
      return FUELS.map(def => {
        const existing = byName.get(def.name);
        if (existing) {
          // mutate existing to keep same reference
          existing.class = def.class;
          return existing;
        }
        // IMPORTANT: ensure it's actually stored, not just returned
        const created = this.createFuelState(def.name, def.class);
        this.localData.fuels.push(created);
        return created;
      });
    },
  },
  watch: {
    capacitySelection: {
      handler(next) {
        const sig = this.signature(next);
        if (sig === this.lastEmittedSignature) return;

        this.localData = this.clone(next);
        this.ensureFuelCoverage();
        this.initializeAllFuels();
      },
      deep: true,
    },
  },
  mounted() {
    this.ensureFuelCoverage();
    this.initializeAllFuels();
    this.emitCleanData();
  },
  methods: {
    /* ---------------------------
     * Data integrity / sync
     * --------------------------- */
    clone(obj) {
      return cloneDeep(obj);
    },
    signature(obj) {
      try {
        return JSON.stringify(obj || {});
      } catch {
        return "";
      }
    },
    ensureFuelCoverage() {
      if (!this.localData) this.localData = { fuels: [] };
      if (!Array.isArray(this.localData.fuels)) this.localData.fuels = [];

      const existing = new Map(this.localData.fuels.map((f) => [f.name, f]));
      const merged = FUELS.map((def) => {
        const f = existing.get(def.name);
        return f
          ? { ...f, id: def.id, class: def.class }
          : this.createFuelState(def.name, def.class);
      });

      this.localData.fuels = merged;
    },
    createFuelState(name, cssClass) {
      return {
        id: FUEL_BY_NAME[name]?.id,
        name,
        class: cssClass,
        rows: [],
        changeRate:
          fuelParameterCatalog.common.defaultFuelCostAdjustmentRatePerPeriod * 100,
        maintenanceCost: fuelParameterCatalog.common.maintenanceRate * 100,
        decommissioningCost:
          fuelParameterCatalog.common.decommissioningRate * 100,
      };
    },

    emitCleanData() {
      const clean = this.clone(this.localData);

      (clean.fuels || []).forEach((fuel) => {
        // Strip invalid capacity rows only
        fuel.rows = (fuel.rows || []).filter((r) => !r.isInvalid);

        if (fuel.rows.length === 0) {
          fuel.rows.push({ capacity: null, cost: 0, storageVolume: 0 });
        }

        // Preserve numeric fields (avoid parent resetting to defaults)
        // If user temporarily clears the input, v-model.number can become null/NaN.
        const normalizeNum = (v, fallback = 0) => {
          const n = Number(v);
          return Number.isFinite(n) ? n : fallback;
        };

        fuel.changeRate = normalizeNum(fuel.changeRate, 0);
        fuel.maintenanceCost = normalizeNum(fuel.maintenanceCost, 0);
        fuel.decommissioningCost = normalizeNum(fuel.decommissioningCost, 0);

        // Ensure class remains consistent with FUELS
        const def = FUEL_BY_NAME[fuel.name];
        if (def) fuel.class = def.class;
      });

      const sig = this.signature(clean);
      if (sig === this.lastEmittedSignature) return;
      this.lastEmittedSignature = sig;

      this.$emit("update:capacitySelection", clean);
    },


    /* ---------------------------
     * Init rows
     * --------------------------- */
    initializeAllFuels() {
      (this.localData?.fuels || []).forEach((fuel) => {
        if (!Array.isArray(fuel.rows)) fuel.rows = [];
        if (fuel.rows.length === 0) this.addRow(fuel, { emit: false });

        fuel.rows.forEach((row) => {
          this.normalizeRow(row);
          this.recomputeRow(fuel, row);
        });

        this.sortRows(fuel);
      });
    },
    normalizeRow(row) {
      row.capacity = row.capacity ?? 0;
      row.cost = row.cost ?? 0;
      row.storageVolume = row.storageVolume ?? 0;
      row.isInvalid = row.isInvalid ?? false;
      row.error = row.error ?? "";
    },
    sortRows(fuel) {
      fuel.rows.sort((a, b) => Number(a.capacity || 0) - Number(b.capacity || 0));
    },
    normalizeNumberField(obj, key, fallback = 0) {
      const v = Number(obj[key]);
      obj[key] = Number.isFinite(v) ? v : fallback;
    },
    /* ---------------------------
     * Row actions
     * --------------------------- */
    addRow(fuel, { emit = true } = {}) {
      fuel.rows.push({
        capacity: 0,
        cost: 0,
        storageVolume: 0,
        isInvalid: false,
        error: "",
      });
      if (emit) this.emitCleanData();
    },
    removeRow(fuel, index) {
      if (fuel.rows.length <= 1) return;
      fuel.rows.splice(index, 1);
      this.emitCleanData();
    },

    /* ---------------------------
     * Input handlers
     * --------------------------- */
    onCapacityInput(fuel, row) {
      this.recomputeRow(fuel, row);
      this.emitCleanData();
    },
    onCapacityBlur(fuel) {
      this.sortRows(fuel);
      this.emitCleanData();
    },

    recomputeRow(fuel, row) {
      this.validateCapacity(fuel, row);
      if (row.isInvalid) {
        row.calculation = null;
        row.cost = 0;
        row.storageVolume = 0;
        return;
      }
      this.updateCalculations(fuel, row);
    },

    /* ---------------------------
     * Validation
     * --------------------------- */
    validateCapacity(fuel, row) {
      row.isInvalid = false;
      row.error = "";

      const parameters = getFuelParameters(fuel.id || fuel.name);

      const cap = row.capacity;
      if (cap === null || cap === "" || Number.isNaN(Number(cap))) {
        row.isInvalid = true;
        row.error = "Please enter a capacity";
        return;
      }

      const n = Number(cap);

      if (
        n < parameters.minimumCapacityMgoEquivalentTonnes ||
        n > parameters.maximumCapacityMgoEquivalentTonnes
      ) {
        row.isInvalid = true;
        row.error = `Allowed range: ${parameters.minimumCapacityMgoEquivalentTonnes} – ${parameters.maximumCapacityMgoEquivalentTonnes}`;
        return;
      }

      const dup = fuel.rows.some((r) => r !== row && Number(r.capacity) === n);
      if (dup) {
        row.isInvalid = true;
        row.error = "Capacity duplicates another entry";
      }
    },

    /* ---------------------------
     * Cost / Volume model
     * --------------------------- */
    updateCalculations(fuel, row) {
      const result = estimateTankOption(fuel.id || fuel.name, row.capacity);
      row.calculation = result;
      row.storageVolume = result.storageVolumeM3;
      row.cost = result.baseInvestmentCostUSD;
    },

    /* ---------------------------
     * UI helpers
     * --------------------------- */
    fmtUSD(x) {
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(
        Number(x || 0)
      );
    },
    slugify(name) {
      return String(name).toLowerCase().replace(/\s+/g, "-").replace(/[^\w-]/g, "");
    },
    stepsLinkId(fuelName) {
      return `cost-steps-${this.slugify(fuelName)}`;
    },

    fuelTooltipHtml(fuel) {
      const parameters = getFuelParameters(fuel.id || fuel.name);
      const firstValidRow = (fuel.rows || []).find((row) => !row.isInvalid);
      const capacity =
        Number(firstValidRow?.capacity) ||
        parameters.minimumCapacityMgoEquivalentTonnes;
      const result = estimateTankOption(fuel.id || fuel.name, capacity);

      return [
        `<li><strong>Input:</strong> ${result.capacityMgoEquivalentTonnes} t MGO-e.</li>`,
        `<li><strong>Physical mass:</strong> ${result.capacityMgoEquivalentTonnes} × ${result.mgoLowerHeatingValueMJPerKg} / ${result.fuelLowerHeatingValueMJPerKg} = ${result.physicalMassTonnes.toFixed(2)} t.</li>`,
        `<li><strong>Storage volume:</strong> ${result.physicalMassTonnes.toFixed(2)} × 1000 / ${result.densityKgPerM3} = ${result.storageVolumeM3.toFixed(2)} m³.</li>`,
        `<li><strong>Shell cost:</strong> ${this.fmtUSD(result.shellCalibrationUSDPerM3)} × ${result.referenceVolumeM3} × (V / ${result.referenceVolumeM3})<sup>${result.scalingExponent}</sup> = ${this.fmtUSD(result.shellInstallationCostUSD)} USD.</li>`,
        `<li><strong>Base investment:</strong> ${this.fmtUSD(result.fixedInstallationCostUSD)} + ${this.fmtUSD(result.shellInstallationCostUSD)} = ${this.fmtUSD(result.baseInvestmentCostUSD)} USD.</li>`,
        "<li><strong>Cost boundary:</strong> storage installation only; no liquefaction or compression cost is included.</li>",
      ].join("");
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

/* Error box */
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

/* Fuel color square (color comes from fuels.css classes) */
.fuel-square {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border: 1px solid black;
  vertical-align: middle;
}

.cost-steps {
  width: 100%;
  max-width: 700px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.cost-steps-trigger {
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.cost-steps-link {
  text-decoration: underline;
  cursor: pointer;
}

/* Popover is rendered into body -> use :deep so scoped styles apply */
:deep(.steps-popover) {
  max-width: 520px;
  font-size: 0.9rem;
}

:deep(.steps-popover ul) {
  padding-left: 18px;
  margin: 0;
}

:deep(.steps-popover li) {
  margin: 3px 0;
}
</style>
