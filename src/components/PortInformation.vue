<template>
  <div class="container">
    <h3>Port Information</h3>

    <b-table :items="localPorts" :fields="fields" responsive="sm" striped hover>
      <!-- First column: Remove button -->
      <template #cell(remove)="row">
        <div v-if="row.item.showConfirmRemove">
          <!-- Validation buttons when delete action is triggered -->
          <b-button size="sm" variant="success" @click="confirmRemove(row.index)">
            <img src="@/assets/check.png" alt="Confirm" width="20">
          </b-button>
          <b-button size="sm" variant="danger" @click="cancelRemove(row.index)">
            <img src="@/assets/cancel.png" alt="Cancel" width="20">
          </b-button>
        </div>
        <div v-else>
          <!-- Remove button (-) with light grey color -->
          <b-button size="sm" variant="light" @click="triggerRemove(row.index)">
            <img src="@/assets/remove.png" alt="Remove" width="30">
          </b-button>
        </div>
      </template>

      <!-- Second column: Editable port name with validation -->
      <template #cell(name)="row">
        <b-form-input
          v-model="row.item.name"
          :state="!row.item.hasError"
          @input="validatePortName()"
        ></b-form-input>
        <b-form-invalid-feedback v-if="row.item.hasError">
          Port name must be unique and non-empty.
        </b-form-invalid-feedback>
      </template>

      <!-- Third column: Custom dropdown for energy type with light grey color -->
      <template #cell(energyType)="row">
        <div>
          <b-dropdown
            :text="getDropdownText(row.item.energyType)"
            variant="light"
            class="mb-2"
            :class="{ 'is-invalid': row.item.hasEnergyError }"
            @click="row.item.hasEnergyError = false"
          >
            <b-dropdown-item-button
              v-for="(energy, index) in energyTypes"
              :key="index"
              @click="selectEnergyType(row.index, energy.value)"
            >
              <span v-html="energy.text"></span>
            </b-dropdown-item-button>
          </b-dropdown>
          <b-form-invalid-feedback v-if="row.item.hasEnergyError">
            Select an energy type.
          </b-form-invalid-feedback>
        </div>
      </template>

      <!-- Fourth column: Editable port capacity -->
      <template #cell(capacity)="row">
        <b-form-input
          type="number"
          v-model="row.item.capacity"
          :state="!row.item.hasCapacityError"
          @input="validatePortCapacity(row.index)"
        ></b-form-input>
        <b-form-invalid-feedback v-if="row.item.hasCapacityError">
          Capacity must be greater than 0.
        </b-form-invalid-feedback>
      </template>

      <!-- Fifth column: Refueling capacity (calculated) -->
      <template #cell(refuelingCapacity)="row">
        {{ calculateRefuelingCapacity(row.item.energyType, row.item.capacity) }} MW
      </template>
    </b-table>

    <!-- Add Row Button -->
    <b-button variant="primary" @click="addRow">Add New Port</b-button>
  </div>
</template>

