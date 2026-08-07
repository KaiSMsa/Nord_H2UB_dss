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

            <div class="financial-assumptions">
              <fieldset class="fuel-financial-frame">
                <legend>{{ fuel.name }} - Financial costs</legend>

                <div class="assumption-row">
                  <div class="assumption-field">
                    <label
                      title="Annual expected change in technology cost. Negative values represent cost reductions."
                    >Annual cost adjustment (%)</label>
                    <input type="number" v-model.number="fuel.technologyCostAdjustmentRateAnnualPercent" placeholder="-2" min="-99.99" required
                      :disabled="isDisabled"
                      @input="emitCleanData" @blur="normalizeNumberField(fuel, 'technologyCostAdjustmentRateAnnualPercent', 0); emitCleanData()" />
                  </div>

                  <div class="assumption-field">
                    <label
                      title="Annual maintenance cost as a share of base investment. The backend aggregates it over each planning period."
                    >Annual maintenance rate (%)</label>
                    <input type="number" v-model.number="fuel.maintenanceRateAnnualPercent" placeholder="4" min="0" required
                      :disabled="isDisabled"
                      @input="emitCleanData" @blur="normalizeNumberField(fuel, 'maintenanceRateAnnualPercent', 0); emitCleanData()" />
                  </div>
                </div>

                <div class="assumption-row assumption-row-single">
                  <div class="assumption-field">
                    <label
                      title="Applied once to the base investment cost when the storage asset is decommissioned."
                    >Decommissioning rate at closure (%)</label>
                    <input type="number" v-model.number="fuel.decommissioningRateAtClosurePercent" placeholder="10" min="0" required
                      :disabled="isDisabled"
                      @input="emitCleanData" @blur="normalizeNumberField(fuel, 'decommissioningRateAtClosurePercent', 0); emitCleanData()" />
                  </div>
                </div>
              </fieldset>

              <div class="assumption-row assumption-row-single shared-financial-assumption">
                <div class="assumption-field">
                  <label
                    title="Shared across all fuels. Annual rate used to convert future costs into present-value terms. The neutral 0% default requires author approval before production use."
                  >Annual discount rate (%)</label>
                  <input type="number" v-model.number="localData.discountRateAnnualPercent" placeholder="0" min="-99.99" step="0.1" required
                    :class="{ 'is-invalid': isDiscountRateInvalid() }" :disabled="isDisabled"
                    @input="emitCleanData"
                    @blur="normalizeNumberField(localData, 'discountRateAnnualPercent', defaultDiscountRateAnnualPercent); emitCleanData()" />
                  <small v-if="isDiscountRateInvalid()" class="assumption-error">
                    Discount rate must be greater than -100%.
                  </small>
                </div>
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
import { PLANNING_PERIOD_YEARS } from "@/constants/planningYears.js";
import {
  calculateDiscountFactor,
  calculatePresentValueCost,
  calculateTimeAdjustedInvestmentCost,
  estimateTankOption,
  fuelParameterCatalog,
  getFuelParameters,
} from "@/utils/tankCost.js";
import { formatUSDWithoutDecimals } from "@/utils/currencyFormatting.js";
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
      defaultDiscountRateAnnualPercent:
        fuelParameterCatalog.common.defaultDiscountRateAnnual * 100,
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

      const rateValue = (currentValue, legacyValue, fallback) => {
        const candidate = currentValue ?? legacyValue;
        const number = Number(candidate);
        return candidate !== "" && Number.isFinite(number) ? number : fallback;
      };
      const equivalentAnnualPercent = (planningPeriodPercent) => {
        if (
          planningPeriodPercent === "" ||
          planningPeriodPercent === null ||
          planningPeriodPercent === undefined
        ) return undefined;
        const percentage = Number(planningPeriodPercent);
        if (!Number.isFinite(percentage) || percentage <= -100) return undefined;
        return (
          (Math.pow(
            1 + percentage / 100,
            1 / PLANNING_PERIOD_YEARS
          ) - 1) * 100
        );
      };
      const annualMaintenancePercent = (planningPeriodPercent) => {
        if (
          planningPeriodPercent === "" ||
          planningPeriodPercent === null ||
          planningPeriodPercent === undefined
        ) return undefined;
        const percentage = Number(planningPeriodPercent);
        return Number.isFinite(percentage)
          ? percentage / PLANNING_PERIOD_YEARS
          : undefined;
      };
      const firstFuel = this.localData.fuels[0] || {};
      const legacyDiscountRatePercent =
        this.localData.discountRatePercent
        ?? this.localData.discountRate
        ?? firstFuel.discountRatePercent
        ?? firstFuel.discountRate;
      this.localData.discountRateAnnualPercent = rateValue(
        this.localData.discountRateAnnualPercent,
        equivalentAnnualPercent(legacyDiscountRatePercent),
        this.defaultDiscountRateAnnualPercent
      );
      delete this.localData.discountRate;
      delete this.localData.discountRatePercent;
      this.localData.transitionCostRate ??=
        fuelParameterCatalog.common.transitionCostRate;

      const existing = new Map(this.localData.fuels.map((f) => [f.name, f]));
      const merged = FUELS.map((def) => {
        const f = existing.get(def.name);
        if (!f) return this.createFuelState(def.name, def.class);

        const currentState = { ...f };
        delete currentState.discountRate;
        delete currentState.discountRatePercent;
        delete currentState.changeRate;
        delete currentState.technologyCostAdjustmentRatePercent;
        delete currentState.maintenanceCost;
        delete currentState.maintenanceRatePercent;
        delete currentState.decommissioningCost;

        return {
          ...currentState,
          id: def.id,
          class: def.class,
          technologyCostAdjustmentRateAnnualPercent: rateValue(
            f.technologyCostAdjustmentRateAnnualPercent,
            equivalentAnnualPercent(
              f.technologyCostAdjustmentRatePercent ?? f.changeRate
            ),
            fuelParameterCatalog.common
              .defaultTechnologyCostAdjustmentRateAnnual * 100
          ),
          maintenanceRateAnnualPercent: rateValue(
            f.maintenanceRateAnnualPercent,
            annualMaintenancePercent(
              f.maintenanceRatePercent ?? f.maintenanceCost
            ),
            fuelParameterCatalog.common.maintenanceRateAnnual * 100
          ),
          decommissioningRateAtClosurePercent: rateValue(
            f.decommissioningRateAtClosurePercent,
            f.decommissioningCost,
            fuelParameterCatalog.common.decommissioningRateAtClosure * 100
          ),
        };
      });

      this.localData.fuels = merged;
    },
    createFuelState(name, cssClass) {
      return {
        id: FUEL_BY_NAME[name]?.id,
        name,
        class: cssClass,
        rows: [],
        technologyCostAdjustmentRateAnnualPercent:
          fuelParameterCatalog.common
            .defaultTechnologyCostAdjustmentRateAnnual * 100,
        maintenanceRateAnnualPercent:
          fuelParameterCatalog.common.maintenanceRateAnnual * 100,
        decommissioningRateAtClosurePercent:
          fuelParameterCatalog.common.decommissioningRateAtClosure * 100,
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
      if (obj[key] === "" || obj[key] === null || obj[key] === undefined) return;
      const v = Number(obj[key]);
      obj[key] = Number.isFinite(v) ? v : fallback;
    },
    isDiscountRateInvalid() {
      if (
        this.localData.discountRateAnnualPercent === "" ||
        this.localData.discountRateAnnualPercent === null ||
        this.localData.discountRateAnnualPercent === undefined
      ) return true;
      const ratePercent = Number(this.localData.discountRateAnnualPercent);
      return !Number.isFinite(ratePercent) || ratePercent <= -100;
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
      return formatUSDWithoutDecimals(x);
    },
    fmtNumber(x) {
      return new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 6,
      }).format(Number(x || 0));
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
      const discountRateAnnual =
        Number(this.localData.discountRateAnnualPercent) / 100;
      const technologyCostAdjustmentRateAnnual =
        Number(fuel.technologyCostAdjustmentRateAnnualPercent) / 100;
      const hasValidDiscountRate =
        Number.isFinite(discountRateAnnual) && discountRateAnnual > -1;
      const financialLines = [];

      if (hasValidDiscountRate) {
        const periodOneDiscountFactor = calculateDiscountFactor(
          discountRateAnnual,
          PLANNING_PERIOD_YEARS
        );
        const periodOneAdjustedInvestmentCost =
          calculateTimeAdjustedInvestmentCost(
            result.baseInvestmentCostUSD,
            technologyCostAdjustmentRateAnnual,
            PLANNING_PERIOD_YEARS
          );
        const periodOnePresentValueInvestmentCost = calculatePresentValueCost(
          periodOneAdjustedInvestmentCost,
          periodOneDiscountFactor
        );

        financialLines.push(
          `<li><strong>Period 1 technology adjustment:</strong> Base cost × (1 + ${technologyCostAdjustmentRateAnnual})<sup>${PLANNING_PERIOD_YEARS}</sup> = ${this.fmtUSD(periodOneAdjustedInvestmentCost)} USD.</li>`,
          `<li><strong>Period 1 discount factor:</strong> 1 / (1 + ${discountRateAnnual})<sup>${PLANNING_PERIOD_YEARS}</sup> = ${periodOneDiscountFactor.toFixed(6)}.</li>`,
          `<li><strong>Period 1 present value:</strong> Adjusted cost × discount factor = ${this.fmtUSD(periodOnePresentValueInvestmentCost)} USD.</li>`
        );
      } else {
        financialLines.push(
          "<li><strong>Discount rate:</strong> Enter a value greater than -100% to calculate present values.</li>"
        );
      }

      return [
        `<li><strong>Input:</strong> ${result.capacityMgoEquivalentTonnes} t MGO-e.</li>`,
        `<li><strong>Physical mass:</strong> ${result.capacityMgoEquivalentTonnes} × ${result.mgoLowerHeatingValueMJPerKg} / ${result.fuelLowerHeatingValueMJPerKg} = ${result.physicalMassTonnes.toFixed(2)} t.</li>`,
        `<li><strong>Storage volume:</strong> ${result.physicalMassTonnes.toFixed(2)} × 1000 / ${result.densityKgPerM3} = ${result.storageVolumeM3.toFixed(2)} m³.</li>`,
        `<li><strong>Shell cost:</strong> ${this.fmtNumber(result.shellCalibrationUSDPerM3)} × ${result.referenceVolumeM3} × (V / ${result.referenceVolumeM3})<sup>${result.scalingExponent}</sup> = ${this.fmtUSD(result.shellInstallationCostUSD)} USD.</li>`,
        `<li><strong>Base investment:</strong> ${this.fmtUSD(result.fixedInstallationCostUSD)} + ${this.fmtUSD(result.shellInstallationCostUSD)} = ${this.fmtUSD(result.baseInvestmentCostUSD)} USD.</li>`,
        ...financialLines,
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

.financial-assumptions {
  display: grid;
  width: 100%;
  max-width: 700px;
  gap: 18px;
  margin-top: 20px;
}

.fuel-financial-frame {
  display: grid;
  gap: 16px;
  min-width: 0;
  margin: 0;
  padding: 14px 16px 16px;
  border: 1px solid #ced4da;
  border-radius: 6px;
}

.fuel-financial-frame legend {
  float: none;
  width: auto;
  justify-self: start;
  margin: 0;
  padding: 0 8px;
  color: inherit;
  font-size: 1rem;
  font-weight: 400;
  text-align: left;
}

.assumption-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.assumption-row-single > .assumption-field {
  grid-column: 1;
}

.shared-financial-assumption {
  padding-left: 16px;
}

.assumption-field {
  display: grid;
  grid-template-rows: minmax(2.7em, auto) auto auto;
  align-content: start;
  align-items: start;
  gap: 6px;
}

.assumption-field label {
  width: 100%;
  margin: 0;
  font-weight: 400;
  line-height: 1.35;
  text-align: left;
  cursor: help;
}

.assumption-field input[type="number"] {
  width: 120px;
  justify-self: start;
}

.assumption-error {
  color: #721c24;
}

@media (max-width: 700px) {
  .assumption-row {
    grid-template-columns: 1fr;
  }

  .shared-financial-assumption {
    padding-left: 0;
  }
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
