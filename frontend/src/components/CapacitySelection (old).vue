<template>
    <div class="container mt-4">
      <h3>Capacity Selection</h3>
      <p class="left-align">Please enter possible alternative fuel capacities for each port as percentages of their current capacities:</p>
      <ul class="left-align">
        <li>Select a port.</li>
        <li>Provide percentage values for each alternative fuel based on the current capacities of the port.</li>
        <li>You can enter many percentages, for example "20%", "50%" and "100%".</li>
      </ul>
  
      <b-accordion id="capacity-accordion" flush>
        <b-accordion-item
          v-for="(port, portIndex) in localPorts"
          :key="portIndex"
          
          :title="port.name"
        >
          <div
            v-for="fuel in selectedFuels(port.fuelSelections)"
            :key="fuel"
            class="mb-4"
          >
            <h5>{{ getFuelDisplayName(fuel) }}</h5>
  
            <!-- Form Tags for capacities -->
            <b-form-tags
              v-model="port.capacities[fuel]"
              separator=" ,;"
              placeholder="Enter capacities separated by space, comma, or semicolon"
              :tag-validator="capacityValidator"
              @input="onTagsInput(port, fuel)"
              add-on-blur
              add-on-enter
            ></b-form-tags>
          </div>
        </b-accordion-item>
      </b-accordion>
    </div>
  </template>
  
  <script>
  export default {
    name: 'CapacitySelection',
    props: {
      ports: {
        type: Array,
        required: true,
      },
    },
    data() {
      return {
        localPorts: JSON.parse(JSON.stringify(this.ports)), // Deep clone of ports
      };
    },
    methods: {
      selectedFuels(fuelSelections) {
        return Object.keys(fuelSelections).filter((fuel) => fuelSelections[fuel]);
      },
      getFuelDisplayName(fuelKey) {
        const fuelNames = {
          liquidHydrogen: 'Liquid Hydrogen',
          compressedHydrogen: 'Compressed Hydrogen',
          ammonia: 'Ammonia',
          methanol: 'Methanol',
          lng: 'LNG',
        };
        return fuelNames[fuelKey] || fuelKey;
      },
      capacityValidator(tag) {
        // Remove percent symbol if present
        let input = tag.trim();
        if (input.endsWith('%')) {
          input = input.slice(0, -1).trim();
        }
        const value = parseFloat(input);
        return !isNaN(value) && value >= 0 && value <= 200;
      },
      onTagsInput(port, fuel) {
        // Process capacities to ensure % is appended
        port.capacities[fuel] = port.capacities[fuel]
          .map((tag) => {
            let input = tag.trim();
            if (input.endsWith('%')) {
              input = input.slice(0, -1).trim();
            }
            const value = parseFloat(input);
            // Validate the value
            if (isNaN(value) || value < 0 || value > 200) {
              return null; // Invalid value
            }
            // Return the value as a string with percentage sign
            return String(value) + '%';
          })
          .filter((tag) => tag !== null);
  
        // Remove duplicates
        port.capacities[fuel] = [...new Set(port.capacities[fuel])];
  
        // Sort the capacities
        port.capacities[fuel].sort((a, b) => parseFloat(a) - parseFloat(b));
  
        // Emit the updated localPorts to the parent
        this.$emit('update:ports', JSON.parse(JSON.stringify(this.localPorts)));
      },
    },
    watch: {
      ports: {
        handler(newPorts) {
          // Update localPorts when the prop changes
          this.localPorts = JSON.parse(JSON.stringify(newPorts));
        },
        deep: true,
      },
    },
  };
  </script>
  
  <style scoped>
  .container {
    max-width: 800px;
  }
  
  .left-align {
    text-align: left;
  }

  h5 {
    margin-top: 20px;
    margin-bottom: 10px;
  }
  </style>
  