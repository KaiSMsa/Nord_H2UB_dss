const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildInitialStatePayload,
  buildTankCostPayload,
} = require("../src/utils/optimizationPayload.js");

function validFuel(overrides = {}) {
  return {
    id: "liquid-hydrogen",
    name: "Liquid Hydrogen",
    rows: [{ capacity: 3000 }],
    technologyCostAdjustmentRatePercent: -2,
    maintenanceRatePercent: 4,
    decommissioningRateAtClosurePercent: 10,
    ...overrides,
  };
}

test("request preserves exact base costs and converts percentages once", () => {
  const payload = buildTankCostPayload([validFuel()], 5);
  const option = payload.TankOptions["Liquid Hydrogen"][0];

  assert.equal(Number.isFinite(option.baseInvestmentCostUSD), true);
  assert.equal(payload.Capacities["Liquid Hydrogen"][0], 3000);
  assert.equal(payload.discountRatePerPlanningPeriod, 0.05);
  assert.equal(payload.technologyCostAdjustmentRatePerPlanningPeriod["Liquid Hydrogen"], -0.02);
  assert.equal(payload.maintenanceRatePerPlanningPeriod["Liquid Hydrogen"], 0.04);
  assert.equal(payload.decommissioningRateAtClosure["Liquid Hydrogen"], 0.1);
  assert.equal("Costs" in payload, false);
});

test("valid zero percentages are preserved rather than treated as missing", () => {
  const payload = buildTankCostPayload([
    validFuel({
      technologyCostAdjustmentRatePercent: 0,
      maintenanceRatePercent: 0,
      decommissioningRateAtClosurePercent: 0,
    }),
  ], 0);

  assert.equal(payload.discountRatePerPlanningPeriod, 0);
  assert.equal(payload.technologyCostAdjustmentRatePerPlanningPeriod["Liquid Hydrogen"], 0);
  assert.equal(payload.maintenanceRatePerPlanningPeriod["Liquid Hydrogen"], 0);
  assert.equal(payload.decommissioningRateAtClosure["Liquid Hydrogen"], 0);
});

for (const field of [
  "technologyCostAdjustmentRatePercent",
  "maintenanceRatePercent",
  "decommissioningRateAtClosurePercent",
]) {
  test(`missing ${field} is rejected before request serialization`, () => {
    const fuel = validFuel();
    delete fuel[field];
    assert.throws(() => buildTankCostPayload([fuel], 5), /is required/);
  });
}

test("missing scalar discount rate is rejected before request serialization", () => {
  assert.throws(() => buildTankCostPayload([validFuel()]), /discountRatePercent is required/);
});

test("discount rate is scalar while other rates are mappings by fuel", () => {
  const payload = buildTankCostPayload([
    validFuel(),
    validFuel({
      id: "ammonia",
      name: "Ammonia",
      technologyCostAdjustmentRatePercent: -3,
      maintenanceRatePercent: 5,
      decommissioningRateAtClosurePercent: 12,
    }),
  ], 6);

  assert.equal(payload.discountRatePerPlanningPeriod, 0.06);
  assert.deepEqual(payload.technologyCostAdjustmentRatePerPlanningPeriod, {
    "Liquid Hydrogen": -0.02,
    Ammonia: -0.03,
  });
  assert.deepEqual(payload.maintenanceRatePerPlanningPeriod, {
    "Liquid Hydrogen": 0.04,
    Ammonia: 0.05,
  });
  assert.deepEqual(payload.decommissioningRateAtClosure, {
    "Liquid Hydrogen": 0.1,
    Ammonia: 0.12,
  });
});

test("out-of-range options cannot reach the backend", () => {
  assert.throws(
    () =>
      buildTankCostPayload([
        validFuel({
          id: "compressed-hydrogen",
          name: "Compressed Hydrogen",
          rows: [{ capacity: 3000 }],
        }),
      ], 5),
    /above the maximum/
  );
});

test("initial state is explicit, binary, and satisfies period-zero demand", () => {
  const initialState = buildInitialStatePayload(
    ["MGO", "Ammonia"],
    { MGO: [2000, 5000, 10000], Ammonia: [1000, 5000, 7000] },
    {
      MGO: { "2025": 10000, "2030": 5000 },
      Ammonia: { "2025": 0, "2030": 7000 },
    },
    ["2025", "2030"]
  );

  assert.deepEqual(initialState.MGO[0], [0, 0, 1]);
  assert.equal(initialState.MGO.flat().reduce((sum, value) => sum + value, 0), 1);
  assert.equal(initialState.Ammonia.flat().reduce((sum, value) => sum + value, 0), 0);
});
