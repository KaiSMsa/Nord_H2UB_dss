<template>
<b-tabs v-model="activeTab" >
  <b-tab
    v-for="(sc) in scenarios"
    :key="sc.id"
    :title="sc.name"
  >
    <!-- draw the viewer only the first time we have results -->
    <ResultChartViewer
      v-if="sc.viewerReady"
      :chartData="sc.cachedChartData"
      :costChartData="sc.cachedCostChart"
      :costDistributionData="sc.cachedCostDist"
    />
    <p v-else>No results available.</p>
  </b-tab>
</b-tabs>

</template>

<script>
// import cloneDeep from 'lodash.clonedeep'
import ResultChartViewer from './ResultChartViewer.vue'

export default {
  name: 'ResultBarChart',
  components: { ResultChartViewer },
  props: { scenarios: Array },


  data () {
    return {
      /* start on the newest scenario */
      activeTab: this.scenarios.length - 1
    }
  },

  watch: {
    /* whenever a scenario is added, jump to the new (last) tab */
    scenarios (val) {
      this.activeTab = val.length - 1
    }
  }


  // computed: {
  //   lastIndex () { return this.scenarios.length - 1 }
  // },

  // methods: {
    /* helper: does the scenario have result data? */
    // hasResults (sc) {
    //   return sc.resultData && Object.keys(sc.resultData).length > 0
    // },

    /* ------------------------------------------------------------------
     *  BUILD Chart data – same logic you had in MainDashboard but
     *  transformed into standalone helpers so each scenario can be
     *  rendered independently.
     * ------------------------------------------------------------------ */
    // buildChartData (sc) {
    //   const res = sc.resultData
    //   if (!res) return { labels: [], datasets: [] }

    //   const years     = ['2025', '2030', '2035', '2040', '2045']
    //   const fuelList  = ['MGO','Liquid Hydrogen','Compressed Hydrogen','Ammonia','Methanol','LNG']
    //   const fuelColors= {
    //     MGO:'#007bff','Liquid Hydrogen':'#28a745','Compressed Hydrogen':'#17a2b8',
    //     Ammonia:'#ffc107', Methanol:'#dc3545', LNG:'#6f42c1'
    //   }
    //   const datasets = []

    //   fuelList.forEach(fuel => {
    //     if (!res[fuel]) return
    //     const tankIds = new Set()
    //     years.forEach(y => res[fuel][y] && Object.keys(res[fuel][y]).forEach(tid => tankIds.add(tid)))

    //     tankIds.forEach(tid => {
    //       const data = years.map(y => {
    //         let v = 0
    //         const yObj = res[fuel][y]
    //         if (yObj && yObj[tid]) {
    //           Object.entries(yObj[tid]).forEach(([cap,status]) => {
    //             if (status.opened || status.operating) v += +cap
    //           })
    //         }
    //         return v
    //       })
    //       datasets.push({ label:`${fuel} – ${tid}`, data, backgroundColor:fuelColors[fuel], stack:fuel })
    //     })
    //   })

    //   return { labels: years, datasets }
    // },

    // buildCostChartData (sc) {
    //   const costs = sc.resultCosts
    //   if (!costs) return { labels: [], datasets: [] }

    //   const years     = ['2025','2030','2035','2040','2045']
    //   const fuelList  = ['MGO','Liquid Hydrogen','Compressed Hydrogen','Ammonia','Methanol','LNG']
    //   const fuelColors= {
    //     MGO:'#007bff','Liquid Hydrogen':'#28a745','Compressed Hydrogen':'#17a2b8',
    //     Ammonia:'#ffc107', Methanol:'#dc3545', LNG:'#6f42c1'
    //   }
    //   const datasets = []

    //   fuelList.forEach(fuel => {
    //     if (!costs[fuel]) return
    //     const data = years.map(y => {
    //       let open=0, op=0, dec=0
    //       if (costs[fuel][y]) {
    //         Object.values(costs[fuel][y]).forEach(tank =>
    //           Object.values(tank).forEach(c => {
    //             open += c.opened||0; op += c.operating||0; dec += c.closed||0
    //           })
    //         )
    //       }
    //       return { total: open+op+dec, opening:open, operating:op, decommissioning:dec }
    //     })
    //     datasets.push({ label:fuel, data, backgroundColor:fuelColors[fuel], stack:fuel })
    //   })

    //   return { labels: years, datasets }
    // },

    // buildCostDistData (sc) {
    //   const costs = sc.resultCosts
    //   if (!costs) return { labels:[], datasets:[] }

    //   const years = ['2025','2030','2035','2040','2045']
    //   const total = { opened:0, operating:0, closed:0 }

    //   Object.values(costs).forEach(fuelObj => {
    //     years.forEach(y => {
    //       if (fuelObj[y]) {
    //         Object.values(fuelObj[y]).forEach(tank =>
    //           Object.values(tank).forEach(c => {
    //             total.opened += c.opened||0
    //             total.operating += c.operating||0
    //             total.closed += c.closed||0
    //           })
    //         )
    //       }
    //     })
    //   })

    //   return {
    //     labels: ['Opening Costs','Maintenance Costs','Decommissioning Costs'],
    //     datasets: [
    //       { data:[total.opened,total.operating,total.closed],
    //         backgroundColor:['#007bff','#28a745','#dc3545'] }
    //     ]
    //   }
    // }
  // }
}
</script>