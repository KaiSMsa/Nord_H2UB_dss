const { estimateTankOption } = require("./tankCost.js");

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

function buildTankCostPayload(fuels, discountRatePercent) {
  const payload = {
    Capacities: {},
    TankOptions: {},
    discountRatePerPlanningPeriod: percentageToRate(
      discountRatePercent,
      "discountRatePercent"
    ),
    technologyCostAdjustmentRatePerPlanningPeriod: {},
    maintenanceRatePerPlanningPeriod: {},
    decommissioningRateAtClosure: {},
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
    payload.technologyCostAdjustmentRatePerPlanningPeriod[fuelName] = percentageToRate(
      fuel.technologyCostAdjustmentRatePercent,
      `${fuelName}.technologyCostAdjustmentRatePercent`
    );
    payload.maintenanceRatePerPlanningPeriod[fuelName] = percentageToRate(
      fuel.maintenanceRatePercent,
      `${fuelName}.maintenanceRatePercent`
    );
    payload.decommissioningRateAtClosure[fuelName] = percentageToRate(
      fuel.decommissioningRateAtClosurePercent,
      `${fuelName}.decommissioningRateAtClosurePercent`
    );

  });

  return payload;
}

module.exports = { buildTankCostPayload };
