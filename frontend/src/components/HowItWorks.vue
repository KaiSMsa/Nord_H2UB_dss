<template>
    <section class="howitworks-container">
      <!-- Brief description about the tool -->
      <div class="intro-text">
        <p>
          GREENPORT helps you optimize your port’s fuel capacity and
          invest in the most viable future fuels. Follow the steps below to set your
          capacity, choose fuels, adjust tank sizes, and generate an optimal strategy.
        </p>
      </div>
  
      <div class="steps-grid">
        <!-- Step 1 (Top Left) -->
        <div class="step-box">
          <div class="step-icon">
            <img src="@/assets/tank_capacity.svg" alt="Tank Capacity" />
          </div>
          <div class="step-header">Step 1: Set the fuel port capacity</div>
          <p>Define your available port capacity to serve as the basis for planning.</p>
        </div>
  
        <!-- Step 2 (Top Right) -->
        <div class="step-box">
          <div class="step-icon">
            <img src="@/assets/green tank.svg" alt="Green Tank" />
          </div>
          <div class="step-header">Step 2: Invest on which fuels to offer in the future</div>
          <p>Decide which fuels to invest in based on future demand and sustainability.</p>
        </div>
  
        <!-- Step 3 (Bottom Left) -->
        <div class="step-box">
          <div class="step-icon">
            <img src="@/assets/costs.svg" alt="Costs" />
          </div>
          <div class="step-header">Step 3: Adjust the possible tank sizes</div>
          <p>Customize tank sizes to fit the fuel volumes and operational needs.</p>
        </div>
  
        <!-- Step 4 (Bottom Right) -->
        <div class="step-box">
          <div class="step-icon">
            <img src="@/assets/plan.svg" alt="Plan" />
          </div>
          <div class="step-header">Step 4: Generate the plan</div>
          <p>Run the planning algorithm to determine the optimal strategy.</p>
        </div>
      </div>
  
      <!-- Get started button below steps -->
      <div class="get-started-container">
        <button class="get-started-btn" @click="onGetStarted">Get started</button>
      </div>
    </section>
  </template>
  
  <script>
  export default {
    name: 'HowItWorks',
    methods: {
      onGetStarted() {
        // Emit an event so the parent can switch to the main dashboard
        this.$emit('started');
      }
    }
  };
  </script>
  
  <style scoped>
  /* Container */
  body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    margin: 0;
    padding: 20px;
  }
  
  .howitworks-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
  }
  
  /* Intro text for the top description */
  .intro-text {
    margin-bottom: 30px;
    text-align: center;
    color: #555;
    font-size: 1.1rem;
    line-height: 1.4;
  }
  
  /* 2x2 grid for steps */
  .steps-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-row-gap: 40px;
    grid-column-gap: 40px;
    margin-bottom: 30px;
  }
  
  .step-box {
    background: #fff;
    border-radius: 6px;
    padding: 20px;
    position: relative;
    text-align: center;
  }
  
  /* Step icon */
  .step-icon {
    width: 100px;
    height: 100px;
    margin: 0 auto 10px;
  }
  
  /* Step title */
  .step-header {
    font-size: 1.2em;
    margin-bottom: 10px;
    font-weight: bold;
    text-align: center;
  }
  
  .step-box p {
    margin: 0;
    color: #555;
    line-height: 1.5;
    text-align: center;
  }
  
  /* "Get started" button area */
  .get-started-container {
    text-align: center;
  }
  
  .get-started-btn {
    padding: 10px 20px;
    font-size: 1em;
    background-color: #007BFF;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .get-started-btn:hover {
    background-color: #0056b3;
  }
  </style>
  