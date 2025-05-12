<template>
  <b-tabs v-if="scenarios.length > 1" v-model="activeTab" >
    <!-- one tab per scenario -->
    <b-tab
      v-for="(sc, idx) in scenarios"
      :key="sc.id"
      :title="sc.name"
      :active="idx === lastIndex"
    >
      <!-- Editable only on the newest scenario -->
      <FuelCapacityEditor
        v-if="idx === lastIndex"
        v-model:capacitySelection="sc.data.fuelCapacitySelection"
        :disabled="!sc.editable"
        @update:capacitySelection="val => pushUpdate(idx,val)"
      />
      <FuelCapacityEditor
        v-else
        :capacitySelection="sc.data.fuelCapacitySelection"
        :disabled="true"
      />
    </b-tab>
  </b-tabs>
  <!-- Single scenario, no tabs -->
  <FuelCapacityEditor
    v-else
    v-model:capacitySelection="localScenarios[0].data.fuelCapacitySelection"
    :disabled="!scenarios[0].editable"
    @update:capacitySelection="val => pushUpdate(0,val)"
  />
    <!-- <div class="global-data-display">
      <h3>Global Data</h3>
      <pre>{{ JSON.stringify(scenarios, null, 2) }}</pre>
    </div> -->
</template>

<script>
import cloneDeep from 'lodash.clonedeep'
import FuelCapacityEditor from './FuelCapacityEditor.vue'

export default {
  name: 'FuelCapacitySelection',
  components: { FuelCapacityEditor },
  props: {scenarios: Array},
  emits: ['update-scenario'],

  data() {
    return {
      localScenarios: cloneDeep(this.scenarios),
      activeTab: this.scenarios.length - 1
    };
  },
  computed: {
    lastIndex() { return this.scenarios.length - 1; }
  },
  watch: {
    scenarios: {
      handler(newVal) { this.localScenarios = cloneDeep(newVal) },
      deep: true
    }
  },
  methods: {
    /* propagate edits from child -> parent */
    pushUpdate(idx, value) {
      this.$emit('update-scenario', { index: idx, value })
    }
  }
  // mounted() {
  //   /* Seed the newest scenario if it's still empty */
  //   const newest = this.scenarios[this.lastIndex]
  //   if (newest.id !== 1 && newest.editable) {
  //     const fresh = newest.data.fuelCapacitySelection.fuels.every(f =>
  //       f.rows.length === 0 || f.rows.every(r => r.capacity === 0)
  //     )
  //     if (fresh) {
  //       newest.data.fuelCapacitySelection =
  //         cloneDeep(this.scenarios[0].data.fuelCapacitySelection)
  //     }
  //   }
  // }
}
</script>