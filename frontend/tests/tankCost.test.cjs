const test = require("node:test");
const assert = require("node:assert/strict");

const {
  calculateBaseInvestmentCost,
  calculateDecommissioningCost,
  calculateDiscountFactor,
  calculateMaintenanceCost,
  calculatePhysicalFuelMass,
  calculatePresentValueCost,
  calculateScaledShellCost,
  calculateStorageVolume,
  calculateTimeAdjustedInvestmentCost,
  estimateTankOption,
  fuelParameterCatalog,
} = require("../src/utils/tankCost.js");

function approximatelyEqual(actual, expected, tolerance, message) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `${message}: expected ${expected} ± ${tolerance}, received ${actual}`
  );
}

test("physical mass and storage volume conversions preserve precision", () => {
  const mass = calculatePhysicalFuelMass(3000, 120);
  const volume = calculateStorageVolume(mass, 70.8);

  approximatelyEqual(mass, 1070, 1e-10, "LH2 physical mass");
  approximatelyEqual(volume, 15112.994350282486, 1e-9, "LH2 volume");
});

test("shell calibration is applied at 1,000 m3 with exponent 0.65", () => {
  const shellCost = calculateScaledShellCost(1000, 2500, 1000, 0.65);
  assert.equal(shellCost, 2500000);
  assert.equal(fuelParameterCatalog.common.referenceVolumeM3, 1000);
  assert.equal(fuelParameterCatalog.common.scalingExponent, 0.65);
});

test("fixed cost is added exactly once", () => {
  assert.equal(calculateBaseInvestmentCost(2000000, 2500000), 4500000);
});

const regressionCases = [
  ["mgo", 3000, 3529.4117647058824, 2769898.897165507],
  ["liquid-hydrogen", 1070, 15112.994350282483, 16605547.674780592],
  ["compressed-hydrogen", 1070, 52093.476144109045, 35670772.86889839],
  ["ammonia", 6903.225806451612, 10122.031974269226, 8253287.941257987],
  ["methanol", 6452.261306532663, 8167.419375357802, 4849667.483388843],
  ["lng", 2620.408163265306, 6165.666266506602, 5393034.387552835],
];

for (const [fuelId, expectedMass, expectedVolume, expectedCost] of regressionCases) {
  test(`${fuelId} 3,000 t MGO-e regression`, () => {
    const result = estimateTankOption(fuelId, 3000);
    approximatelyEqual(result.physicalMassTonnes, expectedMass, 1e-9, "mass");
    approximatelyEqual(result.storageVolumeM3, expectedVolume, 1e-9, "volume");
    approximatelyEqual(result.investmentCostUSD, expectedCost, 0.01, "cost");
  });
}

test("compressed hydrogen uses 20.54 kg/m3", () => {
  assert.equal(estimateTankOption("compressed-hydrogen", 1000).densityKgPerM3, 20.54);
});

test("hydrogen tank costs contain no liquefaction or compression surcharge", () => {
  for (const fuelId of ["liquid-hydrogen", "compressed-hydrogen"]) {
    const result = estimateTankOption(fuelId, 1000);
    assert.equal(
      result.investmentCostUSD,
      result.fixedInstallationCostUSD + result.shellInstallationCostUSD
    );
    assert.equal("liquefactionCostUSD" in result, false);
    assert.equal("compressionCostUSD" in result, false);
  }
});

test("maintenance and decommissioning derive from the same base investment cost", () => {
  const baseCost = estimateTankOption("ammonia", 3000).baseInvestmentCostUSD;
  assert.equal(calculateMaintenanceCost(baseCost, 0.04), baseCost * 0.04);
  assert.equal(calculateDecommissioningCost(baseCost, 0.1), baseCost * 0.1);
  assert.equal(fuelParameterCatalog.common.maintenanceRateBasis, "annual");
});

test("annual cost adjustment and discounting use elapsed years", () => {
  const adjusted = calculateTimeAdjustedInvestmentCost(100, -0.02, 10);
  const discountFactor = calculateDiscountFactor(0.05, 10);
  const presentValue = calculatePresentValueCost(adjusted, discountFactor);

  approximatelyEqual(adjusted, 100 * 0.98 ** 10, 1e-12, "adjusted cost");
  approximatelyEqual(discountFactor, 1 / 1.05 ** 10, 1e-12, "discount factor");
  approximatelyEqual(presentValue, 100 * 0.98 ** 10 / 1.05 ** 10, 1e-12, "present value");
});

test("discount factor validates the rate and period index", () => {
  assert.equal(calculateDiscountFactor(0.05, 0), 1);
  assert.equal(calculateDiscountFactor(0.05, 1), 1 / 1.05);
  assert.equal(calculateDiscountFactor(0.05, 2), 1 / 1.05 ** 2);
  assert.throws(() => calculateDiscountFactor(-1, 1), /greater than -1/);
  assert.throws(() => calculateDiscountFactor(0.05, -1), /greater than or equal to zero/);
});

test("configured discount default and its approval status are exposed", () => {
  assert.equal(
    fuelParameterCatalog.common.defaultDiscountRateAnnual,
    0.04
  );
  assert.equal(
    fuelParameterCatalog.common.discountRateDefaultStatus,
    "author-approval-required"
  );
});

test("all default tank options comply with their fuel-specific limits", () => {
  for (const fuel of fuelParameterCatalog.fuels) {
    for (const capacity of fuel.defaultCapacitiesMgoEquivalentTonnes) {
      assert.deepEqual(estimateTankOption(fuel.id, capacity).validationWarnings, []);
    }
  }
});

test("operational CO2-e factors match the retained fuel-characteristics table", () => {
  const factors = Object.fromEntries(
    fuelParameterCatalog.fuels.map((fuel) => [
      fuel.id,
      fuel.operationalEmissionFactorTonnesCO2ePerTonneMgoEquivalent,
    ])
  );

  assert.deepEqual(factors, {
    mgo: 3.17,
    "liquid-hydrogen": 0,
    "compressed-hydrogen": 0,
    ammonia: 0,
    methanol: 2.96,
    lng: 2.4,
  });
});
