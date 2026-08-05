const { estimateTankOption, fuelParameterCatalog } = require("./tankCost.js");

function percentageToRate(value, fieldName) {
  if (
    value === null ||
    value === undefined ||
    (typeof value === "string" && value.trim() === "")
  ) {
    throw new TypeError(`${fieldName} is required`);
  }
  const percentage = Number(value);
  if (!Number.isFinite(percentage)) {
    throw new TypeError(`${fieldName} must be a finite percentage`);
  }
  return percentage / 100;
}

function buildTankCostPayload(fuels) {
  const payload = {
    Capacities: {},
    TankOptions: {},
    Costs: {},
  };

  fuels.forEach((fuel) => {
    const fuelName = fuel.name;
    const tankOptions = fuel.rows.map((row) =>
      estimateTankOption(fuel.id || fuelName, row.capacity)
    );
    const invalidOption = tankOptions.find(
      (option) => option.validationWarnings.length > 0
    );

    if (invalidOption) {
      throw new RangeError(
        `${fuelName} ${invalidOption.capacityMgoEquivalentTonnes} t MGO-e: ${invalidOption.validationWarnings.join(" ")}`
      );
    }

    payload.Capacities[fuelName] = tankOptions.map(
      (option) => option.capacityMgoEquivalentTonnes
    );
    payload.TankOptions[fuelName] = tankOptions;
    const baseInvestmentCostsUSD = tankOptions.map(
      (option) => option.baseInvestmentCostUSD
    );
    const technologyCostAdjustmentRatePerPlanningPeriod = percentageToRate(
      fuel.technologyCostAdjustmentRatePercent,
      `${fuelName}.technologyCostAdjustmentRatePercent`
    );
    const maintenanceRatePerPlanningPeriod = percentageToRate(
      fuel.maintenanceRatePercent,
      `${fuelName}.maintenanceRatePercent`
    );
    const decommissioningRateAtClosure = percentageToRate(
      fuel.decommissioningRateAtClosurePercent,
      `${fuelName}.decommissioningRateAtClosurePercent`
    );
    const discountRatePerPlanningPeriod = percentageToRate(
      fuel.discountRatePercent,
      `${fuelName}.discountRatePercent`
    );

    payload.Costs[fuelName] = {
      baseInvestmentCostsUSD,
      technologyCostAdjustmentRatePerPlanningPeriod,
      maintenanceRatePerPlanningPeriod,
      maintenanceRateBasis: fuelParameterCatalog.common.maintenanceRateBasis,
      decommissioningRateAtClosure,
      decommissioningRateBasis:
        fuelParameterCatalog.common.decommissioningRateBasis,
      discountRatePerPlanningPeriod,
    };
  });

  return payload;
}

module.exports = { buildTankCostPayload };
