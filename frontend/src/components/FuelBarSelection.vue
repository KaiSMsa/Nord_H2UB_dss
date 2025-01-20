<template>
  <div class="container">
    <h3>Fuel Selection</h3>

    <!-- Container for bars and table using CSS grid -->
    <div class="bars-table-container">
      <!-- Bars Section -->
      <div class="bars-row">
        <!-- Invisible div to align with 'Fuel Type' column -->
        <div class="invisible-bar-space"></div>

        <div class="stacked-bar" v-for="interval in intervals" :key="interval.name"
          :style="{ height: getBarHeight(interval) + 'px' }">
          <!-- Top Handle -->
          <div v-if="hasTopHandle(interval)" class="drag-handle top-handle"
            @mousedown.stop="interval.name === '2025' ? null : startDragTopBar(interval, $event)"></div>

          <!-- Fuel Bars and Drag Handles -->
          <div v-for="(item, index) in getBarItems(interval)" :key="index"
            :class="item.type === 'bar' ? ['bar', item.fuel.class] : 'drag-handle'"
            :style="item.type === 'bar' ? { height: item.height + '%' } : null" @mousedown.stop="
              item.type === 'handle' && interval.name !== '2025'
                ? startDragHandle(interval, item.handleIndex, $event)
                : null
              ">
            <!-- If it's a bar, display the label -->
            <span v-if="item.type === 'bar'" class="bar-label-text">
              {{ item.fuel.name }}
              ({{ getFuelPercentage(interval, item.fuel).toFixed(1) }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- Table Section -->
      <div class="table-section">
        <table class="table">
          <thead>
            <tr>
              <th>Fuel Type</th>
              <th v-for="interval in intervals" :key="interval.name">
                {{ interval.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <!-- Fuel Rows -->
            <tr v-for="fuel in fuels" :key="fuel.name">
              <td>
                <span class="fuel-square" :class="fuel.class"></span>
                {{ fuel.name }}
              </td>
              <td v-for="interval in intervals" :key="interval.name + '-' + fuel.name">
                <input type="number" v-model.number="interval.fuelValues[fuel.name]"
                  :disabled="interval.name === '2025'" @input="onFuelInput(interval, fuel.name)" min="0" step="100" />
              </td>
            </tr>
            <!-- Total Amount Row -->
            <tr class="total-row">
              <td><strong>Total Amount (MGO-equivalent)</strong></td>
              <td v-for="interval in intervals" :key="'total-' + interval.name">
                <span>{{ interval.totalAmount.toLocaleString('en-US') }}</span>
              </td>
            </tr>
            <!-- CO₂ Equivalent Row -->
            <tr class="total-row">
              <td><strong>CO₂-equivalent (tonnes)</strong></td>
              <td v-for="interval in intervals" :key="'total-' + interval.name">
                <span>{{ calculateCO2Equivalent(interval).toLocaleString('en-US') }}</span>
              </td>
            </tr>
            <!-- Emission Reduction Row -->
            <tr class="total-row">
              <td><strong>CO₂-eq Reduction from 2025</strong></td>
              <td v-for="(interval, index) in intervals" :key="'change-' + interval.name">
                <!-- Skip the first interval as it's the baseline -->
                <span v-if="index === 0">-</span>
                <span v-else>
                  <span :class="{ 'text-danger': calculateCO2Reduction(interval) > 0, 'text-success': calculateCO2Reduction(interval) < 0 }">
                    {{ Math.abs(calculateCO2Reduction(interval)) }}%
                    <i
                      :class="calculateCO2Reduction(interval) > 0 ? 'bi bi-arrow-up' : 'bi bi-arrow-down'"
                      :style="{color: calculateCO2Reduction(interval) > 0 ? 'red': 'green', marginLeft: '5px'}">
                    </i>
                  </span>
                </span>
              </td>
            </tr>            
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <!-- <pre class="mt-4">{{ localData.fuelBarSelection }}</pre> -->
</template>

<script>
export default {
  name: 'FuelBarSelection',
  props: ['globalData'],
  data() {
    return {
      localData: JSON.parse(JSON.stringify(this.globalData)),
      maxBarHeight: 600, // Maximum height for the bar representing 100%
      stepSize: 100, // Step size for inputs
      MAX_FACTOR: 3,
      fuels: [
        { name: 'MGO', class: 'mgo-bar' },
        { name: 'Liquid Hydrogen', class: 'lh2-bar' },
        { name: 'Compressed Hydrogen', class: 'ch2-bar' },
        { name: 'Ammonia', class: 'ammonia-bar' },
        { name: 'Methanol', class: 'methanol-bar' },
        { name: 'LNG', class: 'lng-bar' },
      ],
      emissionFactors: {
        MGO: 3.17,               // CO2-eq per tonne for Marine Gas Oil
        'Liquid Hydrogen': 0, // Example value
        'Compressed Hydrogen': 0,
        Ammonia: 0,
        Methanol: 1.37,
        LNG: 2.75,
      },
      dragging: false,
      dragInfo: {
        interval: null,
        handleIndex: null,
        initialMouseY: 0,
        initialFuelValues: {},
      },
    };
  },
  computed: {
    intervals() {
      return this.localData.fuelBarSelection.intervals;
    },
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
    hasTopHandle(interval) {
      return this.getFuelsForInterval(interval).length > 0;
    },
    getBarItems(interval) {
      const fuelsForInterval = this.getFuelsForInterval(interval);
      const items = [];

      fuelsForInterval.forEach((fuel, index) => {
        // Add the bar item
        items.push({
          type: 'bar',
          fuel: fuel,
          height: this.getFuelHeight(interval, fuel),
        });

        // If not the last fuel, add a handle after the bar
        if (index < fuelsForInterval.length - 1) {
          items.push({
            type: 'handle',
            handleIndex: index,
          });
        }
      });

      return items;
    },
    startDragHandle(interval, handleIndex, event) {
      this.dragging = true;
      this.dragInfo.interval = interval;
      this.dragInfo.handleIndex = handleIndex;
      this.dragInfo.initialMouseY = event.clientY;

      // Save initial fuel values
      this.dragInfo.initialFuelValues = { ...interval.fuelValues };

      // Add event listeners
      window.addEventListener('mousemove', this.onDragHandle);
      window.addEventListener('mouseup', this.stopDragHandle);
    },
    onDragHandle(event) {
      if (this.localData.isStep1Initial) {
        this.localData.isStep1Initial = false; // Prevent Step 1 from recalculating in the future
      }
      if (!this.dragging) return;

      const deltaY = event.clientY - this.dragInfo.initialMouseY;
      const containerHeight = this.getBarHeight(this.dragInfo.interval);
      if (containerHeight === 0) return;

      const fuelsForInterval = this.getFuelsForInterval(this.dragInfo.interval);
      if (this.dragInfo.handleIndex >= fuelsForInterval.length - 1) {
        console.warn("Handle index is out of bounds. Stopping drag.");
        this.stopDragHandle();
        return;
      }

      const fuelAbove = fuelsForInterval[this.dragInfo.handleIndex];
      const fuelBelow = fuelsForInterval[this.dragInfo.handleIndex + 1];

      if (!fuelAbove || !fuelBelow) {
        console.warn("Fuel reference is undefined. Stopping drag.");
        this.stopDragHandle();
        return;
      }

      const fuelAboveHeight = this.getFuelBarHeight(this.dragInfo.interval, fuelAbove);
      const fuelBelowHeight = this.getFuelBarHeight(this.dragInfo.interval, fuelBelow);
      const combinedBarHeight = fuelAboveHeight + fuelBelowHeight;

      if (combinedBarHeight === 0) return;

      const percentageChange = (deltaY / combinedBarHeight) * 100;

      const initialAmountAbove = this.dragInfo.initialFuelValues[fuelAbove.name];
      const initialAmountBelow = this.dragInfo.initialFuelValues[fuelBelow.name];
      const totalFuelAmount = initialAmountAbove + initialAmountBelow;

      const amountChange = (percentageChange / 100) * totalFuelAmount;

      let newAmountAbove = initialAmountAbove + amountChange;
      let newAmountBelow = initialAmountBelow - amountChange;

      // Ensure amounts are within bounds
      if (newAmountAbove < this.stepSize || newAmountBelow < this.stepSize) {
        return;
      }

      // Round amounts to the nearest step
      newAmountAbove = this.roundToStep(newAmountAbove, this.stepSize);
      newAmountBelow = this.roundToStep(newAmountBelow, this.stepSize);

      // Update fuel values
      this.dragInfo.interval.fuelValues[fuelAbove.name] = newAmountAbove;
      this.dragInfo.interval.fuelValues[fuelBelow.name] = newAmountBelow;

      //this.dragInfo.interval.totalAmount = Object.values(this.dragInfo.interval.fuelValues)
      //  .reduce((sum, val) => sum + val, 0);

      // Now clamp if needed
      this.checkAndClampInterval(this.dragInfo.interval);
    },
    startDragTopBar(interval, event) {
      this.dragging = true;
      this.dragInfo.interval = interval;
      this.dragInfo.initialMouseY = event.clientY;

      // Identify the top fuel
      const fuelsForInterval = this.getFuelsForInterval(interval);
      this.dragInfo.topFuel = fuelsForInterval[0];
      if (!this.dragInfo.topFuel) {
        // No top fuel to resize
        return;
      }

      // Capture the initial top-fuel value and *all* initial fuel values
      this.dragInfo.initialFuelValue = interval.fuelValues[this.dragInfo.topFuel.name];
      this.dragInfo.initialFuelValues = { ...interval.fuelValues };

      // Capture the initial container (entire bar) height
      this.dragInfo.initialContainerHeight = this.getBarHeight(interval);

      // Change the mouse cursor
      document.body.style.cursor = 'ns-resize';

      // Add listeners for the drag
      window.addEventListener('mousemove', this.onDragTopBar);
      window.addEventListener('mouseup', this.stopDragHandle);
    },
    onDragTopBar(event) {
      if (this.localData.isStep1Initial) {
        this.localData.isStep1Initial = false; // Prevent Step 1 from recalculating in the future
      }

      if (!this.dragging) return;

      // Positive deltaY means user drags down, negative means drag up
      const deltaY = event.clientY - this.dragInfo.initialMouseY;
      const containerHeight = this.dragInfo.initialContainerHeight;
      if (containerHeight === 0) return;

      // Top fuel references
      const topFuel = this.dragInfo.topFuel;
      const initialTopFuelAmount = this.dragInfo.initialFuelValue;

      // Total “initial” fuel (when dragging started)
      const initialTotalFuel = Object.values(this.dragInfo.initialFuelValues)
        .reduce((sum, val) => sum + val, 0);

      // Convert pixel movement into a percentage of the *entire* bar
      const percentageChange = (deltaY / containerHeight) * 100;

      // Then figure out how many “fuel units” that percentage corresponds to.
      // The simplest approach is to scale by the entire interval’s initial total.
      // If you prefer the top bar to grow more slowly, scale by `initialTopFuelAmount`.
      const amountChange = (percentageChange / 100) * initialTotalFuel;

      // If dragging upward, deltaY is negative, so we *add* to the top bar:
      let newAmount = initialTopFuelAmount - amountChange;
      // (We subtract because if deltaY < 0, `- negative` is a plus.)

      // Enforce a floor (stepSize)
      if (newAmount < this.stepSize) {
        newAmount = this.stepSize;
      }
      // Round to the nearest step (100, etc.)
      newAmount = this.roundToStep(newAmount, this.stepSize);

      // Update that top fuel in the live interval
      this.dragInfo.interval.fuelValues[topFuel.name] = newAmount;

      // Recompute the interval’s total
      this.dragInfo.interval.totalAmount = Object.values(this.dragInfo.interval.fuelValues)
        .reduce((sum, val) => sum + val, 0);

      // Enforce the 300% cap
      this.checkAndClampInterval(this.dragInfo.interval);
    },
    stopDragHandle() {
      this.dragging = false;
      window.removeEventListener('mousemove', this.onDragHandle);
      window.removeEventListener('mousemove', this.onDragTopBar);
      window.removeEventListener('mouseup', this.stopDragHandle);

      // Reset the cursor back to default
      document.body.style.cursor = 'default';
    },
    roundToStep(value, step) {
      return Math.round(value / step) * step;
    },
    getFuelBarHeight(interval, fuel) {
      const totalBarHeight = this.getBarHeight(interval);
      const fuelHeightPercentage = this.getFuelHeight(interval, fuel);
      return (fuelHeightPercentage / 100) * totalBarHeight;
    },
    onFuelInput(interval, changedFuelName) {
      if (this.localData.isStep1Initial) {
        this.localData.isStep1Initial = false; // Prevent Step 1 from recalculating in the future
      }
      if (interval.fuelValues[changedFuelName] < 0) {
        interval.fuelValues[changedFuelName] = 0;
      }

      interval.fuelValues[changedFuelName] = this.roundToStep(
        interval.fuelValues[changedFuelName],
        this.stepSize
      );

      interval.totalAmount = Object.values(interval.fuelValues).reduce(
        (sum, val) => sum + val,
        0
      );
      // Enforce the 300% cap here
      this.checkAndClampInterval(interval);
    },
    getBarHeight(interval) {
      const totalAmount2025 = this.intervals[0].totalAmount;
      if (totalAmount2025 === 0) return 0;
      // const heightPercentage = (interval.totalAmount / totalAmount2025) * 100;
      // return (heightPercentage * this.maxBarHeight) / 100;

      const ratio = interval.totalAmount / totalAmount2025;
      const cappedRatio = Math.min(ratio, 3);
      const fractionOfContainer = cappedRatio / 3;

      return fractionOfContainer * this.maxBarHeight;
    },
    getFuelHeight(interval, fuel) {
      const totalFuelAmount = interval.totalAmount;
      if (totalFuelAmount === 0) return 0;
      const fuelAmount = interval.fuelValues[fuel.name];
      return (fuelAmount / totalFuelAmount) * 100;
    },
    getFuelPercentage(interval, fuel) {
      const totalAmount = interval.totalAmount;
      if (totalAmount === 0) return 0;
      const fuelAmount = interval.fuelValues[fuel.name];
      return (fuelAmount / totalAmount) * 100;
    },
    getActiveFuels(interval) {
      return this.fuels.filter((fuel) => interval.fuelValues[fuel.name] > 0);
    },
    getFuelsForInterval(interval) {
      // Reverse the order to have MGO at the bottom
      return this.getActiveFuels(interval).slice().reverse();
    },
    checkAndClampInterval(interval) {
      const totalAmount2025 = this.intervals[0].totalAmount;
      if (totalAmount2025 === 0) return;

      let maxAllowed = totalAmount2025 * this.MAX_FACTOR; // e.g. 3× 2025
      maxAllowed = this.roundToStep(maxAllowed, this.stepSize);

      // If the total exceeds the maximum allowed, clamp & show a message
      if (interval.totalAmount > maxAllowed) {
        this.stopDragHandle();
        // Find the difference
        //const exceededAmount = interval.totalAmount - maxAllowed;
        // Subtract from one or more fuels (simple approach: from the last changed one)
        // Or just clamp that last changed one. Here we'll do a direct clamp:
        const ratio = maxAllowed / interval.totalAmount;
        // Scale down each fuel proportionally
        Object.keys(interval.fuelValues).forEach((fuelName) => {
          let scaledValue = interval.fuelValues[fuelName] * ratio;
          scaledValue = this.roundToStep(scaledValue, this.stepSize);
          interval.fuelValues[fuelName] = scaledValue;
        });
        // Recalculate total
        interval.totalAmount = Object.values(interval.fuelValues)
          .reduce((sum, val) => sum + val, 0);

        // Provide user-friendly feedback
        //alert(`Exceeding the maximum allowed (300% of 2025). Values were clamped.`);
        //alert(maxAllowed);
      }
    },
    calculateCO2Equivalent(interval) {
      let totalCO2Eq = 0;
      for (const [fuel, amount] of Object.entries(interval.fuelValues)) {
        const factor = this.emissionFactors[fuel] || 0;
        totalCO2Eq += amount * factor;
      }
      return totalCO2Eq; // Format with commas and 2 decimal places
    },
    calculateCO2Reduction(interval) {
      const baseline = this.calculateCO2Equivalent(this.intervals[0]); // CO2 equivalent
      const currentCO2 = this.calculateCO2Equivalent(interval);
      if (baseline === 0) return 0; // Avoid division by zero
      return  Math.round(((currentCO2 - baseline) / baseline) * 100); // Percentage change
    },
  },
};
</script>


<style scoped>
.container {
  margin-top: 20px;
}

/* Main Container for Grid Alignment */
.bars-table-container {
  display: grid;
  grid-template-columns: 300px repeat(5, 120px);
  gap: 5px;
}


/* Bars Row (to align with table columns) */
.bars-row {
  display: contents;
}

/* Invisible div to align with 'Fuel Type' column */
.invisible-bar-space {
  width: 310px;
}

.stacked-bar {
  display: flex;
  flex-direction: column;
  /* Changed to column-reverse */
  background-color: #f0f0f0;
  border: 1px solid #ccc;
  position: relative;
  overflow: hidden;
  user-select: none;
  width: 100%;
  align-self: flex-end;
}

.bar {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  position: relative;
}

.bar-label-text {
  position: absolute;
  text-align: center;
  font-size: 10px;
  padding: 1px;
}

/* Drag Handle */
.drag-handle {
  width: 100%;
  height: 5px;
  background-color: #ccc;
  cursor: ns-resize;
}

/* Top Handle */
.top-handle {
  position: absolute;
  top: 0;
  height: 5px;
  background-color: #949393;
  cursor: ns-resize;
  z-index: 1;
}

/* Fuel Square */
.fuel-square {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border: 1px solid black;
  vertical-align: middle;
}

.fuel-bar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  max-width: 800px; /* Optional: Ensure a max-width */
}

/* Remove background colors for table rows */
.table-row-mgo td,
.table-row-lh2 td,
.table-row-ch2 td,
.table-row-ammonia td,
.table-row-methanol td,
.table-row-lng td {
  background-color: white;
}

/* Highlight Total Amount Row */
.total-row td {
  background-color: #eeeeee;
  font-weight: bold;
}

/* Table Section */
.table-section {
  grid-column: 1 / span 6;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 10px;
  text-align: center;
  border: 1px solid #ddd;
}

.table td:first-child {
  font-weight: bold;
  padding-right: 10px;
  text-align: left;
  min-width: 300px;
}

.table input[type='number'] {
  width: 100px;
}

/* Fuel Bar Colors */
.bar.mgo-bar,
.fuel-square.mgo-bar {
  background-color: #007bff;
}

.bar.lh2-bar,
.fuel-square.lh2-bar {
  background-color: #28a745;
}

.bar.ch2-bar,
.fuel-square.ch2-bar {
  background-color: #17a2b8;
}

.bar.ammonia-bar,
.fuel-square.ammonia-bar {
  background-color: #ffc107;
}

.bar.methanol-bar,
.fuel-square.methanol-bar {
  background-color: #dc3545;
}

.bar.lng-bar,
.fuel-square.lng-bar {
  background-color: #6f42c1;
}
</style>
