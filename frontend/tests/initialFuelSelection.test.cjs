const test = require("node:test");
const assert = require("node:assert/strict");

const {
  INITIAL_MGO_EQUIVALENT_TONNES,
  INITIAL_PORT_FUEL_AMOUNTS_TONNES,
  createInitialFuelSelectionIntervals,
} = require("../src/constants/initialFuelSelection.js");

const years = ["2025", "2030", "2035", "2040", "2045", "2050"];
const expectedPlan = {
  MGO: [9_100, 6_000, 4_000, 3_000, 1_400, 0],
  "Liquid Hydrogen": [0, 0, 0, 0, 0, 0],
  "Compressed Hydrogen": [0, 0, 0, 0, 0, 0],
  Ammonia: [0, 3_000, 6_000, 8_000, 11_000, 13_500],
  Methanol: [0, 1_000, 1_000, 1_000, 1_000, 1_000],
  LNG: [0, 0, 0, 0, 0, 0],
};

test("initial port and year-by-year selection use the centralized plan", () => {
  assert.equal(INITIAL_MGO_EQUIVALENT_TONNES, 9_100);
  assert.deepEqual(INITIAL_PORT_FUEL_AMOUNTS_TONNES, {
    MGO: 9_100,
    MDO: 0,
    IFO: 0,
    VLSFO: 0,
    HFO: 0,
  });

  const intervals = createInitialFuelSelectionIntervals(years);
  for (const [fuelName, expectedValues] of Object.entries(expectedPlan)) {
    assert.deepEqual(
      intervals.map((interval) => interval.fuelValues[fuelName]),
      expectedValues
    );
  }
  assert.deepEqual(
    intervals.map((interval) => interval.totalAmount),
    [9_100, 10_000, 11_000, 12_000, 13_400, 14_500]
  );
});

test("an undefined planning year is rejected clearly", () => {
  assert.throws(
    () => createInitialFuelSelectionIntervals(["2055"]),
    /No initial fuel-selection plan is defined for 2055/
  );
});
