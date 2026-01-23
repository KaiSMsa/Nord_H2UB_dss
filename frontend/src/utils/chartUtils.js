// src/utils/chartUtils.js
// -------------------------------------------------------------
//  Shared chart-building helpers (no Vue dependency)
// -------------------------------------------------------------
import { PLANNING_YEARS } from '@/constants/planningYears.js';
import { FUELS} from "@/constants/fuels.js";
const FUEL_LIST = FUELS.map(f => f.name);
const FUEL_COLORS = Object.fromEntries(FUELS.map(f => [f.name, f.color]));
const YEARS      = PLANNING_YEARS;


/* --------------------------------------------------
 * 1) Capacity - stacked bar
 * -------------------------------------------------- */
export function buildChartData (scenario) {
  const res = scenario.resultData;
  if (!res) return { labels: [], datasets: [] };

  const datasets = [];

  FUEL_LIST.forEach(fuel => {
    if (!res[fuel]) return;

    /* gather tank IDs present in any year */
    const tankIds = new Set();
    YEARS.forEach(y => {
      if (res[fuel][y]) Object.keys(res[fuel][y]).forEach(tid => tankIds.add(tid));
    });

    /* dataset per tank */
    tankIds.forEach(tid => {
      const data = YEARS.map(y => {
        let value = 0;
        const yObj = res[fuel][y];
        if (yObj && yObj[tid]) {
          Object.entries(yObj[tid]).forEach(([cap, status]) => {
            if (status.opened || status.operating) value += +cap;
          });
        }
        return value;
      });

      datasets.push({
        label: `${fuel} – ${tid}`,
        data,
        backgroundColor: FUEL_COLORS[fuel],
        stack: fuel
      });
    });
  });

  return { labels: YEARS, datasets };
}

/* --------------------------------------------------
 * 2) Cost stacked-log bar
 * -------------------------------------------------- */
export function buildCostChartData (scenario) {
  const costs = scenario.resultCosts;
  if (!costs) return { labels: [], datasets: [] };

  const datasets = [];

  FUEL_LIST.forEach(fuel => {
    if (!costs[fuel]) return;

    const data = YEARS.map(y => {
      let opening = 0, operating = 0, decommissioning = 0;
      if (costs[fuel][y]) {
        Object.values(costs[fuel][y]).forEach(tank =>
          Object.values(tank).forEach(c => {
            opening        += c.opened       || 0;
            operating      += c.operating    || 0;
            decommissioning+= c.closed       || 0;
          })
        );
      }
      return {
        total: opening + operating + decommissioning,
        opening, operating, decommissioning
      };
    });

    datasets.push({
      label: fuel,
      data,
      backgroundColor: FUEL_COLORS[fuel],
      stack: fuel
    });
  });

  return { labels: YEARS, datasets };
}

/* --------------------------------------------------
 * 3) Cost distribution pie
 * -------------------------------------------------- */
export function buildCostDistData (scenario) {
  const costs = scenario.resultCosts;
  if (!costs) return { labels: [], datasets: [] };

  const totals = { opened: 0, operating: 0, closed: 0 };

  Object.values(costs).forEach(fuelObj => {
    YEARS.forEach(y => {
      if (fuelObj[y]) {
        Object.values(fuelObj[y]).forEach(tank =>
          Object.values(tank).forEach(c => {
            totals.opened        += c.opened       || 0;
            totals.operating     += c.operating    || 0;
            totals.closed        += c.closed       || 0;
          })
        );
      }
    });
  });

  return {
    labels: ['Opening Costs', 'Maintenance Costs', 'Decommissioning Costs'],
    datasets: [
      {
        data: [totals.opened, totals.operating, totals.closed],
        backgroundColor: ['#007bff', '#28a745', '#dc3545']
      }
    ]
  };
}
