<template>
    <div class="container">
        <h3>
            Select fuels to offer in the future
            <span class="info-tooltip">
                <i class="bi bi-info-circle-fill"></i>
                <span class="tooltip-content">
                    <ul class="mb-0">
                        <li>Enter the amount of each fuel you intend to supply for future years.</li>
                        <li>All figures are in tonnes of MGO-equivalent.</li>
                        <li>Adjust values by typing in the table or by dragging the bars.</li>
                        <li>The total amount per year is capped at <strong>300 % of the 2025 value</strong>.</li>
                        <li>Values are rounded to the <strong>nearest 100 tonnes</strong>.</li>
                    </ul>
                </span>
            </span>
        </h3>

        <!-- Container for bars and table using CSS grid -->
        <div class="bars-table-container">
            <!-- Bars Section -->
            <div class="bars-row">
                <!-- Invisible div to align with 'Fuel Type' column -->
                <div class="invisible-bar-space"></div>

                <div class="stacked-bar" v-for="interval in intervals" :key="interval.name"
                    :style="{ height: getBarHeight(interval) + 'px' }">
                    <!-- Top Handle -->
                    <div v-if="hasTopHandle(interval)" class="drag-handle top-handle" @mousedown.stop="
                        interval.name === '2025' || disabled ? null : startDragTopBar(interval, $event)
                        "></div>

                    <!-- Fuel Bars and Drag Handles -->
                    <div v-for="(item, index) in getBarItems(interval)" :key="index"
                        :class="item.type === 'bar' ? ['bar', item.fuel.class] : 'drag-handle'"
                        :style="item.type === 'bar' ? { height: item.height + '%' } : null" @mousedown.stop="
                            item.type === 'handle' && interval.name !== '2025' && !disabled
                                ? startDragHandle(interval, item.handleIndex, $event)
                                : null
                            ">
                        <!-- If it's a bar, display the label -->
                        <span v-if="item.type === 'bar'" class="bar-label-text">
                            {{ item.fuel.name }} ({{ getFuelPercentage(interval, item.fuel).toFixed(1) }}%)
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
                            <th v-for="interval in intervals" :key="interval.name">{{ interval.name }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Fuel Rows -->
                        <tr v-for="fuel in fuels" :key="fuel.name">
                            <td>
                                <span class="fuel-square" :class="fuel.class"></span>
                                {{ fuel.name }}
                            </td>
                            <td v-for="interval in intervals" :key="interval.name + '-' + fuel.name"
                                class="position-relative">
                                <input type="number" v-model.number="interval.fuelValues[fuel.name]"
                                    :disabled="interval.name === '2025' || disabled"
                                    @input="onFuelInput(interval, fuel.name)" min="0" step="100"
                                    :class="{ 'is-invalid': isInvalid(interval.name, fuel.name) }" />

                                <transition name="fade">
                                    <div v-if="isInvalid(interval.name, fuel.name)" class="error-box">
                                        {{ getError(interval.name, fuel.name) }}
                                    </div>
                                </transition>
                            </td>
                        </tr>

                        <!-- Total Amount Row -->
                        <tr class="total-row">
                            <td><strong>Total Amount (in tonnes of MGO-e)</strong></td>
                            <td v-for="interval in intervals" :key="'total-' + interval.name">
                                <span>{{ interval.totalAmount.toLocaleString('en-US') }}</span>
                            </td>
                        </tr>

                        <!-- CO₂ Equivalent Row -->
                        <tr class="total-row">
                            <td><strong>CO₂-equivalent (tonnes)</strong></td>
                            <td v-for="interval in intervals" :key="'co2-' + interval.name">
                                <span>{{ calculateCO2Equivalent(interval).toLocaleString('en-US') }}</span>
                            </td>
                        </tr>

                        <!-- Emission Reduction Row -->
                        <tr class="total-row">
                            <td><strong>CO₂-eq Reduction from 2025</strong></td>
                            <td v-for="(interval, index) in intervals" :key="'change-' + interval.name">
                                <span v-if="index === 0">-</span>
                                <span v-else>
                                    <span :class="{
                                        'text-danger': calculateCO2Reduction(interval) > 0,
                                        'text-success': calculateCO2Reduction(interval) < 0,
                                    }">
                                        {{ Math.abs(calculateCO2Reduction(interval)) }}%
                                        <i :class="calculateCO2Reduction(interval) > 0
                                                ? 'bi bi-arrow-up'
                                                : 'bi bi-arrow-down'
                                            " :style="{
                            color: calculateCO2Reduction(interval) > 0 ? 'red' : 'green',
                            marginLeft: '5px',
                        }"></i>
                                    </span>
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>
  
  <script>
