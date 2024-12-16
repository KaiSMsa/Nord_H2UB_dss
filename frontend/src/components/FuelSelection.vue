<template>
  <div class="container">
    <h3>Fuel selection</h3>
    <p>Select possible fuel alternatives for each port:</p>

    <b-table :items="localPorts" :fields="fields" responsive="sm" striped hover>
      <!-- Port Name Column -->
      <template #cell(name)="row">
        {{ row.item.name }}
      </template>

      <!-- Energy Type Column -->
      <template #cell(energyType)="row">
        {{ getEnergyTypeText(row.item.energyType) }}
      </template>

      <!-- Liquid Hydrogen Switch -->
      <template #cell(liquidHydrogen)="row">
        <div class="form-group">
          <label class="switch">
            <input type="checkbox" v-model="row.item.fuelSelections.liquidHydrogen" />
            <span class="slider round"></span>
          </label>
        </div>
      </template>

      <!-- Compressed Hydrogen Switch -->
      <template #cell(compressedHydrogen)="row">
        <div class="form-group">
          <label class="switch">
            <input type="checkbox" v-model="row.item.fuelSelections.compressedHydrogen" />
            <span class="slider round"></span>
          </label>
        </div>
      </template>

      <!-- Ammonia Switch -->
      <template #cell(ammonia)="row">
        <div class="form-group">
          <label class="switch">
            <input type="checkbox" v-model="row.item.fuelSelections.ammonia" />
            <span class="slider round"></span>
          </label>
        </div>
      </template>

      <!-- Methanol Switch -->
      <template #cell(methanol)="row">
        <div class="form-group">
          <label class="switch">
            <input type="checkbox" v-model="row.item.fuelSelections.methanol" />
            <span class="slider round"></span>
          </label>
        </div>
      </template>

      <!-- LNG Switch -->
      <template #cell(lng)="row">
        <div class="form-group">
          <label class="switch">
            <input type="checkbox" v-model="row.item.fuelSelections.lng" />
            <span class="slider round"></span>
          </label>
        </div>
      </template>
    </b-table>
  </div>
</template>

<script>
export default {
  name: 'FuelSelection',
  props: {
    ports: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      // Create a local copy of the ports data
      localPorts: JSON.parse(JSON.stringify(this.ports)),
      // Table fields
      fields: [
        { key: 'name', label: 'Port Name' },
        { key: 'energyType', label: 'Energy Type' },
        { key: 'liquidHydrogen', label: 'Liquid Hydrogen' },
        { key: 'compressedHydrogen', label: 'Compressed Hydrogen' },
        { key: 'ammonia', label: 'Ammonia' },
        { key: 'methanol', label: 'Methanol' },
        { key: 'lng', label: 'LNG' }
      ],
      // Energy types with their meanings
      energyTypes: [
        { value: 'MGO', text: 'MGO (Marine Gas Oil)' },
        { value: 'MDO', text: 'MDO (Marine Diesel Oil)' },
        { value: 'IFO', text: 'IFO (Intermediate Fuel Oil)' },
        { value: 'VLSFO', text: 'VLSFO (Very Low Sulphur Fuel Oil)' },
        { value: 'HFO', text: 'HFO (Heavy Fuel Oil)' }
      ]
    };
  },
  watch: {
    // Watch for changes in localPorts and emit updates to the parent
    localPorts: {
      handler(newVal) {
        this.$emit('update:ports', newVal);
      },
      deep: true
    }/*,
    // Watch for changes in the parent ports prop to update localPorts
    ports: {
      handler(newVal) {
        this.localPorts = JSON.parse(JSON.stringify(newVal));
      },
      deep: true
    }*/
  },
  methods: {
    getEnergyTypeText(energyValue) {
      const energy = this.energyTypes.find(e => e.value === energyValue);
      return energy ? energy.text : energyValue;
    }
  }
};
</script>

<style scoped>
.b-table {
  margin-bottom: 20px;
}
.b-form-invalid-feedback {
  display: block;
  color: #dc3545;
}
.is-invalid {
  border-color: #dc3545 !important;
  border-radius: 0.25rem;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

/* Slider */
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .2s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .2s;
}

input:checked + .slider {
  background-color: var(--bs-primary);
}

input:focus + .slider {
  box-shadow: 0 0 1px #28a745;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

/* Rounded Slider */
.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}
</style>
