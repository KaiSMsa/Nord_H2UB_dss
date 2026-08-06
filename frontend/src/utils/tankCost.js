const fuelParameterCatalog = require("../constants/fuelParameters.json");

const MGO_LOWER_HEATING_VALUE_MJ_PER_KG =
  fuelParameterCatalog.common.mgoLowerHeatingValueMJPerKg;

function requireFiniteNumber(value, argumentName) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new TypeError(`${argumentName} must be a finite number`);
  }
  return number;
}

function requirePositiveNumber(value, argumentName) {
  const number = requireFiniteNumber(value, argumentName);
  if (number <= 0) {
    throw new RangeError(`${argumentName} must be greater than zero`);
  }
  return number;
}

function getFuelParameters(fuelIdentifier) {
  const normalized = String(fuelIdentifier || "").toLowerCase();
  const fuel = fuelParameterCatalog.fuels.find((candidate) =>
    [
      candidate.id,
      candidate.displayName,
      candidate.optimizerName,
      candidate.abbreviation,
    ]
      .filter(Boolean)
      .some((alias) => alias.toLowerCase() === normalized)
  );

  if (!fuel) {
    throw new RangeError(`Unknown fuel: ${fuelIdentifier}`);
  }

  return fuel;
}

function calculatePhysicalFuelMass(
  capacityMgoEquivalentTonnes,
  fuelLowerHeatingValueMJPerKg
) {
  const capacity = requireFiniteNumber(
    capacityMgoEquivalentTonnes,
    "capacityMgoEquivalentTonnes"
  );
  const fuelLhv = requirePositiveNumber(
    fuelLowerHeatingValueMJPerKg,
    "fuelLowerHeatingValueMJPerKg"
  );

  return (capacity * MGO_LOWER_HEATING_VALUE_MJ_PER_KG) / fuelLhv;
}

function calculateStorageVolume(physicalMassTonnes, densityKgPerM3) {
  const mass = requireFiniteNumber(physicalMassTonnes, "physicalMassTonnes");
  const density = requirePositiveNumber(densityKgPerM3, "densityKgPerM3");
  return (mass * 1000) / density;
}

function calculateScaledShellCost(
  storageVolumeM3,
  shellCalibrationUSDPerM3,
  referenceVolumeM3,
  scalingExponent
) {
  const volume = requireFiniteNumber(storageVolumeM3, "storageVolumeM3");
  const calibration = requireFiniteNumber(
    shellCalibrationUSDPerM3,
    "shellCalibrationUSDPerM3"
  );
  const referenceVolume = requirePositiveNumber(
    referenceVolumeM3,
    "referenceVolumeM3"
  );
  const exponent = requireFiniteNumber(scalingExponent, "scalingExponent");

  return (
    calibration *
    referenceVolume *
    Math.pow(volume / referenceVolume, exponent)
  );
}

function calculateBaseInvestmentCost(
  fixedInstallationCostUSD,
  shellInstallationCostUSD
) {
  return (
    requireFiniteNumber(fixedInstallationCostUSD, "fixedInstallationCostUSD") +
    requireFiniteNumber(shellInstallationCostUSD, "shellInstallationCostUSD")
  );
}

function calculateMaintenanceCost(
  baseInvestmentCostUSD,
  maintenanceRateAnnual
) {
  return (
    requireFiniteNumber(baseInvestmentCostUSD, "baseInvestmentCostUSD") *
    requireFiniteNumber(
      maintenanceRateAnnual,
      "maintenanceRateAnnual"
    )
  );
}

function calculateDecommissioningCost(
  baseInvestmentCostUSD,
  decommissioningRateAtClosure
) {
  return (
    requireFiniteNumber(baseInvestmentCostUSD, "baseInvestmentCostUSD") *
    requireFiniteNumber(
      decommissioningRateAtClosure,
      "decommissioningRateAtClosure"
    )
  );
}

function calculateTimeAdjustedInvestmentCost(
  baseInvestmentCostUSD,
  technologyCostAdjustmentRateAnnual,
  elapsedYears
) {
  const baseCost = requireFiniteNumber(
    baseInvestmentCostUSD,
    "baseInvestmentCostUSD"
  );
  const rate = requireFiniteNumber(
    technologyCostAdjustmentRateAnnual,
    "technologyCostAdjustmentRateAnnual"
  );
  const years = requireFiniteNumber(elapsedYears, "elapsedYears");
  return baseCost * Math.pow(1 + rate, years);
}

