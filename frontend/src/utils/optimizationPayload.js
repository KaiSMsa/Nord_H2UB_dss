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

function buildInitialStatePayload(fuels, capacitiesByFuel, demandByFuel, periods) {
  if (!Array.isArray(periods) || periods.length === 0) {
    throw new TypeError("periods must be a non-empty array");
  }

  const initialState = {};
  const firstPeriod = periods[0];

  fuels.forEach((fuel) => {
    const fuelName = typeof fuel === "string" ? fuel : fuel.name;
    const capacities = capacitiesByFuel[fuelName];
    const demandSeries = demandByFuel[fuelName];
    if (!Array.isArray(capacities) || capacities.length === 0) {
      throw new TypeError(`Capacities.${fuelName} must be a non-empty array`);
    }
    if (!demandSeries || typeof demandSeries !== "object") {
      throw new TypeError(`Demand.${fuelName} is required`);
    }

    const numericCapacities = capacities.map(Number);
    const minimumCapacity = Math.min(...numericCapacities);
    const maximumDemand = Math.max(...periods.map((period) => Number(demandSeries[period])));
    const initialDemand = Number(demandSeries[firstPeriod]);
    if (
      !numericCapacities.every((capacity) => Number.isFinite(capacity) && capacity > 0) ||
      !Number.isFinite(maximumDemand) ||
      !Number.isFinite(initialDemand) ||
      maximumDemand < 0 ||
      initialDemand < 0
    ) {
      throw new TypeError(`Invalid capacity or demand value for ${fuelName}`);
    }

    const tankCount = Math.ceil(maximumDemand / minimumCapacity);
    const state = Array.from({ length: tankCount }, () =>
      Array(numericCapacities.length).fill(0)
    );
    let remainingDemand = initialDemand;

    for (let tankIndex = 0; tankIndex < tankCount && remainingDemand > 0; tankIndex += 1) {
      const sufficientOptions = numericCapacities
        .map((capacity, index) => ({ capacity, index }))
        .filter(({ capacity }) => capacity >= remainingDemand);
      const optionIndex = sufficientOptions.length > 0
        ? sufficientOptions.reduce((smallest, option) =>
          option.capacity < smallest.capacity ? option : smallest
        ).index
        : numericCapacities.reduce(
          (largestIndex, capacity, index) =>
            capacity > numericCapacities[largestIndex] ? index : largestIndex,
          0
        );
      state[tankIndex][optionIndex] = 1;
      remainingDemand -= numericCapacities[optionIndex];
    }

    if (remainingDemand > 0) {
      throw new RangeError(`Initial tank state cannot satisfy ${fuelName} demand`);
    }
    initialState[fuelName] = state;
  });

  return initialState;
}

module.exports = { buildInitialStatePayload, buildTankCostPayload };
