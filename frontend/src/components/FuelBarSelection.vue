<template>
  <!-- Tabbed view (≥2 scenarios) -->
  <b-tabs v-if="localScenarios.length > 1" v-model="activeTab" content-class="mt-3" >
    <b-tab
      v-for="(sc, idx) in localScenarios"
      :key="sc.id"
      :title="sc.name"
      :active="idx === lastIndex"
    >
      <!-- newest scenario = editable -->
      <FuelBarEditor
        v-if="idx === lastIndex"
        v-model:fuelSelection="sc.data.fuelBarSelection"
        @update:fuelSelection="v => pushUpdate(idx, v)"
        :disabled="!sc.editable"
      />
      <!-- earlier scenarios = read-only -->
      <FuelBarEditor
        v-else
        :fuelSelection="sc.data.fuelBarSelection"
        :disabled="true"
      />
    </b-tab>
  </b-tabs>
  
  <!-- ─────────────── Single-scenario view ─────────────── -->
  <div v-else class="tab-content mt-3">
    <!-- replicate <b-tab>’s inner .tab-pane so the same CSS applies -->
    <div class="tab-pane fade show active">
      <FuelBarEditor
        v-model:fuelSelection="localScenarios[0].data.fuelBarSelection"
        @update:fuelSelection="v => pushUpdate(0, v)"
        :disabled="!localScenarios[0].editable"
      />
    </div>
  </div>
      <!-- <div class="global-data-display">
      <h3>Global Data</h3>
      <pre>{{ JSON.stringify(scenarios, null, 2) }}</pre>
    </div> -->
</template>

<script>
import cloneDeep from 'lodash.clonedeep'
import FuelBarEditor from './FuelBarEditor.vue'

export default {
  name: 'FuelBarSelection',
  components: { FuelBarEditor },

  props: {
    /* full list of scenarios from MainDashboard */
    scenarios: { type: Array, required: true }
  },
  emits: ['update-scenario'],
  data() {
    return {
      /* local copy of scenarios to avoid mutating the original */
      localScenarios: cloneDeep(this.scenarios),
      activeTab: this.scenarios.length - 1
    }
  },
  computed: {
    lastIndex() { return this.scenarios.length - 1 }
  },
  watch: {
    scenarios: {
      handler(newVal) {
        this.localScenarios = cloneDeep(newVal);
        // this.activeTab = newVal.length - 1; // Set the active tab to the last scenario
      },
      deep: true
    }
  },
  methods: {
    pushUpdate(idx, val) {
      // this.localScenarios[idx].data.fuelBarSelection = val
      // this.$emit('update-scenario', this.localScenarios)
      this.$emit('update-scenario', { index: idx, value: val })
    }
  },
}
</script>
