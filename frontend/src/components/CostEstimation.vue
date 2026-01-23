<template>
    <div class="container mt-4">
      <h3>Cost Estimation</h3>
      <p>Review and adjust cost estimates for each port and fuel type:</p>
  
      <b-accordion id="cost-estimation-accordion" flush>
        <b-accordion-item
          v-for="(port, portIndex) in localPorts"
          :key="portIndex"
          :visible="portIndex === 0"
          :title="port.name"
        >
          <div v-for="fuel in selectedFuels(port.fuelSelections)" :key="fuel">
            <h5>{{ getFuelDisplayName(fuel) }}</h5>
            <table class="table">
              <thead>
                <tr>
                  <th>Capacity</th>
                  <th>Storage Tank (tonnes)</th>
                  <th>Installation Cost (USD)</th>
                  <th>Maintenance Cost per Year (USD)</th>
                  <th>Decommissioning Cost (USD)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="capacity in port.capacities[fuel]" :key="capacity">
                  <td>{{ capacity }}</td>
                  <td>
                    <!-- Display the computed Storage Tank value with tooltip -->
                    <span
                      data-bs-toggle="tooltip"
                      data-bs-html="true"
                      :data-bs-title="port.costEstimates[fuel][capacity].storageTankDetails"
                      class="storage-tank-value"
                    >
                      {{ formatNumber(port.costEstimates[fuel][capacity].storageTank) }}
                    </span>
                  </td>
                  <td>
                    <!-- Display the computed Installation Cost with tooltip -->
                    <input
                      type="number"
                      v-model.number="port.costEstimates[fuel][capacity].installationCost"
                      class="form-control"
                      :data-bs-toggle="'tooltip'"
                      data-bs-html="true"
                      :data-bs-title="port.costEstimates[fuel][capacity].installationCostDetails"
                    />
                  </td>
                  <td>
                    <!-- Maintenance Cost Tooltip -->
                    <input
                      type="number"
                      v-model.number="port.costEstimates[fuel][capacity].maintenanceCostPerYear"
                      class="form-control"
                      :data-bs-toggle="'tooltip'"
                      data-bs-html="true"
                      :data-bs-title="'~4% of ' + formatNumber(port.costEstimates[fuel][capacity].installationCost) + ' USD'"
                    />
                  </td>
                  <td>
                    <!-- Decommissioning Cost Tooltip -->
                    <input
                      type="number"
                      v-model.number="port.costEstimates[fuel][capacity].decommissioningCost"
                      class="form-control"
                      :data-bs-toggle="'tooltip'"
                      data-bs-html="true"
                      :data-bs-title="'~10% of ' + formatNumber(port.costEstimates[fuel][capacity].installationCost) + ' USD'"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </b-accordion-item>
      </b-accordion>
    <!-- For testing purposes: Display the updated ports data -->
    <pre class="mt-4">{{ localPorts }}</pre>

    </div>
  </template>
  
  <script>
  import * as bootstrap from 'bootstrap';
  
  export default {
    name: 'CostEstimation',
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
    created() {
      this.initializeCostEstimates();
    },
    mounted() {
      this.initializeTooltips();
    },
    methods: {
      initializeCostEstimates() {
        const energyContents = {
          liquidHydrogen: 120,
          compressedHydrogen: 120,
          ammonia: 18.6,
          methanol: 19.9,
          lng: 50,
        };
        const fuelEnergyContentPerKg = 42.8; // MJ/kg
  
        // Costs and densities
        const storageCostPerKgLH2 = 50; // USD/kg for Liquefied Hydrogen storage
        const liquefactionCostPerKgLH2 = 1.2; // USD/kg for liquefaction
  
        const densities = {
          compressedHydrogen: 70.8, // kg/m3
          ammonia: 682,
          methanol: 792,
          lng: 450,
        };
  
        const unitInstallationCosts = {
          compressedHydrogen: 600, // USD/m3
          ammonia: 2000,
          methanol: 1000,
          lng: 2000,
        };
  
        this.localPorts.forEach((port) => {
          if (!port.costEstimates) {
            port.costEstimates = {};
          }
          const selectedFuels = this.selectedFuels(port.fuelSelections || {});
          selectedFuels.forEach((fuel) => {
            if (!port.costEstimates[fuel]) {
              port.costEstimates[fuel] = {};
            }
            if (!port.capacities || !port.capacities[fuel]) {
              // Initialize capacities if not defined
              port.capacities = port.capacities || {};
              port.capacities[fuel] = []; // Initialize as an empty array
            }
            port.capacities[fuel].forEach((capacity) => {
              // Parse the capacity percentage (e.g., '50%' => 50)
              const capacityPercentage = parseFloat(
                capacity.replace('%', '').trim()
              );
              // Compute desired capacity in tonnes
              const desiredCapacityTonnes =
                port.capacity * (capacityPercentage / 100);
              // Get the energy content of the fuel (MJ/kg)
              const fuelEnergyContent = energyContents[fuel];
              if (fuelEnergyContent) {
                // Compute Energy in MJ
                const energyMJ = desiredCapacityTonnes * fuelEnergyContentPerKg;
                // Compute Storage Tank volume in tonnes
                const storageTank = energyMJ / fuelEnergyContent;
                // Round up to the nearest hundreds
                const storageTankRounded = Math.ceil(storageTank / 100) * 100;
                // Prepare tooltip text with HTML formatting
                const storageTankDetails = `
                  <strong>Energy (MJ)</strong> = ${desiredCapacityTonnes.toFixed(
                    2
                  )} tonnes × ${fuelEnergyContentPerKg} MJ/kg = ${energyMJ.toFixed(
                  2
                )} MJ<br>
                  <strong>Capacity Tank (tonnes)</strong> = ${energyMJ.toFixed(
                    2
                  )} MJ ÷ ${fuelEnergyContent} MJ/kg = ${storageTank.toFixed(
                  2
                )} tonnes<br>
                  <strong>Rounding</strong>: Rounded up to the nearest hundred: ${storageTankRounded} tonnes
                `;
  
                // Initialize cost estimates
                const costEstimate = {
                  storageTank: storageTankRounded,
                  storageTankDetails: storageTankDetails.trim(),
                  installationCost: 0,
                  maintenanceCostPerYear: 0,
                  decommissioningCost: 0,
                  installationCostDetails: '',
                };
  
                if (fuel === 'liquidHydrogen') {
                  // Compute Storage Cost and Liquefaction Cost
                  const storageCost =
                    storageTankRounded * 1000 * storageCostPerKgLH2; // Convert tonnes to kg
                  const liquefactionCost =
                    storageTankRounded * 1000 * liquefactionCostPerKgLH2; // Convert tonnes to kg
                  const installationCost = storageCost + liquefactionCost;
                  // Round up to thousands
                  const installationCostRounded =
                    Math.ceil(installationCost / 1000) * 1000;
                  // Compute Maintenance and Decommissioning Costs
                  const maintenanceCost =
                    Math.ceil((installationCostRounded * 0.04) / 1000) * 1000;
                  const decommissioningCost =
                    Math.ceil((installationCostRounded * 0.1) / 1000) * 1000;
                  // Prepare installation cost details
                  const installationCostDetails = `
                    <strong>Storage Cost</strong> = ${storageTankRounded} tonnes × 1000 kg/tonne × ${storageCostPerKgLH2} USD/kg = ${storageCost.toFixed(
                    2
                  )} USD<br>
                    <strong>Liquefaction Cost</strong> = ${storageTankRounded} tonnes × 1000 kg/tonne × ${liquefactionCostPerKgLH2} USD/kg = ${liquefactionCost.toFixed(
                    2
                  )} USD<br>
                    <strong>Installation Cost</strong> = Storage Cost + Liquefaction Cost = ${installationCost.toFixed(
                    2
                  )} USD<br>
                    <strong>Rounded Installation Cost</strong>: Rounded up to thousands: ${installationCostRounded} USD
                  `;
  
                  costEstimate.installationCost = installationCostRounded;
                  costEstimate.installationCostDetails =
                    installationCostDetails.trim();
                  costEstimate.maintenanceCostPerYear = maintenanceCost;
                  costEstimate.decommissioningCost = decommissioningCost;
                } else if (
                  ['compressedHydrogen', 'ammonia', 'methanol', 'lng'].includes(
                    fuel
                  )
                ) {
                  // Get density and unit installation cost
                  const density = densities[fuel]; // kg/m3
                  const unitInstallationCost = unitInstallationCosts[fuel]; // USD/m3
                  // Compute Volume in m3
                  const volumeM3 =
                    (storageTankRounded * 1000) / density; // Convert tonnes to kg
                  // Compute Installation Cost
                  const installationCost = volumeM3 * unitInstallationCost;
                  // Round up to thousands
                  const installationCostRounded =
                    Math.ceil(installationCost / 1000) * 1000;
                  // Compute Maintenance and Decommissioning Costs
                  const maintenanceCost =
                    Math.ceil((installationCostRounded * 0.04) / 1000) * 1000;
                  const decommissioningCost =
                    Math.ceil((installationCostRounded * 0.1) / 1000) * 1000;
                  // Prepare installation cost details
                  const installationCostDetails = `
                    <strong>Volume (m³)</strong> = ${storageTankRounded} tonnes × 1000 kg/tonne ÷ ${density} kg/m³ = ${volumeM3.toFixed(
                    2
                  )} m³<br>
                    <strong>Installation Cost</strong> = Volume × ${unitInstallationCost} USD/m³ = ${installationCost.toFixed(
                    2
                  )} USD<br>
                    <strong>Rounded Installation Cost</strong>: Rounded up to thousands: ${installationCostRounded} USD
                  `;
  
                  costEstimate.installationCost = installationCostRounded;
                  costEstimate.installationCostDetails =
                    installationCostDetails.trim();
                  costEstimate.maintenanceCostPerYear = maintenanceCost;
                  costEstimate.decommissioningCost = decommissioningCost;
                } else {
                  // Other fuels
                  costEstimate.installationCost = 0;
                  costEstimate.installationCostDetails =
                    'Installation cost calculation not defined for this fuel.';
                  costEstimate.maintenanceCostPerYear = 0;
                  costEstimate.decommissioningCost = 0;
                }
  
                port.costEstimates[fuel][capacity] = costEstimate;
              } else {
                // If fuel energy content is not defined, set storageTank to 0
                port.costEstimates[fuel][capacity] = {
                  storageTank: 0,
                  storageTankDetails: 'Fuel energy content not defined.',
                  installationCost: 0,
                  installationCostDetails: 'Installation cost calculation not defined.',
                  maintenanceCostPerYear: 0,
                  decommissioningCost: 0,
                };
              }
            });
          });
        });
      },
      initializeTooltips() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(
          this.$el.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
          new bootstrap.Tooltip(tooltipTriggerEl);
        });
      },
      selectedFuels(fuelSelections) {
        return Object.keys(fuelSelections || {}).filter(
          (fuel) => fuelSelections[fuel]
        );
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
      formatNumber(value) {
        return new Intl.NumberFormat('en-US', { style: 'decimal' }).format(value);
      },
    },
    watch: {
      ports: {
        handler() {
          this.localPorts = JSON.parse(JSON.stringify(this.ports));
          this.initializeCostEstimates();
          // Re-initialize tooltips after DOM update
          this.$nextTick(() => {
            this.initializeTooltips();
          });
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
  
  h5 {
    margin-top: 20px;
    margin-bottom: 10px;
  }
  
  .storage-tank-value {
    font-weight: bold;
    cursor: help;
  }
  </style>
  