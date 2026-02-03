<template>
  <div class="container">
    <h3>Adjust possible fuel tank sizes</h3>

    <b-card no-body>
      <b-tabs card>
        <b-tab
          v-for="fuel in fuels"
          :key="fuel.name"
          :title="fuel.name"
          :title-item-class="'d-flex align-items-center'"
        >
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
                      <input
                        type="number"
                        v-model.number="row.capacity"
                        placeholder="Tonnes"
                        :class="{ 'is-invalid': row.isInvalid }"
                        min="0"
                        :step="stepSize"
                        :disabled="isDisabled"
                        @input="onCapacityInput(fuel, row)"
                        @blur="onCapacityBlur(fuel)"
                      />
                      <transition name="fade">
                        <div v-if="row.isInvalid" class="error-box">
                          {{ row.error }}
                        </div>
                      </transition>
                    </td>

                    <td>{{ Number(row.storageVolume || 0).toFixed(0) }} m³</td>
                    <td>{{ fmtUSD(row.cost) }} $</td>

                    <td>
                      <b-button
                        size="sm"
                        variant="danger"
                        :disabled="isDisabled || fuel.rows.length === 1"
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
              :disabled="isDisabled"
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
                  :disabled="isDisabled"
                  @change="emitCleanData()"
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
                  :disabled="isDisabled"
                  @change="emitCleanData()"
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
                  :disabled="isDisabled"
                  @change="emitCleanData()"
                />
              </div>
            </div>

            <!-- Cost estimation steps hover popover -->
            <div class="cost-steps mt-3">
              <span
                class="cost-steps-trigger"
                :id="stepsLinkId(fuel.name)"
                tabindex="0"
                role="button"
              >
                <span class="cost-steps-link">Cost estimation steps</span>
              </span>

              <b-popover
                :target="stepsLinkId(fuel.name)"
                triggers="hover focus"
                placement="bottom"
                container="body"
                boundary="window"
                custom-class="steps-popover"
              >
                <div class="steps-popover-body">
                  <ul class="mb-0" v-html="fuelTooltipHtml(fuel.name)"></ul>
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

const STEP_SIZE = 100;
const ALPHA = 0.65;
const V_REF = 1000;
const MJ_PER_KG_MGO = 42.8;

