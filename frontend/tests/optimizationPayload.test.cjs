const test = require("node:test");
const assert = require("node:assert/strict");

const { buildTankCostPayload } = require("../src/utils/optimizationPayload.js");

test("optimizer base costs equal the structured UI calculation before display rounding", () => {
  const payload = buildTankCostPayload([
    {
      id: "liquid-hydrogen",
      name: "Liquid Hydrogen",
      rows: [{ capacity: 3000 }],
      changeRate: -2,
      maintenanceCost: 4,
      decommissioningCost: 10,
    },
  ], 3);
  const option = payload.TankOptions["Liquid Hydrogen"][0];

  assert.equal(
    payload.Costs["Liquid Hydrogen"].baseInvestmentCostsUSD[0],
    option.baseInvestmentCostUSD
  );
  assert.equal(payload.Capacities["Liquid Hydrogen"][0], 3000);
  assert.equal(
    payload.Costs["Liquid Hydrogen"].fuelCostAdjustmentRatePerPeriod,
    -0.02
  );
  assert.equal(
    payload.Costs["Liquid Hydrogen"].maintenanceRatePerPlanningPeriod,
    0.04
  );
  assert.equal(payload.Costs["Liquid Hydrogen"].decommissioningRate, 0.1);
  assert.equal(payload.Costs["Liquid Hydrogen"].discountRatePerPeriod, null);
  assert.equal(
    payload.Costs["Liquid Hydrogen"].investmentCostsUSDByPeriod[0][2],
    option.baseInvestmentCostUSD * 0.98 ** 2
  );
  assert.equal(
    payload.Costs["Liquid Hydrogen"].maintenanceCostsUSDByPeriod[0][2],
    option.baseInvestmentCostUSD * 0.04
  );
  assert.equal(
    payload.Costs["Liquid Hydrogen"].decommissioningCostsUSDByPeriod[0][2],
    option.baseInvestmentCostUSD * 0.1
  );
});

test("out-of-range options cannot reach the optimizer", () => {
  assert.throws(
    () =>
      buildTankCostPayload([
        {
          id: "compressed-hydrogen",
          name: "Compressed Hydrogen",
          rows: [{ capacity: 3000 }],
          changeRate: -2,
          maintenanceCost: 4,
          decommissioningCost: 10,
        },
      ]),
    /above the maximum/
  );
});
