const test = require("node:test");
const assert = require("node:assert/strict");

const { buildTankCostPayload } = require("../src/utils/optimizationPayload.js");

function validFuel(overrides = {}) {
  return {
    id: "liquid-hydrogen",
    name: "Liquid Hydrogen",
    rows: [{ capacity: 3000 }],
    discountRatePercent: 5,
    technologyCostAdjustmentRatePercent: -2,
    maintenanceRatePercent: 4,
    decommissioningRateAtClosurePercent: 10,
    ...overrides,
  };
}

test("request preserves exact base costs and converts percentages once", () => {
  const payload = buildTankCostPayload([validFuel()]);
  const costs = payload.Costs["Liquid Hydrogen"];
  const option = payload.TankOptions["Liquid Hydrogen"][0];

  assert.equal(costs.baseInvestmentCostsUSD[0], option.baseInvestmentCostUSD);
  assert.equal(payload.Capacities["Liquid Hydrogen"][0], 3000);
  assert.equal(costs.discountRatePerPlanningPeriod, 0.05);
  assert.equal(costs.technologyCostAdjustmentRatePerPlanningPeriod, -0.02);
  assert.equal(costs.maintenanceRatePerPlanningPeriod, 0.04);
  assert.equal(costs.decommissioningRateAtClosure, 0.1);
  assert.equal("investmentCostsUSDByPeriod" in costs, false);
  assert.equal("maintenanceCostsUSDByPeriod" in costs, false);
  assert.equal("decommissioningCostsUSDByPeriod" in costs, false);
});

test("valid zero percentages are preserved rather than treated as missing", () => {
  const payload = buildTankCostPayload([
    validFuel({
      discountRatePercent: 0,
      technologyCostAdjustmentRatePercent: 0,
      maintenanceRatePercent: 0,
      decommissioningRateAtClosurePercent: 0,
    }),
  ]);
  const costs = payload.Costs["Liquid Hydrogen"];

  assert.equal(costs.discountRatePerPlanningPeriod, 0);
  assert.equal(costs.technologyCostAdjustmentRatePerPlanningPeriod, 0);
  assert.equal(costs.maintenanceRatePerPlanningPeriod, 0);
  assert.equal(costs.decommissioningRateAtClosure, 0);
});

for (const field of [
  "discountRatePercent",
  "technologyCostAdjustmentRatePercent",
  "maintenanceRatePercent",
  "decommissioningRateAtClosurePercent",
]) {
  test(`missing ${field} is rejected before request serialization`, () => {
    const fuel = validFuel();
    delete fuel[field];
    assert.throws(() => buildTankCostPayload([fuel]), /is required/);
  });
}

test("out-of-range options cannot reach the backend", () => {
  assert.throws(
    () =>
      buildTankCostPayload([
        validFuel({
          id: "compressed-hydrogen",
          name: "Compressed Hydrogen",
          rows: [{ capacity: 3000 }],
        }),
      ]),
    /above the maximum/
  );
});
