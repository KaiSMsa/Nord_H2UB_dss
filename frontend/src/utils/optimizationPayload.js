const {
  calculateDecommissioningCost,
  calculateDiscountFactor,
  calculateMaintenanceCost,
  calculatePresentValueCost,
  calculateTimeAdjustedInvestmentCost,
  estimateTankOption,
  fuelParameterCatalog,
} = require("./tankCost.js");

function percentageToRate(value, fieldName) {
  const percentage = Number(value);
  if (!Number.isFinite(percentage)) {
    throw new TypeError(`${fieldName} must be a finite percentage`);
  }
  return percentage / 100;
}

function buildTankCostPayload(fuels, periodCount = 1) {
  if (!Number.isInteger(periodCount) || periodCount <= 0) {
    throw new RangeError("periodCount must be a positive integer");
  }

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
    const fuelCostAdjustmentRatePerPeriod = percentageToRate(
      fuel.changeRate,
      `${fuelName}.changeRate`
    );
    const maintenanceRatePerPlanningPeriod = percentageToRate(
      fuel.maintenanceCost,
      `${fuelName}.maintenanceCost`
    );
    const decommissioningRate = percentageToRate(
      fuel.decommissioningCost,
      `${fuelName}.decommissioningCost`
    );
    const discountRatePerPeriod =
      fuelParameterCatalog.common.discountRatePerPeriod;
    const discountFactors = Array.from({ length: periodCount }, (_, periodIndex) =>
      discountRatePerPeriod === null
        ? 1
        : calculateDiscountFactor(discountRatePerPeriod, periodIndex)
    );

    payload.Costs[fuelName] = {
      baseInvestmentCostsUSD,
      fuelCostAdjustmentRatePerPeriod,
      maintenanceRatePerPlanningPeriod,
      maintenanceRateBasis: fuelParameterCatalog.common.maintenanceRateBasis,
      decommissioningRate,
      decommissioningRateBasis:
        fuelParameterCatalog.common.decommissioningRateBasis,
      discountRatePerPeriod,
      investmentCostsUSDByPeriod: baseInvestmentCostsUSD.map((baseCost) =>
        discountFactors.map((discountFactor, periodIndex) =>
          calculatePresentValueCost(
            calculateTimeAdjustedInvestmentCost(
              baseCost,
              fuelCostAdjustmentRatePerPeriod,
              periodIndex
            ),
            discountFactor
          )
        )
      ),
      maintenanceCostsUSDByPeriod: baseInvestmentCostsUSD.map((baseCost) =>
        discountFactors.map((discountFactor) =>
          calculatePresentValueCost(
            calculateMaintenanceCost(
              baseCost,
              maintenanceRatePerPlanningPeriod
            ),
            discountFactor
          )
        )
      ),
      decommissioningCostsUSDByPeriod: baseInvestmentCostsUSD.map((baseCost) =>
        discountFactors.map((discountFactor) =>
          calculatePresentValueCost(
            calculateDecommissioningCost(baseCost, decommissioningRate),
            discountFactor
          )
        )
      ),
    };
  });

  return payload;
}

module.exports = { buildTankCostPayload };
