const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const { buildTankCostPayload } = require("../src/utils/optimizationPayload.js");

const pythonExecutable = process.env.PYTHON || "python";
const pythonProbe = spawnSync(pythonExecutable, ["--version"], {
  encoding: "utf8",
});
const pythonAvailable = !pythonProbe.error && pythonProbe.status === 0;
const ortoolsProbe = pythonAvailable
  ? spawnSync(pythonExecutable, ["-c", "import ortools"], { encoding: "utf8" })
  : { status: 1 };
const optimizerAvailable = ortoolsProbe.status === 0;

function approximatelyEqual(actual, expected, tolerance = 1e-8) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `expected ${expected} ± ${tolerance}, received ${actual}`
  );
}

test(
  "frontend request rates become backend model coefficients without rounding",
  { skip: pythonAvailable ? false : "Python runtime is unavailable" },
  () => {
    const tankPayload = buildTankCostPayload([
      {
        id: "ammonia",
        name: "Ammonia",
        rows: [{ capacity: 3000 }],
        technologyCostAdjustmentRateAnnualPercent: -1.3,
        maintenanceRateAnnualPercent: 3.7,
        decommissioningRateAtClosurePercent: 12.3,
      },
    ], 7.1, 5, 1.2);
    const request = {
      T: ["2025", "2030", "2035", "2040"],
      Fuels: ["Ammonia"],
      ...tankPayload,
    };
    const backendScript = path.resolve(
      __dirname,
      "../../backend/financial_parameters.py"
    );
    const result = spawnSync(pythonExecutable, [backendScript], {
      input: JSON.stringify(request),
      encoding: "utf8",
    });

    assert.equal(result.status, 0, result.stderr || result.stdout);
    const prepared = JSON.parse(result.stdout).Ammonia;
    const baseCost = request.TankOptions.Ammonia[0].baseInvestmentCostUSD;

    assert.equal(prepared.discountRateAnnual, 0.071);
    assert.equal(
      prepared.technologyCostAdjustmentRateAnnual,
      -0.013
    );
    assert.equal(prepared.maintenanceRateAnnual, 0.037);
    assert.equal(prepared.decommissioningRateAtClosure, 0.123);
    approximatelyEqual(
      prepared.openingCostCoefficientsUSD[0][2],
      baseCost * 0.987 ** 10 / 1.071 ** 10
    );
    approximatelyEqual(
      prepared.maintenanceCostCoefficientsUSD[0][2],
      5 * baseCost * 0.037 / 1.071 ** 10
    );
    approximatelyEqual(
      prepared.decommissioningCostCoefficientsUSD[0][2],
      baseCost * 0.123 / 1.071 ** 10
    );
  }
);

test(
  "optimizer response preserves received rates and full-precision costs",
  { skip: optimizerAvailable ? false : "Python with OR-Tools is unavailable" },
  () => {
    const tankPayload = buildTankCostPayload([
      {
        id: "mgo",
        name: "MGO",
        rows: [{ capacity: 2000 }],
        technologyCostAdjustmentRateAnnualPercent: -2,
        maintenanceRateAnnualPercent: 4,
        decommissioningRateAtClosurePercent: 10,
      },
    ], 5, 5, 1.2);
    const request = {
      T: ["2025", "2030"],
      Fuels: ["MGO"],
      Demand: { MGO: { "2025": 2000, "2030": 2000 } },
      InitialState: { MGO: [[1]] },
      ...tankPayload,
    };
    const backendScript = path.resolve(
      __dirname,
      "../../backend/model_tank_index.py"
    );
    const temporaryDirectory = fs.mkdtempSync(
      path.join(os.tmpdir(), "nord-h2ub-model-test-")
    );

    try {
      const result = spawnSync(pythonExecutable, [backendScript], {
        cwd: temporaryDirectory,
        input: JSON.stringify(request),
        encoding: "utf8",
      });
      assert.equal(result.status, 0, result.stderr || result.stdout);
      const response = JSON.parse(result.stdout);
      const parameters = response.financialParameters;
      const baseCost = request.TankOptions.MGO[0].baseInvestmentCostUSD;

      assert.equal(parameters.discountRateAnnual, 0.05);
      assert.equal(
        parameters.technologyCostAdjustmentRateAnnual.MGO,
        -0.02
      );
      assert.equal(parameters.maintenanceRateAnnual.MGO, 0.04);
      assert.equal(parameters.decommissioningRateAtClosure.MGO, 0.1);
      assert.deepEqual(response.periodMapping[0], {
        label: "2025",
        periodIndex: 0,
        elapsedYears: 0,
        discountFactor: 1,
      });
      assert.equal(response.periodMapping[1].elapsedYears, 5);
      assert.equal(parameters.planningPeriodYears, 5);
      assert.equal(parameters.transitionCostRate, 1.2);
      approximatelyEqual(response.periodMapping[1].discountFactor, 1 / 1.05 ** 5);
      approximatelyEqual(
        response.costs.MGO["2025"].Tank_1["2000"].operating,
        5 * baseCost * 0.04
      );
      approximatelyEqual(
        response.costs.MGO["2030"].Tank_1["2000"].operating,
        5 * baseCost * 0.04 / 1.05 ** 5
      );
      approximatelyEqual(
        response.costBreakdown.totalObjectiveUSD,
        response.costBreakdown.maintenanceCostUSD
      );
    } finally {
      fs.rmSync(temporaryDirectory, { recursive: true, force: true });
    }
  }
);
