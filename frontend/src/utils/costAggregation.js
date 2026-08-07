function sumTransitionCostsForFuelYear(transitions, fuel, year) {
  const tankTransitions = transitions?.[fuel]?.[year];
  if (!tankTransitions) return 0;

  return Object.values(tankTransitions).reduce((fuelYearTotal, entries) => {
    if (!Array.isArray(entries)) return fuelYearTotal;
    return fuelYearTotal + entries.reduce(
      (tankTotal, transition) => tankTotal + (Number(transition?.costUSD) || 0),
      0
    );
  }, 0);
}

function aggregateFuelYearCosts(costs, transitions, fuel, year) {
  let opening = 0;
  let operating = 0;
  let decommissioning = 0;
  const fuelYearCosts = costs?.[fuel]?.[year];

  if (fuelYearCosts) {
    Object.values(fuelYearCosts).forEach((tank) => {
      Object.values(tank).forEach((cost) => {
        opening += Number(cost.opened) || 0;
        operating += Number(cost.operating) || 0;
        decommissioning += Number(cost.closed) || 0;
      });
    });
  }

  const transition = sumTransitionCostsForFuelYear(
    transitions,
    fuel,
    year
  );
  return {
    total: opening + operating + decommissioning + transition,
    opening,
    operating,
    decommissioning,
    transition,
  };
}

module.exports = {
  aggregateFuelYearCosts,
  sumTransitionCostsForFuelYear,
};