// Local-only model (kept here since you said it’s only used here)
const FUEL_MODEL = {
  MGO: {
    limits: { min: 2000, max: 10000 },
    fixed: 500000,
    props: { rho: 850, EC: 42.8, cShell: 1000 },
  },
  "Liquid Hydrogen": {
    limits: { min: 2000, max: 7000 },
    fixed: 2000000,
    props: { rho: 70.8, EC: 120, cShell: 50, cLiquef: 1.2 },
  },
  "Compressed Hydrogen": {
    limits: { min: 3000, max: 6000 },
    fixed: 20000000,
    props: { rho: 70.8, EC: 120, cShell: 600 },
  },
  Ammonia: {
    limits: { min: 1000, max: 7000 },
    fixed: 3000000,
    props: { rho: 682, EC: 18.6, cShell: 2000 },
  },
  Methanol: {
    limits: { min: 1000, max: 10000 },
    fixed: 2500000,
    props: { rho: 792, EC: 19.9, cShell: 1000 },
  },
  LNG: {
    limits: { min: 1000, max: 10000 },
    fixed: 500000,
    props: { rho: 450, EC: 50, cShell: 2000 },
  },
};

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
      const byName = new Map((this.localData?.fuels || []).map((f) => [f.name, f]));
      return FUELS.map((def) => {
        const existing = byName.get(def.name);
        return existing
          ? { ...existing, class: def.class } // ensure class follows shared constants
          : this.createFuelState(def.name, def.class);
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
      return JSON.parse(JSON.stringify(obj));
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
        return f ? { ...f, class: def.class } : this.createFuelState(def.name, def.class);
      });

      this.localData.fuels = merged;
    },
    createFuelState(name, cssClass) {
      return {
        name,
        class: cssClass,
        rows: [],
        changeRate: 0,
        maintenanceCost: 4,
        decommissioningCost: 10,
      };
    },

    emitCleanData() {
      const clean = this.clone(this.localData);

      (clean.fuels || []).forEach((fuel) => {
        fuel.rows = (fuel.rows || []).filter((r) => !r.isInvalid);

        if (fuel.rows.length === 0) {
          fuel.rows.push({ capacity: null, cost: 0, storageVolume: 0 });
        }

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
        row.cost = 0;
        row.storageVolume = 0;
        return;
      }
      this.updateCalculations(fuel, row);
    },

    /* ---------------------------
     * Validation
     * --------------------------- */
    getFuelModel(fuelName) {
      return FUEL_MODEL[fuelName] || null;
    },
    validateCapacity(fuel, row) {
      row.isInvalid = false;
      row.error = "";

      const model = this.getFuelModel(fuel.name);
      const limits = model?.limits;

      const cap = row.capacity;
      if (cap === null || cap === "" || Number.isNaN(Number(cap))) {
        row.isInvalid = true;
        row.error = "Please enter a capacity";
        return;
      }

      const n = Number(cap);

      if (limits && (n < limits.min || n > limits.max)) {
        row.isInvalid = true;
        row.error = `Allowed range: ${limits.min} – ${limits.max}`;
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
    scaledShellCost(volumeM3, baseUSDperM3, alpha = ALPHA) {
      const V = Math.max(Number(volumeM3) || 0, 0);
      const k = baseUSDperM3 * Math.pow(V_REF, 1 - alpha);
      return k * Math.pow(V, alpha);
    },
    updateCalculations(fuel, row) {
      const model = this.getFuelModel(fuel.name);
      if (!model) return;

      const capT = Number(row.capacity || 0);
      const { fixed, props } = model;
      const { rho, EC, cShell } = props;
      const cLiquef = props.cLiquef || 0;

      const capacityMJ = capT * MJ_PER_KG_MGO * 1000;

      const volumeM3 =
        fuel.name === "MGO"
          ? (capT * 1000) / rho
          : (capacityMJ / EC) / rho;

      row.storageVolume = Math.round(volumeM3);

      const shellCost = this.scaledShellCost(row.storageVolume, cShell);
      const liquefactionCost =
        fuel.name === "Liquid Hydrogen" ? (capacityMJ / EC) * cLiquef : 0;

      row.cost = Math.round(fixed + shellCost + liquefactionCost);
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

    fuelTooltipHtml(fuelName) {
      const model = this.getFuelModel(fuelName);
      if (!model) return "<li>Cost estimation details are not available for this fuel.</li>";

      const { fixed, props } = model;
      const lines = [];

      lines.push(`<li><strong>Input:</strong> Tank capacity in <em>t MGO-eq</em>.</li>`);

      if (fuelName === "MGO") {
        lines.push(
          `<li><strong>Storage volume:</strong> V = (capacity × 1000) / ρ, with ρ = ${props.rho} kg/m³.</li>`
        );
      } else {
        lines.push(
          `<li><strong>Energy equivalence:</strong> E = capacity × 42.8 MJ/kg × 1000 (kg/t).</li>`
        );
        lines.push(
          `<li><strong>Fuel mass:</strong> m = E / EC, with EC = ${props.EC} MJ/kg.</li>`
        );
        lines.push(
          `<li><strong>Storage volume:</strong> V = m / ρ, with ρ = ${props.rho} kg/m³.</li>`
        );
      }

      lines.push(`<li><strong>Fixed cost per tank:</strong> ${this.fmtUSD(fixed)} USD.</li>`);
      lines.push(
        `<li><strong>Tank shell cost basis:</strong> ${this.fmtUSD(props.cShell)} USD/m³.</li>`
      );
      lines.push(
        `<li><strong>Economies of scale:</strong> Shell cost scales as C<sub>shell</sub> = k·V<sup>${ALPHA}</sup>, with α = ${ALPHA}.</li>`
      );
      lines.push(
        `<li><strong>Calibration:</strong> k is chosen so that at V<sub>ref</sub> = ${V_REF} m³, the scaled cost equals the linear cost (${this.fmtUSD(
          props.cShell
        )}×V<sub>ref</sub>).</li>`
      );

      if (fuelName === "Liquid Hydrogen") {
        lines.push(
          `<li><strong>Liquefaction cost:</strong> ${props.cLiquef} USD/kg × hydrogen mass (linear with m).</li>`
        );
      }
      if (fuelName === "Ammonia") {
        lines.push(
          `<li><strong>Ammonia assumption:</strong> liquid anhydrous NH₃ (refrigerated, near-atmospheric storage).</li>`
        );
      }

      lines.push(
        `<li><strong>Total investment (per tank):</strong> C = fixed + C<sub>shell</sub>${
          fuelName === "Liquid Hydrogen" ? " + liquefaction" : ""
        }.</li>`
      );

      return lines.join("");
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
