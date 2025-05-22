<template>
  <b-tabs v-model="activeTab">
    <b-tab v-for="(sc) in scenarios" :key="sc.id" :title="sc.name">
      <!-- draw the viewer only the first time we have results -->
      <ResultChartViewer v-if="sc.viewerReady" :chartData="sc.cachedChartData" :costChartData="sc.cachedCostChart"
        :costDistributionData="sc.cachedCostDist" />
      <p v-else>No results available.</p>
      <!-- ▸▸ Export button (only if we have data) -->
      <div v-if="sc.viewerReady" class="d-flex justify-content-end mt-3">
        <b-button variant="success" @click="exportScenarioExcelJS(sc)">
          Export to Excel
        </b-button>
      </div>
    </b-tab>
  </b-tabs>

</template>

<script>
// import cloneDeep from 'lodash.clonedeep'
import ResultChartViewer from './ResultChartViewer.vue'
import { utils, writeFile } from 'xlsx';          // SheetJS
import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';              // tiny helper  

export default {
  name: 'ResultBarChart',
  components: { ResultChartViewer },
  props: { scenarios: Array },


  data() {
    return {
      /* start on the newest scenario */
      activeTab: this.scenarios.length - 1
    }
  },

  watch: {
    /* whenever a scenario is added, jump to the new (last) tab */
    scenarios(val) {
      this.activeTab = val.length - 1
    }
  },

  methods: {
    /* ---------------------------------------------------------------- */
    exportScenario(sc) {
      /* ----------- build three AOA blocks ----------------------------- */
      /* 1) Fuel Capacity */
      const fuelCapAOA = [
        ['Fuel', 'Total MGO-eq (t)'],
        ...Object.entries(sc.data.portFuelInformation.fuelAmounts)
      ];

      /* 2) Fuel Selection */
      const intervals = sc.data.fuelBarSelection.intervals;
      const selHdr = ['Fuel', ...intervals.map(i => i.name), 'Total MGO-eq', 'Total CO₂-eq'];
      const factors = { MGO: 3.17, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0, Ammonia: 0, Methanol: 1.37, LNG: 2.75 };

      const selBody = Object.keys(intervals[0].fuelValues).map(fuel => {
        const row = [fuel];
        let sumMGO = 0, sumCO2 = 0;
        intervals.forEach(iv => {
          const v = iv.fuelValues[fuel];
          row.push(v);
          sumMGO += v;
          sumCO2 += v * (factors[fuel] || 0);
        });
        row.push(sumMGO, +sumCO2.toFixed(1));
        return row;
      });

      const fuelSelAOA = [selHdr, ...selBody];

      /* 3) Tank Sizes sheets merged into one */
      const tankAOAs = sc.data.fuelCapacitySelection.fuels.map(f => {
        const hdr = [`Tank Sizes – ${f.name}`, '', ''];
        const subHdr = ['Capacity (t)', 'Storage Vol (m³)', 'Cost (USD)'];
        const body = f.rows.map(r => [r.capacity, r.storageVolume, r.cost]);
        return [hdr, subHdr, ...body];
      });

      /* ----------- write into a single worksheet ---------------------- */
      const ws = utils.aoa_to_sheet([[]]);
      let rowPtr = 0;

      const addBlock = (aoa) => {
        utils.sheet_add_aoa(ws, aoa, { origin: { r: rowPtr, c: 0 } });
        this.applyBorder(ws, {                    // ← note “this.”
          s: { r: rowPtr, c: 0 },
          e: { r: rowPtr + aoa.length - 1, c: aoa[0].length - 1 }
        });
        rowPtr += aoa.length + 2;
      };

      addBlock(fuelCapAOA);
      addBlock(fuelSelAOA);
      tankAOAs.forEach(addBlock);

      const wb = utils.book_new();
      utils.book_append_sheet(wb, ws, 'Scenario data');
      writeFile(wb, `Scenario_${sc.id}_export.xlsx`);
    },

    async exportScenarioExcelJS(sc) {
      /* ───────────────────── helpers ───────────────────── */
      const thin = { style: 'thin' };

      /**
       * Add a 2-D array (`aoa`) as a table.
       * @param {Worksheet} ws          – ExcelJS worksheet
       * @param {array[]}   aoa         – array-of-arrays (rows)
       * @param {object}    opts
       *        opts.headerRow : 0-based index of the row to shade (default 0)
       *        opts.shadeCol1 : shade 1st column? (default true)
       */
      function addBlock(ws, aoa, { headerRow = 0, shadeCol1 = true } = {}) {
        const start = ws.rowCount + 1;       // first row just about to be written
        aoa.forEach(r => ws.addRow(r));
        const end = ws.rowCount;           // last row of this block
        const cols = aoa[0].length;

        /* borders + shading */
        for (let r = start; r <= end; ++r) {
          for (let c = 1; c <= cols; ++c) {
            const cell = ws.getCell(r, c);
            cell.border = { top: thin, bottom: thin, left: thin, right: thin };

            /* header row shading */
            if (r === start + headerRow) {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD9D9D9' } };
            }
            /* optional first-column shading */
            if (shadeCol1 && c === 1) {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD9D9D9' } };
            }
          }
        }
      }

      /* ───────────────── workbook / sheet ───────────────── */
      const wb = new ExcelJS.Workbook();
      const ws = wb.addWorksheet(`Scenario_${sc.id + 1}_data`);

      /* 1) Fuel-capacity block ─ header row + first column shaded */
      const titleCapRow = ws.addRow(["Port capacity in 2025"]);
      titleCapRow.font = { bold: true };

      const fuelCapAOA = [
        ['Fuel', 'Total MGO-eq (t)'],
        ...Object.entries(sc.data.portFuelInformation.fuelAmounts)
      ];
      addBlock(ws, fuelCapAOA);                           // default options OK

      /* 2) Fuel-selection block ─ header row + first column shaded */
      /* blank line between sections (not before first) */
      if (ws.rowCount) ws.addRow([]);

      const demandTitle = ws.addRow(["Fuel demand"]);
      demandTitle.font = { bold: true };

      const intervals = sc.data.fuelBarSelection.intervals;
      const fuels = Object.keys(intervals[0].fuelValues);
      const factors = {
        MGO: 3.17, 'Liquid Hydrogen': 0, 'Compressed Hydrogen': 0,
        Ammonia: 0, Methanol: 1.37, LNG: 2.75
      };

      const selHdr = ['Fuel', ...intervals.map(i => i.name)];
      const colTotMGO = Array(intervals.length).fill(0);
      const colTotCO2 = Array(intervals.length).fill(0);

      const selBody = fuels.map(f => {
        const row = [f];
        intervals.forEach((iv, j) => {
          const v = iv.fuelValues[f];
          row.push(v);
          colTotMGO[j] += v;
          colTotCO2[j] += v * (factors[f] || 0);
        });
        return row;
      });

      const fuelSelAOA = [
        selHdr,
        ...selBody,
        ['Total MGO-eq', ...colTotMGO],
        ['Total CO₂-eq', ...colTotCO2.map(v => +v.toFixed(1))]
      ];
      addBlock(ws, fuelSelAOA);                           // still want shaded col 1

      /* 3) Tank-size tables ─ ONLY "Capacity … Cost" row shaded */
      sc.data.fuelCapacitySelection.fuels.forEach(f => {
        if (ws.rowCount) ws.addRow([]);
        /* ── ❶ title line ───────────────────────────────────────────── */
        const titleRowIdx = ws.rowCount + 1; 
        ws.addRow([`Tank sizes – ${f.name}`]);
        ws.mergeCells(titleRowIdx, 1, titleRowIdx, 3);       // merge A…C of that row
        ws.getCell(titleRowIdx, 1).font = { bold: true };    // bold face
        /* ── ❷ write the table ─────────────────────────────────────────── */ 
        const subHdr = [['Capacity (t)', 'Storage Vol (m³)', 'Cost (USD)']]; // shaded
        const body = f.rows.map(r => [r.capacity, r.storageVolume, r.cost]);
        addBlock(ws, [...subHdr, ...body], { headerRow: 0, shadeCol1: false });
      });

      /* @@@@@@@@@@@@@@@@@@@@@@@@@@@@ 2nd sheet: Results @@@@@@@@@@@@@@@@@@@@@@@@@@@@ */
      const wsCap = wb.addWorksheet(`Scenario_${sc.id + 1}_capacity_results`);

      /* years come straight from the bar-chart labels */
      const years = sc.cachedChartData.labels.map(String);  // make sure they’re strings

      /* quick helpers -------------------------------------------------------- */
      /** Count active tanks (opened + operating, ignore closed) for one fuel,
       * one year, one capacity. */
      function activeCount(fuel, yr, cap) {
        const yrObj = sc.resultData?.[fuel]?.[yr];
        if (!yrObj) return 0;

        let cnt = 0;
        Object.values(yrObj).forEach(tankObj => {
          const capKey = Object.keys(tankObj)[0]; // only one key per tank
          if (+capKey !== cap) return;

          const status = tankObj[capKey];
          if ((status.opened ?? 0) > 0 || (status.operating ?? 0) > 0) cnt += 1;
        });
        return cnt;
      }

      /* ---------------------------------------------------------------------- */
      sc.data.fuelCapacitySelection.fuels.forEach(fuelCfg => {
        const fuel = fuelCfg.name;
        const capacities = fuelCfg.rows.map(r => r.capacity).sort((a, b) => a - b);

        /* blank line between tables (skip before very first section) */
        if (wsCap.rowCount) wsCap.addRow([]);

        /* label line */
        const title = wsCap.addRow([fuel]);
        title.font = { bold: true };
        /* header */
        const hdr = ['Year\\Capacity', ...capacities.map(c => `${c} t`), 'Total (t)'];

        /* body */
        const body = years.map(yr => {
          const row = [yr];
          let total = 0;
          capacities.forEach(cap => {
            const nTanks = activeCount(fuel, yr, cap);
            row.push(nTanks);
            total += nTanks * cap;
          });
          row.push(total);
          return row;
        });

        addBlock(wsCap, [hdr, ...body]);  // highlight header row + first col
      });


      /* @@@@@@@@@@@@@@@@@@@@@@@@@@@@ 3rd sheet: Results @@@@@@@@@@@@@@@@@@@@@@@@@@@@ */



      /* ────────────────── ③ Cost-results sheet ─────────────────── */
      const wsCost = wb.addWorksheet(`Scenario_${sc.id + 1}_cost_results`);
      const costYears = sc.cachedCostChart.labels.map(String);
      //cosnt fuels = sc.data.fuelCapacitySelection.fuels.map(f => f.name);

      /* map <fuel> → per-year cost objects */
      const costMap = {};
      sc.cachedCostChart.datasets.forEach(ds => costMap[ds.label] = ds.data);

      const costTypes = [
        { label: 'Opening Costs ($)', key: 'opening' },
        { label: 'Maintenance Costs ($)', key: 'operating' },
        { label: 'Decommissioning Costs ($)', key: 'decommissioning' }
      ];

      costTypes.forEach((ct) => {
        /* blank line between sections (not before first) */
        if (wsCost.rowCount) wsCost.addRow([]);

        /* section title */
        const trow = wsCost.addRow([ct.label]);
        trow.font = { bold: true };

        /* header */
        const hdr = ['Fuel\\Year', ...costYears];

        /* rows for each fuel */
        const rows = fuels.map(f => {
          const r = [f];
          costYears.forEach((yr, idx) => {
            const v = costMap[f]?.[idx]?.[ct.key] ?? 0;
            r.push(v);
          });
          return r;
        });

        /* total row */
        const totRow = ['Total'];
        costYears.forEach((yr, idx) => {
          let s = 0;
          fuels.forEach(f => { s += costMap[f]?.[idx]?.[ct.key] ?? 0; });
          totRow.push(s);
        });

        addBlock(wsCost, [hdr, ...rows, totRow]);     // highlight header + col 1
      });
      /* ───────────────── save file ───────────────── */
      const buf = await wb.xlsx.writeBuffer();
      saveAs(new Blob([buf]), `Scenario_${sc.id + 1}_export.xlsx`);
    }

  }
}
</script>