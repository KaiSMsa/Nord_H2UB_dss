const INITIAL_MGO_EQUIVALENT_TONNES = 10_000;
const INITIAL_VALUE_STEP_TONNES = 100;
const LATER_PERIOD_TOTAL_GROWTH_RATE = 0.1;

const INITIAL_PORT_FUEL_AMOUNTS_TONNES = Object.freeze({
  MGO: 10_000,
  MDO: 0,
  IFO: 0,
  VLSFO: 0,
  HFO: 0,
});

const FUEL_NAMES = Object.freeze([
  "MGO",
  "Liquid Hydrogen",
  "Compressed Hydrogen",
  "Ammonia",
  "Methanol",
  "LNG",
]);

const INITIAL_FUEL_MIX_BY_PERIOD = Object.freeze([
  Object.freeze({ MGO: 1 }),
  Object.freeze({ MGO: 0.6, "Liquid Hydrogen": 0.3, LNG: 0.1 }),
  Object.freeze({ MGO: 0.3, "Liquid Hydrogen": 0.6, LNG: 0.1 }),
]);

const LATER_PERIOD_FUEL_MIX = Object.freeze({
  MGO: 0.1,
  "Liquid Hydrogen": 0.8,
  LNG: 0.1,
});

function roundToStep(value) {
  return Math.round(value / INITIAL_VALUE_STEP_TONNES)
    * INITIAL_VALUE_STEP_TONNES;
}

function createFuelValues(totalMgoEquivalentTonnes, mix) {
  return Object.fromEntries(FUEL_NAMES.map((fuelName) => [
    fuelName,
    roundToStep(totalMgoEquivalentTonnes * (mix[fuelName] || 0)),
  ]));
}

function createInitialFuelSelectionIntervals(
  planningYears,
  initialMgoEquivalentTonnes = INITIAL_MGO_EQUIVALENT_TONNES
) {
  let periodTotal = Math.ceil(
    initialMgoEquivalentTonnes / INITIAL_VALUE_STEP_TONNES
  ) * INITIAL_VALUE_STEP_TONNES;

  return planningYears.map((year, periodIndex) => {
    if (periodIndex >= INITIAL_FUEL_MIX_BY_PERIOD.length) {
      periodTotal = Math.ceil(
        periodTotal * (1 + LATER_PERIOD_TOTAL_GROWTH_RATE)
        / INITIAL_VALUE_STEP_TONNES
      ) * INITIAL_VALUE_STEP_TONNES;
    }
    const mix = INITIAL_FUEL_MIX_BY_PERIOD[periodIndex]
      || LATER_PERIOD_FUEL_MIX;
    return {
      name: year,
      totalAmount: periodTotal,
      fuelValues: createFuelValues(periodTotal, mix),
    };
  });
}

module.exports = {
  INITIAL_FUEL_MIX_BY_PERIOD,
  INITIAL_MGO_EQUIVALENT_TONNES,
  INITIAL_PORT_FUEL_AMOUNTS_TONNES,
  LATER_PERIOD_FUEL_MIX,
  LATER_PERIOD_TOTAL_GROWTH_RATE,
  createInitialFuelSelectionIntervals,
};
