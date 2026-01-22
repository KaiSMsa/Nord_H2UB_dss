<template>
  <div class="container">
    <h3>Set the fuel storage capacity</h3>

    <!-- Form with inputs for each fuel type, labels and inputs aligned horizontally -->
    <b-form>
      <b-form-group v-for="(amount, fuel) in localData.portFuelInformation.fuelAmounts" :key="fuel"
        :label="`${fuel} [tonnes]`" :label-for="`${fuel}-input`" label-cols="6" label-align="left">
        <b-form-input
          :id="`${fuel}-input`"
          type="number"
          v-model.number="localData.portFuelInformation.fuelAmounts[fuel]"
          :min="0" max="200000" step="100"
          :disabled="locked"
          @input="calculateTotals"
        />
      </b-form-group>
    </b-form>

    <!-- Display total amounts -->
    <div class="totals">
      <p><strong>Total amount in MGO-equivalent:</strong> {{ this.localData.portFuelInformation.totalMGOEquivalent }}
        tonnes</p>
      <p><strong>Total amount in MJ:</strong> {{ formatMJ(totalMJ) }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PortFuelCapacity',
  props: {
    scenarioData: {type: Object, required: true},
    locked: {type: Boolean, default: false}
  },
  data() {
    return {
      localData: this.scenarioData,
      totalMJ: 0,
      conversionFactors: {
        MGO: { mgoEquivalent: 1.0, mjPerTon: 42900 },
        MDO: { mgoEquivalent: 0.98, mjPerTon: 42700 },
        IFO: { mgoEquivalent: 0.95, mjPerTon: 42400 },
        VLSFO: { mgoEquivalent: 0.97, mjPerTon: 42600 },
        HFO: { mgoEquivalent: 0.93, mjPerTon: 42200 }
      }
    };
  },
  watch: {
    localData: {
      handler(newVal) {
        this.$emit('update:scenarioData', newVal);
      },
      deep: true
    }
  },
  methods: {
    calculateTotals() {
      let totalMGO = 0;
      let totalMJ = 0;
      for (const fuel in this.localData.portFuelInformation.fuelAmounts) {
        const amount = this.localData.portFuelInformation.fuelAmounts[fuel] || 0;
        const factors = this.conversionFactors[fuel];
        totalMGO += amount * factors.mgoEquivalent;
        totalMJ += amount * factors.mjPerTon;
      }
      totalMGO = Math.ceil(totalMGO / 100) * 100;
      if (!this.localData.isStep1Initial && this.localData.portFuelInformation.totalMGOEquivalent != totalMGO) //the totalMGO has been changed, then reset Step 2
        this.localData.isStep1Initial = true;

      this.localData.portFuelInformation.totalMGOEquivalent = totalMGO;
      this.totalMJ = totalMJ;

      if (this.localData.isStep1Initial) {
        this.localData.fuelBarSelection.intervals.forEach((interval, index) => {
          if (index > 2)  //apply a 10% increase for the last two time periods
            totalMGO = Math.ceil(totalMGO * 1.1 / 100) * 100;

          interval.totalAmount = totalMGO;
          if (index == 0)
            interval.fuelValues.MGO = totalMGO;
          else if (index === 1) {
            interval.fuelValues.MGO = Math.round((totalMGO * 0.6) / 100) * 100;
            interval.fuelValues['Liquid Hydrogen'] = Math.round((totalMGO * 0.3) / 100) * 100;
            interval.fuelValues.LNG = Math.round((totalMGO * 0.1) / 100) * 100;
          }
          else if (index === 2) {
            interval.fuelValues.MGO = Math.round((totalMGO * 0.3) / 100) * 100;
            interval.fuelValues['Liquid Hydrogen'] = Math.round((totalMGO * 0.6) / 100) * 100;
            interval.fuelValues.LNG = Math.round((totalMGO * 0.1) / 100) * 100;
          }
          else if (index > 2) {
            interval.fuelValues.MGO = Math.round((totalMGO * 0.1) / 100) * 100;
            interval.fuelValues['Liquid Hydrogen'] = Math.round((totalMGO * 0.8) / 100) * 100;
            interval.fuelValues.LNG = Math.round((totalMGO * 0.1) / 100) * 100;
          }
        });
      }
      this.$emit("update:globalData", this.localData);
    },
    formatMJ(value) {
      if (value >= 1e9) {
        return (value / 1e9).toFixed(1) + 'e9 MJ';
      } else if (value >= 1e6) {
        return (value / 1e6).toFixed(1) + 'e6 MJ';
      } else if (value >= 1e3) {
        return (value / 1e3).toFixed(1) + 'e3 MJ';
      } else {
        return value.toFixed(2) + ' MJ';
      }
    }
  },
  mounted() {
      this.calculateTotals();
    }
};
</script>

<style scoped>
.container {
  max-width: 600px;
  margin: 0 auto;
}

.totals {
  margin-top: 20px;
  font-size: 1.2em;
}
</style>
