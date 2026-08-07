const INITIAL_MGO_EQUIVALENT_TONNES = 9_100;
const INITIAL_VALUE_STEP_TONNES = 100;

const INITIAL_PORT_FUEL_AMOUNTS_TONNES = Object.freeze({
  MGO: 9_100,
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

const INITIAL_FUEL_PLAN_BY_YEAR = Object.freeze({
  "2025": Object.freeze({
    MGO: 9_100,
    "Liquid Hydrogen": 0,
    Methanol: 0,
  }),
  "2030": Object.freeze({
    MGO: 6_000,
    "Liquid Hydrogen": 3_000,
    Methanol: 1_000,
  }),
  "2035": Object.freeze({
    MGO: 4_000,
    "Liquid Hydrogen": 6_000,
    Methanol: 1_000,
  }),
  "2040": Object.freeze({
    MGO: 3_000,
    "Liquid Hydrogen": 8_000,
    Methanol: 1_000,
  }),
  "2045": Object.freeze({
    MGO: 1_400,
    "Liquid Hydrogen": 11_000,
    Methanol: 1_000,
  }),
  "2050": Object.freeze({
    MGO: 0,
    "Liquid Hydrogen": 13_500,
    Methanol: 1_000,
  }),
});

function roundToStep(value) {
  return Math.round(value / INITIAL_VALUE_STEP_TONNES)
    * INITIAL_VALUE_STEP_TONNES;
}

function createInitialFuelSelectionIntervals(
  planningYears,
  initialMgoEquivalentTonnes = INITIAL_MGO_EQUIVALENT_TONNES
) {
  const scale = initialMgoEquivalentTonnes / INITIAL_MGO_EQUIVALENT_TONNES;

  return planningYears.map((year) => {
    const plannedValues = INITIAL_FUEL_PLAN_BY_YEAR[String(year)];
    if (!plannedValues) {
      throw new RangeError(`No initial fuel-selection plan is defined for ${year}`);
    }
    const fuelValues = Object.fromEntries(FUEL_NAMES.map((fuelName) => [
      fuelName,
      roundToStep((plannedValues[fuelName] || 0) * scale),
    ]));
    return {
      name: year,
      totalAmount: Object.values(fuelValues).reduce(
        (total, amount) => total + amount,
        0
      ),
      fuelValues,
    };
  });
}

module.exports = {
  INITIAL_FUEL_PLAN_BY_YEAR,
  INITIAL_MGO_EQUIVALENT_TONNES,
  INITIAL_PORT_FUEL_AMOUNTS_TONNES,
  createInitialFuelSelectionIntervals,
};
