<template>
  <div class="container">
    <h3>Enter the port fuel capacity</h3>

    <!-- Form with inputs for each fuel type, labels and inputs aligned horizontally -->
    <b-form>
      <!-- MGO Input -->
      <b-form-group label="Marine Gas Oil (MGO) [tonnes]" label-for="mgo-input" label-cols="6" label-align="left">
        <b-form-input id="mgo-input" type="number" v-model.number="fuelAmounts.MGO" :min="0"
          @input="calculateTotals"></b-form-input>
      </b-form-group>

      <!-- MDO Input -->
      <b-form-group label="Marine Diesel Oil (MDO) [tonnes]" label-for="mdo-input" label-cols="6" label-align="left">
        <b-form-input id="mdo-input" type="number" v-model.number="fuelAmounts.MDO" :min="0"
          @input="calculateTotals"></b-form-input>
      </b-form-group>

      <!-- IFO Input -->
      <b-form-group label="Intermediate Fuel Oil (IFO) [tonnes]" label-for="ifo-input" label-cols="6"
        label-align="left">
        <b-form-input id="ifo-input" type="number" v-model.number="fuelAmounts.IFO" :min="0"
          @input="calculateTotals"></b-form-input>
      </b-form-group>

      <!-- VLSFO Input -->
      <b-form-group label="Very Low Sulphur Fuel Oil (VLSFO) [tonnes]" label-for="vlsfo-input" label-cols="6"
        label-align="left">
        <b-form-input id="vlsfo-input" type="number" v-model.number="fuelAmounts.VLSFO" :min="0"
          @input="calculateTotals"></b-form-input>
      </b-form-group>

      <!-- HFO Input -->
      <b-form-group label="Heavy Fuel Oil (HFO) [tonnes]" label-for="hfo-input" label-cols="6" label-align="left">
        <b-form-input id="hfo-input" type="number" v-model.number="fuelAmounts.HFO" :min="0"
          @input="calculateTotals"></b-form-input>
      </b-form-group>
    </b-form>

    <!-- Display total amounts -->
    <div class="totals">
      <p><strong>Total amount in MGO-equivalent:</strong> {{ totalMGOEquivalent }} tonnes</p>
      <p><strong>Total amount in MJ:</strong> {{ formatMJ(totalMJ) }}</p>
    </div>
  </div>
  <!-- <pre class="mt-4">{{ globalData }}</pre> -->
</template>

<script>
export default {
  name: 'PortFuelCapacity',
  props: ['globalData'],
  data() {
    return {
      localData: JSON.parse(JSON.stringify(this.globalData)),
      fuelAmounts: {
        MGO: 0,
        MDO: 0,
        IFO: 0,
        VLSFO: 0,
        HFO: 0,
      },
      totalMGOEquivalent: 0,
      totalMJ: 0,
      // Conversion factors to MGO-equivalent and MJ per tonne
      conversionFactors: {
        MGO: { mgoEquivalent: 1.0, mjPerTon: 42900 }, // Assuming MGO is the base
        MDO: { mgoEquivalent: 0.98, mjPerTon: 42700 },
        IFO: { mgoEquivalent: 0.95, mjPerTon: 42400 },
        VLSFO: { mgoEquivalent: 0.97, mjPerTon: 42600 },
        HFO: { mgoEquivalent: 0.93, mjPerTon: 42200 },
      },
    };
  },
  watch: {
    // Watch for changes in localPorts and emit updates to the parent
    localData: {
      handler(newVal) {
        this.$emit('update:globalData', newVal);
      },
      deep: true
    }
  },
  methods: {
    calculateTotals() {
      let totalMGO = 0;
      let totalMJ = 0;
      for (const fuel in this.fuelAmounts) {
        const amount = this.fuelAmounts[fuel] || 0;
        const factors = this.conversionFactors[fuel];
        totalMGO += amount * factors.mgoEquivalent;
        totalMJ += amount * factors.mjPerTon;
      }
      this.totalMGOEquivalent = Math.round(totalMGO); // Round to integer
      this.totalMJ = totalMJ;
      this.localData.portFuelInformation.totalMGOEquivalent = this.totalMGOEquivalent;
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
    },
  },
  mounted() {
    this.calculateTotals();
  },
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
