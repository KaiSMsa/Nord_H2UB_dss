function tankNumber(tankId) {
  const match = String(tankId).match(/(\d+)/);
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
}

function joinActions(actions) {
  if (actions.length === 1) return actions[0];
  if (actions.length === 2) return `${actions[0]} and ${actions[1]}`;
  return `${actions.slice(0, -1).join(", ")}, and ${actions.at(-1)}`;
}

function readTankState(tank) {
  let activeCapacity = null;
  let isClosed = false;

  Object.entries(tank || {}).forEach(([capacity, status]) => {
    if (status?.opened || status?.operating) {
      activeCapacity = Number(capacity);
    }
    if (status?.closed) isClosed = true;
  });

  return { activeCapacity, isClosed };
}

function firstActiveYearIndex(fuelSchedule, tankId, years) {
  const activeIndex = years.findIndex((year) => {
    const { activeCapacity } = readTankState(fuelSchedule?.[year]?.[tankId]);
    return activeCapacity !== null;
  });
  if (activeIndex >= 0) return activeIndex;

  const firstSeenIndex = years.findIndex(
    (year) => fuelSchedule?.[year]?.[tankId]
  );
  return firstSeenIndex >= 0 ? firstSeenIndex : Number.MAX_SAFE_INTEGER;
}

function getOrderedTankIds(fuelSchedule, years) {
  return [...new Set(
    years.flatMap((year) => Object.keys(fuelSchedule?.[year] || {}))
  )].sort((left, right) => {
    const yearDifference =
      firstActiveYearIndex(fuelSchedule, left, years)
      - firstActiveYearIndex(fuelSchedule, right, years);
    return yearDifference || tankNumber(left) - tankNumber(right);
  });
}

function buildTankDisplayNames(schedule, years) {
  const names = {};

  Object.entries(schedule || {}).forEach(([fuel, fuelSchedule]) => {
    const tankIds = getOrderedTankIds(fuelSchedule, years);

    names[fuel] = Object.fromEntries(
      tankIds.map((tankId, index) => [tankId, `Tank ${index + 1}`])
    );
  });

  return names;
}

function buildTankHighlight(
  fuel,
  tankId,
  displayName,
  fuelSchedule,
  years,
  firstYear
) {
  const actions = [];
  let previousCapacity = null;
  let hasOperated = false;

  years.forEach((year) => {
    const tank = fuelSchedule?.[year]?.[tankId];
    if (!tank) return;

    const { activeCapacity, isClosed } = readTankState(tank);
    if (activeCapacity !== null) {
      if (!hasOperated) {
        actions.push(
          year === firstYear
            ? `operates from ${year}`
            : `is opened in ${year}`
        );
        hasOperated = true;
      } else if (activeCapacity > previousCapacity) {
        actions.push(`is expanded in ${year}`);
      } else if (activeCapacity < previousCapacity) {
        actions.push(`is reduced in ${year}`);
      }
      previousCapacity = activeCapacity;
    }

    if (isClosed) actions.push(`is decommissioned in ${year}`);
  });

  if (!actions.length) return null;
  return `${fuel} - ${displayName} ${joinActions(actions)}.`;
}

function buildPlanHighlights(schedule, planningYears = []) {
  if (!schedule || typeof schedule !== "object") return [];

  const years = planningYears.length
    ? planningYears.map(String)
    : [...new Set(
      Object.values(schedule).flatMap((fuelSchedule) =>
        Object.keys(fuelSchedule || {})
      )
    )].sort((left, right) => Number(left) - Number(right));
  const firstYear = years[0];
  const highlights = [];
  const displayNames = buildTankDisplayNames(schedule, years);

  Object.entries(schedule).forEach(([fuel, fuelSchedule]) => {
    const tankIds = Object.keys(displayNames[fuel] || {});

    tankIds.forEach((tankId) => {
      const highlight = buildTankHighlight(
        fuel,
        tankId,
        displayNames[fuel][tankId],
        fuelSchedule,
        years,
        firstYear
      );
      if (highlight) highlights.push(highlight);
    });
  });

  return highlights;
}

module.exports = {
  buildPlanHighlights,
  buildTankDisplayNames,
  getOrderedTankIds,
};