<script>
export default {
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
        { key: 'remove', label: '', class: 'text-center' },
        { key: 'name', label: 'Port Name' },
        { key: 'energyType', label: 'Energy Type' },
        { key: 'capacity', label: 'Port Capacity (tons)' },
        { key: 'refuelingCapacity', label: 'Refueling Capacity (MW)' }
      ],
      // Energy types with their meanings
      energyTypes: [
        { value: 'MGO', text: '<b>MGO</b> (Marine Gas Oil)' },
        { value: 'MDO', text: '<b>MDO</b> (Marine Diesel Oil)' },
        { value: 'IFO', text: '<b>IFO</b> (Intermediate Fuel Oil)' },
        { value: 'VLSFO', text: '<b>VLSFO</b> (Very Low Sulphur Fuel Oil)' },
        { value: 'HFO', text: '<b>HFO</b> (Heavy Fuel Oil)' }
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
    // Trigger remove action (show validation buttons)
    triggerRemove(index) {
      this.localPorts[index].showConfirmRemove = true;
    },
    // Confirm row removal
    confirmRemove(index) {
      this.localPorts.splice(index, 1);
    },
    // Cancel remove action
    cancelRemove(index) {
      this.localPorts[index].showConfirmRemove = false;
    },
    // Add a new row with default values, if there are no validation issues
    addRow() {
      // Check if there are any invalid port names before adding a new row
      const invalidPorts = this.localPorts.some((port) => {
        return port.hasError || port.name.trim() === '' || port.energyType === '' || port.capacity <= 0;
      });

      // If there's an invalid port, do not add a new row and trigger validation
      if (invalidPorts) {
        this.localPorts.forEach((port, index) => {
          this.validatePortName(index);
          this.validateEnergyType(index);
          this.validatePortCapacity(index);
        });
        return;
      }

      // Add the new row if all current port names are valid
      this.localPorts.push({
        name: 'Port',
        energyType: 'MGO',
        capacity: 5000,
        fuelSelections: {
            liquidHydrogen: false,
            compressedHydrogen: false,
            ammonia: false,
            methanol: false,
            lng: false
        },
        capacities: {
            liquidHydrogen: ['20%', '50%', '100%'],
            compressedHydrogen: ['20%', '50%', '100%'],
            ammonia: ['20%', '50%', '100%'],
            methanol: ['20%', '50%', '100%'],
            lng: ['20%', '50%', '100%']
        }        
       });
    },
    // Select energy type for a specific row
    selectEnergyType(rowIndex, value) {
      this.localPorts[rowIndex].energyType = value;
      this.localPorts[rowIndex].hasEnergyError = false;
    },
    // Validate that the port name is unique while typing
    // validatePortName(index) {
    //   const currentName = this.ports[index].name.trim();
    //   // Check if the name is empty or if it already exists in other rows
    //   const duplicate = this.ports.some(
    //     (port, i) => i !== index && port.name.trim().toLowerCase() === currentName.toLowerCase()
    //   );
    //   this.ports[index].hasError = duplicate || !currentName;
    // },
    validatePortName() {
      // Get a list of all port names, converted to lowercase and trimmed
      const allNames = this.localPorts.map(port => port.name.trim().toLowerCase());

      // Loop through each port and update `hasError` flag accordingly
      this.localPorts.forEach((port, index) => {
        const currentName = port.name.trim().toLowerCase();
        
        // Count the occurrences of the current name in allNames
        const duplicateCount = allNames.filter(name => name === currentName).length;

        // Set `hasError` to true if:
        // 1. The name is empty, OR
        // 2. The name appears more than once (indicating it's a duplicate)
        if (currentName === '' || duplicateCount > 1) {
          this.localPorts[index].hasError = true;
        } else {
          this.localPorts[index].hasError = false;
        }
      });
    },
    // Validate that the energy type is selected
    validateEnergyType(index) {
      const energyType = this.localPorts[index].energyType;
      this.localPorts[index].hasEnergyError = (energyType === '');
    },

    // Validate that the port capacity is greater than 0
    validatePortCapacity(index) {
      const capacity = this.localPorts[index].capacity;
      this.localPorts[index].hasCapacityError = (capacity <= 0);
    },
    // Get the dropdown button text (show selected energy type or placeholder text)
    getDropdownText(energyType) {
      if (energyType) {
        const selectedEnergy = this.energyTypes.find(energy => energy.value === energyType);
        return selectedEnergy ? selectedEnergy.text.replace(/<\/?b>/g, '') : 'Select Energy Type';
      } else {
        return 'Select Energy Type';
      }
    },
    // Calculate refueling capacity based on energy type and capacity
    calculateRefuelingCapacity(energyType, capacity) {
      let factor;
      switch (energyType) {
        case 'MGO':
        case 'MDO':
          factor = 1.1;
          break;
        case 'IFO':
        case 'VLSFO':
          factor = 1.2;
          break;
        case 'HFO':
          factor = 1.3;
          break;
        default:
          return 0;
      }
      return (capacity * factor).toFixed(2);
    }
  }
};
</script>

<style scoped>
/* Optional: Style the table and buttons */
.b-table {
  margin-bottom: 20px;
}
.text-center {
  text-align: center;
}
/* Style for invalid form input */
.is-invalid {
  border-color: #dc3545 !important;
}
.b-form-invalid-feedback {
  display: block;
  color: #dc3545;
}
/* Custom styling to show red border when dropdown is invalid */
.is-invalid {
  border: 1px solid #dc3545 !important; /* Red color to indicate invalid input */
  border-radius: 0.25rem; /* Same border-radius as other bootstrap form components */
}
</style>
