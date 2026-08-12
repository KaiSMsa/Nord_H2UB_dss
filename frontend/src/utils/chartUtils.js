// src/utils/chartUtils.js
// -------------------------------------------------------------
//  Shared chart-building helpers (no Vue dependency)
// -------------------------------------------------------------
import { PLANNING_YEARS } from '@/constants/planningYears.js';
import { FUELS} from "@/constants/fuels.js";
import { aggregateFuelYearCosts } from '@/utils/costAggregation.js';
import { getOrderedTankIds } from '@/utils/planHighlights.js';
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

    /* Use the same opening chronology as Plan Highlights. */
    getOrderedTankIds(res[fuel], YEARS).forEach(tid => {
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
        tankId: tid,
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
  const costs = scenario.resultCosts || {};
  const transitions = scenario.resultTransitions || {};
  if (!scenario.resultCosts && !scenario.resultTransitions) {
    return { labels: [], datasets: [] };
  }

  const datasets = [];

  FUEL_LIST.forEach(fuel => {
    if (!costs[fuel] && !transitions[fuel]) return;

    const data = YEARS.map(y =>
      aggregateFuelYearCosts(costs, transitions, fuel, y)
    );

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
  const costs = scenario.resultCosts || {};
  const transitions = scenario.resultTransitions || {};
  if (!scenario.resultCosts && !scenario.resultTransitions) {
    return { labels: [], datasets: [] };
  }

  const totals = {
    opening: 0,
    operating: 0,
    decommissioning: 0,
    transition: 0,
  };

  const fuels = new Set([
    ...Object.keys(costs),
    ...Object.keys(transitions),
  ]);
  fuels.forEach(fuel => {
    YEARS.forEach(y => {
      const detail = aggregateFuelYearCosts(costs, transitions, fuel, y);
      totals.opening += detail.opening;
      totals.operating += detail.operating;
      totals.decommissioning += detail.decommissioning;
      totals.transition += detail.transition;
    });
  });

  return {
    labels: [
      'Opening Costs',
      'Maintenance Costs',
      'Decommissioning Costs',
      'Transition Costs',
    ],
    datasets: [
      {
        data: [
          totals.opening,
          totals.operating,
          totals.decommissioning,
          totals.transition,
        ],
        backgroundColor: ['#007bff', '#28a745', '#dc3545', '#6f42c1']
      }
    ]
  };
}
