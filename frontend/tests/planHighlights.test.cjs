const test = require("node:test");
const assert = require("node:assert/strict");

const {
  buildPlanHighlights,
  buildTankDisplayNames,
} = require("../src/utils/planHighlights.js");

const years = ["2025", "2030", "2035", "2040", "2045", "2050"];

test("summarizes initial operation, expansion, and decommissioning", () => {
  const schedule = {
    MGO: {
      "2025": { Tank_1: { 10000: { opened: 1 } } },
      "2030": { Tank_1: { 10000: { operating: 1 } } },
      "2050": { Tank_1: { 10000: { closed: 1 } } },
    },
    Ammonia: {
      "2035": { Tank_1: { 1000: { opened: 1 } } },
      "2040": { Tank_1: { 5000: { operating: 1 } } },
    },
  };

  assert.deepEqual(buildPlanHighlights(schedule, years), [
    "MGO - Tank 1 operates from 2025 and is decommissioned in 2050.",
    "Ammonia - Tank 1 is opened in 2035 and is expanded in 2040.",
  ]);
});

test("numbers tanks by first active year and describes capacity reductions", () => {
  const schedule = {
    Ammonia: {
      "2035": {
        Tank_10: { 5000: { opened: 1 } },
      },
      "2040": {
        Tank_10: { 1000: { operating: 1 } },
        Tank_2: { 5000: { opened: 1 } },
      },
      "2045": {
        Tank_2: { 5000: { operating: 1 } },
      },
    },
  };

  assert.deepEqual(buildTankDisplayNames(schedule, years), {
    Ammonia: { Tank_10: "Tank 1", Tank_2: "Tank 2" },
  });
  assert.deepEqual(buildPlanHighlights(schedule, years), [
    "Ammonia - Tank 1 is opened in 2035 and is reduced in 2040.",
    "Ammonia - Tank 2 is opened in 2040.",
  ]);
});