import cloneDeep from 'lodash.clonedeep'

export default {
    name: 'FuelBarEditor',
    props: {
        fuelSelection: {
            type: Object,
            required: true,
        },
        disabled: { type: Boolean, default: false },
    },
    data() {
        return {
            localData: cloneDeep(this.fuelSelection),
            maxBarHeight: 600,
            stepSize: 100,
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
                MGO: 3.17,
                'Liquid Hydrogen': 0,
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
            // NEW: keep track of the last valid (accepted) values to allow easy revert
            lastValidFuelValues: {},
            // NEW: error states keyed by `intervalName-fuelName`
            errorStates: {},
        }
    },
    mounted() {
        // initialise last‑valid map once component is mounted
        this.updateLastValidValues()
    },
    computed: {
        intervals() {
            return this.localData.intervals
        },
    },
    watch: {
        // reflect changes upward
        localData: {
            handler(newVal) {
                this.$emit('update:fuelSelection', newVal)
            },
            deep: true,
        },
    },
    methods: {
        /* ----------  helper methods for the new error‑handling  ---------- */
        keyFor(intervalName, fuelName) {
            return `${intervalName}-${fuelName}`
        },
        isInvalid(intervalName, fuelName) {
            const k = this.keyFor(intervalName, fuelName)
            return this.errorStates[k]?.visible || false
        },
        getError(intervalName, fuelName) {
            const k = this.keyFor(intervalName, fuelName)
            return this.errorStates[k]?.message || ''
        },
        showError(interval, fuelName, message, previousValue) {
            const k = this.keyFor(interval.name, fuelName)
            this.errorStates[k] = { visible: true, message }

            // rollback to previously accepted value **without** updating totals of other fuels
            interval.fuelValues[fuelName] = previousValue

            // ensure error disappears after 2 seconds & reset invalid style
            setTimeout(() => {
                if (this.errorStates[k]) this.errorStates[k].visible = false
            }, 2000)
        },
        updateLastValidValues() {
            this.intervals.forEach((it) => {
                if (!this.lastValidFuelValues[it.name]) this.lastValidFuelValues[it.name] = {}
                Object.keys(it.fuelValues).forEach((fname) => {
                    this.lastValidFuelValues[it.name][fname] = it.fuelValues[fname]
                })
            })
        },

        /* ----------------------------------------------------------------- */

        hasTopHandle(interval) {
            return this.getFuelsForInterval(interval).length > 0
        },
        getBarItems(interval) {
            const fuelsForInterval = this.getFuelsForInterval(interval)
            const items = []

            fuelsForInterval.forEach((fuel, index) => {
                items.push({ type: 'bar', fuel, height: this.getFuelHeight(interval, fuel) })
                if (index < fuelsForInterval.length - 1) {
                    items.push({ type: 'handle', handleIndex: index })
                }
            })
            return items
        },
        /* --------------------------- typing logic ------------------------ */
        onFuelInput(interval, changedFuelName) {
            if (this.localData.isStep1Initial) this.localData.isStep1Initial = false

            const prevAccepted =
                this.lastValidFuelValues?.[interval.name]?.[changedFuelName] ?? 0

            // ensure non‑negative & round *before* any validations
            let newValue = interval.fuelValues[changedFuelName]
            if (newValue < 0) newValue = 0
            if (newValue >= this.stepSize)
                newValue = this.roundToStep(newValue, this.stepSize)
            interval.fuelValues[changedFuelName] = newValue

            // compute the would‑be new total for the interval
            const newTotal = Object.values(interval.fuelValues).reduce((s, v) => s + v, 0)
            const total2025 = this.intervals[0].totalAmount || 0
            const maxAllowed = this.roundToStep(total2025 * this.MAX_FACTOR, this.stepSize)

            if (total2025 && newTotal > maxAllowed) {
                // exceeded → do **NOT** modify other fuels, just show error and rollback
                const msg = `Value too high – total would exceed the 300% cap (${maxAllowed.toLocaleString('en-US')} t)`
                this.showError(interval, changedFuelName, msg, prevAccepted)
                return // early exit, keep previous totals intact
            }

            // within limit – accept & persist as last valid, update totals
            interval.totalAmount = newTotal
            if (!this.lastValidFuelValues[interval.name])
                this.lastValidFuelValues[interval.name] = {}
            this.lastValidFuelValues[interval.name][changedFuelName] = newValue
        },

        /* ---------------------- existing drag logic ---------------------- */
        startDragHandle(interval, handleIndex, event) {
            this.dragging = true
            this.dragInfo.interval = interval
            this.dragInfo.handleIndex = handleIndex
            this.dragInfo.initialMouseY = event.clientY
            this.dragInfo.initialFuelValues = { ...interval.fuelValues }
            window.addEventListener('mousemove', this.onDragHandle)
            window.addEventListener('mouseup', this.stopDragHandle)
        },
        onDragHandle(event) {
            if (this.localData.isStep1Initial) this.localData.isStep1Initial = false
            if (!this.dragging) return

            const deltaY = event.clientY - this.dragInfo.initialMouseY
            const containerHeight = this.getBarHeight(this.dragInfo.interval)
            if (containerHeight === 0) return

            const fuelsForInterval = this.getFuelsForInterval(this.dragInfo.interval)
            if (this.dragInfo.handleIndex >= fuelsForInterval.length - 1) return this.stopDragHandle()

            const fuelAbove = fuelsForInterval[this.dragInfo.handleIndex]
            const fuelBelow = fuelsForInterval[this.dragInfo.handleIndex + 1]

            if (!fuelAbove || !fuelBelow) return this.stopDragHandle()

            const fuelAboveHeight = this.getFuelBarHeight(this.dragInfo.interval, fuelAbove)
            const fuelBelowHeight = this.getFuelBarHeight(this.dragInfo.interval, fuelBelow)
            const combinedBarHeight = fuelAboveHeight + fuelBelowHeight
            if (combinedBarHeight === 0) return

            const percentageChange = (deltaY / combinedBarHeight) * 100
            const initialAmountAbove = this.dragInfo.initialFuelValues[fuelAbove.name]
            const initialAmountBelow = this.dragInfo.initialFuelValues[fuelBelow.name]
            const totalFuelAmount = initialAmountAbove + initialAmountBelow
            const amountChange = (percentageChange / 100) * totalFuelAmount

            let newAmountAbove = initialAmountAbove + amountChange
            let newAmountBelow = initialAmountBelow - amountChange
            if (newAmountAbove < this.stepSize || newAmountBelow < this.stepSize) return

            newAmountAbove = this.roundToStep(newAmountAbove, this.stepSize)
            newAmountBelow = this.roundToStep(newAmountBelow, this.stepSize)

            this.dragInfo.interval.fuelValues[fuelAbove.name] = newAmountAbove
            this.dragInfo.interval.fuelValues[fuelBelow.name] = newAmountBelow

            this.checkAndClampInterval(this.dragInfo.interval)
        },
        startDragTopBar(interval, event) {
            this.dragging = true
            this.dragInfo.interval = interval
            this.dragInfo.initialMouseY = event.clientY
            const fuelsForInterval = this.getFuelsForInterval(interval)
            this.dragInfo.topFuel = fuelsForInterval[0]
            if (!this.dragInfo.topFuel) return
            this.dragInfo.initialFuelValue = interval.fuelValues[this.dragInfo.topFuel.name]
            this.dragInfo.initialFuelValues = { ...interval.fuelValues }
            this.dragInfo.initialContainerHeight = this.getBarHeight(interval)
            document.body.style.cursor = 'ns-resize'
            window.addEventListener('mousemove', this.onDragTopBar)
            window.addEventListener('mouseup', this.stopDragHandle)
        },
        onDragTopBar(event) {
            if (this.localData.isStep1Initial) this.localData.isStep1Initial = false
            if (!this.dragging) return

            const deltaY = event.clientY - this.dragInfo.initialMouseY
            const containerHeight = this.dragInfo.initialContainerHeight
            if (containerHeight === 0) return

            const topFuel = this.dragInfo.topFuel
            const initialTopFuelAmount = this.dragInfo.initialFuelValue
            const initialTotalFuel = Object.values(this.dragInfo.initialFuelValues).reduce((s, v) => s + v, 0)
            const percentageChange = (deltaY / containerHeight) * 100
            const amountChange = (percentageChange / 100) * initialTotalFuel
            let newAmount = initialTopFuelAmount - amountChange
            if (newAmount < this.stepSize) newAmount = this.stepSize
            newAmount = this.roundToStep(newAmount, this.stepSize)

            this.dragInfo.interval.fuelValues[topFuel.name] = newAmount
            this.dragInfo.interval.totalAmount = Object.values(this.dragInfo.interval.fuelValues).reduce(
                (s, v) => s + v,
                0
            )
            this.checkAndClampInterval(this.dragInfo.interval)
        },
        stopDragHandle() {
            this.dragging = false
            window.removeEventListener('mousemove', this.onDragHandle)
            window.removeEventListener('mousemove', this.onDragTopBar)
            window.removeEventListener('mouseup', this.stopDragHandle)
            document.body.style.cursor = 'default'
            // refresh last‑valid map after any drag changes were accepted
            this.updateLastValidValues()
        },

        /* ---------------------- utility / calc helpers ------------------- */
        roundToStep(value, step) {
            return Math.round(value / step) * step
        },
        getFuelBarHeight(interval, fuel) {
            const totalBarHeight = this.getBarHeight(interval)
            const fuelHeightPercentage = this.getFuelHeight(interval, fuel)
            return (fuelHeightPercentage / 100) * totalBarHeight
        },
        getBarHeight(interval) {
            const totalAmount2025 = this.intervals[0].totalAmount
            if (totalAmount2025 === 0) return 0
            const ratio = interval.totalAmount / totalAmount2025
            const cappedRatio = Math.min(ratio, 3)
            return (cappedRatio / 3) * this.maxBarHeight
        },
        getFuelHeight(interval, fuel) {
            const totalFuelAmount = interval.totalAmount
            if (totalFuelAmount === 0) return 0
            return (interval.fuelValues[fuel.name] / totalFuelAmount) * 100
        },
        getFuelPercentage(interval, fuel) {
            const totalAmount = interval.totalAmount
            if (totalAmount === 0) return 0
            return (interval_fuelValues[fuel.name] / totalAmount) * 100
        },
        getActiveFuels(interval) {
            return this.fuels.filter((f) => interval.fuelValues[f.name] > 0)
        },
        getFuelsForInterval(interval) {
            return this.getActiveFuels(interval).slice().reverse()
        },
        checkAndClampInterval(interval) {
            const totalAmount2025 = this.intervals[0].totalAmount
            if (totalAmount2025 === 0) return
            let maxAllowed = this.roundToStep(totalAmount2025 * this.MAX_FACTOR, this.stepSize)
            if (interval.totalAmount > maxAllowed) {
                const ratio = maxAllowed / interval.totalAmount
                Object.keys(interval.fuelValues).forEach((fname) => {
                    let scaled = this.roundToStep(interval.fuelValues[fname] * ratio, this.stepSize)
                    interval.fuelValues[fname] = scaled
                })
                interval.totalAmount = Object.values(interval.fuelValues).reduce((s, v) => s + v, 0)
            }
        },
        calculateCO2Equivalent(interval) {
            return Object.entries(interval.fuelValues).reduce((sum, [name, amt]) => {
                return sum + amt * (this.emissionFactors[name] || 0)
            }, 0)
        },
        calculateCO2Reduction(interval) {
            const baseline = this.calculateCO2Equivalent(this.intervals[0])
            const current = this.calculateCO2Equivalent(interval)
            if (baseline === 0) return 0
            return Math.round(((current - baseline) / baseline) * 100)
        },
    },
}
</script>
  
  <style scoped>
/********* NEW error‑handling styles *********/
.error-box {
    position: absolute;
    left: 0;
    right: 0;
    top: 100%;
    margin-top: 4px;
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    padding: 4px 6px;
    font-size: 0.75rem;
    z-index: 2;
}

.is-invalid {
    border-color: #dc3545 !important;
}

.position-relative {
    position: relative;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

/************************************************/