function calculateDiscountFactor(discountRateAnnual, elapsedYears) {
  const rate = requireFiniteNumber(
    discountRateAnnual,
    "discountRateAnnual"
  );
  const years = requireFiniteNumber(elapsedYears, "elapsedYears");
  if (rate <= -1) {
    throw new RangeError("discountRateAnnual must be greater than -1");
  }
  if (years < 0) {
    throw new RangeError("elapsedYears must be greater than or equal to zero");
  }
  return 1 / Math.pow(1 + rate, years);
}

function calculatePresentValueCost(nominalPeriodCostUSD, discountFactor) {
  return (
    requireFiniteNumber(nominalPeriodCostUSD, "nominalPeriodCostUSD") *
    requireFiniteNumber(discountFactor, "discountFactor")
  );
}

function estimateTankOption(fuelIdentifier, capacityMgoEquivalentTonnes) {
  const fuel = getFuelParameters(fuelIdentifier);
  const capacity = requireFiniteNumber(
    capacityMgoEquivalentTonnes,
    "capacityMgoEquivalentTonnes"
  );
  const common = fuelParameterCatalog.common;
  const validationWarnings = [];

  if (capacity < fuel.minimumCapacityMgoEquivalentTonnes) {
    validationWarnings.push(
      `Capacity is below the minimum of ${fuel.minimumCapacityMgoEquivalentTonnes} t MGO-e.`
    );
  }
  if (capacity > fuel.maximumCapacityMgoEquivalentTonnes) {
    validationWarnings.push(
      `Capacity is above the maximum of ${fuel.maximumCapacityMgoEquivalentTonnes} t MGO-e.`
    );
  }

  const physicalMassTonnes = calculatePhysicalFuelMass(
    capacity,
    fuel.lowerHeatingValueMJPerKg
  );
  const storageVolumeM3 = calculateStorageVolume(
    physicalMassTonnes,
    fuel.densityKgPerM3
  );
  const shellInstallationCostUSD = calculateScaledShellCost(
    storageVolumeM3,
    fuel.shellCalibrationUSDPerM3,
    common.referenceVolumeM3,
    common.scalingExponent
  );
  const investmentCostUSD = calculateBaseInvestmentCost(
    fuel.fixedInstallationCostUSD,
    shellInstallationCostUSD
  );

  return {
    fuelId: fuel.id,
    fuelName: fuel.displayName,
    optimizerName: fuel.optimizerName || fuel.displayName,
    capacityMgoEquivalentTonnes: capacity,
    mgoLowerHeatingValueMJPerKg: MGO_LOWER_HEATING_VALUE_MJ_PER_KG,
    fuelLowerHeatingValueMJPerKg: fuel.lowerHeatingValueMJPerKg,
    densityKgPerM3: fuel.densityKgPerM3,
    physicalMassTonnes,
    storageVolumeM3,
    fixedInstallationCostUSD: fuel.fixedInstallationCostUSD,
    shellCalibrationUSDPerM3: fuel.shellCalibrationUSDPerM3,
    referenceVolumeM3: common.referenceVolumeM3,
    scalingExponent: common.scalingExponent,
    shellInstallationCostUSD,
    investmentCostUSD,
    baseInvestmentCostUSD: investmentCostUSD,
    minimumCapacityMgoEquivalentTonnes:
      fuel.minimumCapacityMgoEquivalentTonnes,
    maximumCapacityMgoEquivalentTonnes:
      fuel.maximumCapacityMgoEquivalentTonnes,
    validationWarnings,
  };
}

module.exports = {
  MGO_LOWER_HEATING_VALUE_MJ_PER_KG,
  fuelParameterCatalog,
  getFuelParameters,
  calculatePhysicalFuelMass,
  calculateStorageVolume,
  calculateScaledShellCost,
  calculateBaseInvestmentCost,
  calculateMaintenanceCost,
  calculateDecommissioningCost,
  calculateTimeAdjustedInvestmentCost,
  calculateDiscountFactor,
  calculatePresentValueCost,
  estimateTankOption,
};
