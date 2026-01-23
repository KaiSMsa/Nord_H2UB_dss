<template>
  <div class="stepper-container">
    <!-- Stepper Header -->
    <div class="stepper">
      <div v-for="(step, index) in steps" :key="index" class="step-container">
        <!-- Step Circle -->
        <div
          class="step"
          :class="{ active: currentStep === index, completed: index < currentStep }"
        >
          <span v-if="index >= currentStep">{{ index + 1 }}</span>
          <span v-else-if="currentStep > index" class="completed-tick">✔</span>
        </div>
        <!-- Step Label next to the step number -->
        <div class="step-label">{{ step.label }}</div>

        <!-- Line between steps (add line except after the last step) -->
        <div v-if="index < steps.length - 1" class="step-line"></div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="step-content">
      <div v-if="currentStep === 0">
        <!-- Step 1: Port Information -->
        <PortInformation v-model:ports="ports" />
      </div>
      <div v-if="currentStep === 1">
        <!-- Step 2 Content (Can be Facility.vue, for example) -->
         <FuelSelection v-model:ports="ports" />
        <!-- <h3>Step 2: Facility Information</h3>
        <p>This is where you can input facility information.</p> -->
      </div>
      <div v-if="currentStep === 2">
        <!-- Step 3: Capacity Selection -->
        <CapacitySelection v-model:ports="ports" />
      </div>
      <div v-if="currentStep === 3">
        <!-- Step 4: Cost estimation -->
        <CostEstimation v-model:ports="ports" />
      </div>
      <div v-if="currentStep === 4">
        <!-- Step 4: Review & Submit -->
        <h3>Step 4: Review & Submit</h3>
        <p>Review your information and submit the form.</p>
      </div>
    </div>

    <!-- Step Footer -->
    <div class="step-footer">
      <b-button v-if="currentStep > 0" @click="previousStep" variant="secondary">Previous</b-button>
      <b-button v-if="currentStep < steps.length - 1" @click="nextStep" variant="primary">Next</b-button>
      <b-button v-if="currentStep === steps.length - 1" @click="submit" variant="success">Submit</b-button>
    </div>
  </div>
</template>

<script>
import PortInformation from './PortInformation.vue';
import FuelSelection from './FuelSelection(old).vue';
import CapacitySelection from './CapacitySelection (old).vue';
import CostEstimation from '../components/CostEstimation.vue'

export default {
  name: 'MainDashboard',
  components: {
    PortInformation,
    FuelSelection,
    CapacitySelection,
    CostEstimation
  },
  data() {
    return {
      currentStep: 0,
      steps: [
        { label: 'Port Information' },
        { label: 'Fuel Selection' },
        { label: 'Capacity Selection' },
        { label: 'Cost Estimation' },
        { label: 'Review & Submit' }
      ],
      // Move the ports data here
      ports: [
        {
          name: 'Port A',
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
        },
        {
          name: 'Port B',
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
        }
      ]
    };
  },
  methods: {
    nextStep() {
      if (this.currentStep < this.steps.length - 1) {
        this.currentStep++;
      }
    },
    previousStep() {
      if (this.currentStep > 0) {
        this.currentStep--;
      }
    },
    submit() {
      alert('Form Submitted!');
    }
  }
};
</script>

<style scoped>
.stepper-container {
  margin: 2rem 0;
}

.stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.step-container {
  display: flex;
  align-items: center;
  position: relative;
  flex-grow: 1;
}

.step {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 2px solid #ccc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s, border-color 0.3s;
  flex-shrink: 0;
  background-color: #fff;
  z-index: 2;
}

.step.active {
  border-color: #007bff;
  background-color: #007bff;
  color: white;
}

.step.completed {
  border-color: #28a745;
}

.completed-tick {
  color: #28a745;
  font-size: 1.5rem;
  font-weight: bold;
}

.step-label {
  margin-left: 10px;
  font-size: 1rem;
  color: #555;
}

.step-line {
  flex-grow: 1;
  height: 4px;
  background-color: #ccc;
  z-index: 1;
}

.step-content {
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  background-color: #f9f9f9;
  margin-top: 2rem;
  min-height: 300px; /* Minimum height to add some space for content */
  display: flex; /* Enables flex layout for its children */
  flex-direction: column; /* Stacks children vertically */
  width: 100%; /* Ensures it takes full container width */
  box-sizing: border-box;
}

/* Inner Content: Expands to the full width of step-content */
.step-inner-content {
  flex-grow: 1;
  display: flex;
  width: 100%; /* Ensures it matches the width of step-content */
  box-sizing: border-box;
}

/* New CSS for step-footer */
.step-footer {
  display: flex;
  justify-content: space-between; /* Buttons on opposite sides */
  align-items: center;
  margin-top: 2rem;
  padding: 1rem 0;
}
</style>
