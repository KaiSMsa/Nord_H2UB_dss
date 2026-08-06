const test = require("node:test");
const assert = require("node:assert/strict");

const {
  INITIAL_MGO_EQUIVALENT_TONNES,
  INITIAL_PORT_FUEL_AMOUNTS_TONNES,
  createInitialFuelSelectionIntervals,
} = require("../src/constants/initialFuelSelection.js");

const years = ["2025", "2030", "2035", "2040"];

test("initial port and fuel-selection values come from one constants module", () => {
  assert.equal(INITIAL_MGO_EQUIVALENT_TONNES, 10_000);
  assert.deepEqual(INITIAL_PORT_FUEL_AMOUNTS_TONNES, {
    MGO: 10_000,
    MDO: 0,
    IFO: 0,
    VLSFO: 0,
    HFO: 0,
  });

  const intervals = createInitialFuelSelectionIntervals(years);
  assert.deepEqual(intervals[0].fuelValues, {
    MGO: 10_000,
    "Liquid Hydrogen": 0,
    "Compressed Hydrogen": 0,
    Ammonia: 0,
    Methanol: 0,
    LNG: 0,
  });
  assert.equal(intervals[1].fuelValues.MGO, 6_000);
  assert.equal(intervals[1].fuelValues["Liquid Hydrogen"], 3_000);
  assert.equal(intervals[1].fuelValues.LNG, 1_000);
  assert.equal(intervals[2].fuelValues.MGO, 3_000);
  assert.equal(intervals[2].fuelValues["Liquid Hydrogen"], 6_000);
  assert.equal(intervals[2].fuelValues.LNG, 1_000);
  assert.equal(intervals[3].totalAmount, 11_000);
  assert.equal(intervals[3].fuelValues.MGO, 1_100);
  assert.equal(intervals[3].fuelValues["Liquid Hydrogen"], 8_800);
  assert.equal(intervals[3].fuelValues.LNG, 1_100);
});
