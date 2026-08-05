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
        discountRatePercent: 5,
        technologyCostAdjustmentRatePercent: -2,
        maintenanceRatePercent: 4,
        decommissioningRateAtClosurePercent: 10,
      },
    ]);
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
    const baseCost = request.Costs.Ammonia.baseInvestmentCostsUSD[0];

    assert.equal(prepared.discountRatePerPlanningPeriod, 0.05);
    assert.equal(
      prepared.technologyCostAdjustmentRatePerPlanningPeriod,
      -0.02
    );
    assert.equal(prepared.maintenanceRatePerPlanningPeriod, 0.04);
    assert.equal(prepared.decommissioningRateAtClosure, 0.1);
    approximatelyEqual(
      prepared.investmentCostsUSDByPeriod[0][2],
      baseCost * 0.98 ** 2 / 1.05 ** 2
    );
    approximatelyEqual(
      prepared.maintenanceCostsUSDByPeriod[0][2],
      baseCost * 0.04 / 1.05 ** 2
    );
    approximatelyEqual(
      prepared.decommissioningCostsUSDByPeriod[0][2],
      baseCost * 0.1 / 1.05 ** 2
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
        discountRatePercent: 5,
        technologyCostAdjustmentRatePercent: -2,
        maintenanceRatePercent: 4,
        decommissioningRateAtClosurePercent: 10,
      },
    ]);
    const request = {
      T: ["2025", "2030"],
      Fuels: ["MGO"],
      Demand: { MGO: { "2025": 2000, "2030": 2000 } },
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
      const parameters = response.financialParameters.MGO;
      const baseCost = request.Costs.MGO.baseInvestmentCostsUSD[0];

      assert.equal(parameters.discountRatePerPlanningPeriod, 0.05);
      assert.equal(
        parameters.technologyCostAdjustmentRatePerPlanningPeriod,
        -0.02
      );
      assert.equal(parameters.maintenanceRatePerPlanningPeriod, 0.04);
      assert.equal(parameters.decommissioningRateAtClosure, 0.1);
      approximatelyEqual(
        response.costs.MGO["2025"].Tank_1["2000"].operating,
        baseCost * 0.04
      );
      approximatelyEqual(
        response.costs.MGO["2030"].Tank_1["2000"].operating,
        baseCost * 0.04 / 1.05
      );
    } finally {
      fs.rmSync(temporaryDirectory, { recursive: true, force: true });
    }
  }
);
