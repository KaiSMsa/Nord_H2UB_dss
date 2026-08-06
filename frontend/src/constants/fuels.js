import fuelParameterCatalog from "./fuelParameters.json";

const PRESENTATION_BY_ID = {
  mgo: { class: "fuel-color-mgo", color: "#007bff" },
  "liquid-hydrogen": { class: "fuel-color-lh2", color: "#28a745" },
  "compressed-hydrogen": { class: "fuel-color-ch2", color: "#17a2b8" },
  ammonia: { class: "fuel-color-ammonia", color: "#ffc107" },
  methanol: { class: "fuel-color-methanol", color: "#dc3545" },
  lng: { class: "fuel-color-lng", color: "#6f42c1" },
};

export const FUELS = fuelParameterCatalog.fuels.map((fuel) => ({
  key: fuel.abbreviation,
  id: fuel.id,
  name: fuel.optimizerName || fuel.displayName,
  displayName: fuel.displayName,
  abbreviation: fuel.abbreviation,
  operationalEmissionFactorTonnesCO2ePerTonneMgoEquivalent:
    fuel.operationalEmissionFactorTonnesCO2ePerTonneMgoEquivalent,
  ...PRESENTATION_BY_ID[fuel.id],
}));

export const FUEL_BY_NAME = Object.fromEntries(FUELS.map(f => [f.name, f]));
export const FUEL_COLORS_BY_NAME = Object.fromEntries(FUELS.map(f => [f.name, f.color]));
export const OPERATIONAL_EMISSION_FACTORS_BY_NAME = Object.freeze(
  Object.fromEntries(FUELS.map((fuel) => [
    fuel.name,
    fuel.operationalEmissionFactorTonnesCO2ePerTonneMgoEquivalent,
  ]))
);

export function createInitialFuelCapacitySelection() {
  const common = fuelParameterCatalog.common;

  return {
    discountRateAnnualPercent:
      common.defaultDiscountRateAnnual * 100,
    transitionCostRate: common.transitionCostRate,
    fuels: FUELS.map((fuelDefinition) => {
      const parameters = fuelParameterCatalog.fuels.find(
        (fuel) => fuel.id === fuelDefinition.id
      );

      return {
        id: parameters.id,
        name: fuelDefinition.name,
        class: fuelDefinition.class,
        rows: parameters.defaultCapacitiesMgoEquivalentTonnes.map((capacity) => ({
          capacity,
          storageVolume: 0,
          cost: 0,
        })),
        technologyCostAdjustmentRateAnnualPercent:
          common.defaultTechnologyCostAdjustmentRateAnnual * 100,
        maintenanceRateAnnualPercent: common.maintenanceRateAnnual * 100,
        decommissioningRateAtClosurePercent:
          common.decommissioningRateAtClosure * 100,
      };
    }),
  };
}
