const test = require("node:test");
const assert = require("node:assert/strict");

const {
  aggregateFuelYearCosts,
  sumTransitionCostsForFuelYear,
} = require("../src/utils/costAggregation.js");

const costs = {
  MGO: {
    "2030": {
      Tank_1: {
        2000: { opened: 100, operating: 20, closed: 0 },
      },
      Tank_2: {
        5000: { opened: 0, operating: 30, closed: 40 },
      },
    },
  },
};
const transitions = {
  MGO: {
    "2030": {
      Tank_1: [{ fromCapacity: 2000, toCapacity: 5000, costUSD: 50 }],
      Tank_2: [{ fromCapacity: 5000, toCapacity: 2000, costUSD: 60 }],
    },
  },
};

test("transition costs aggregate expansion and reduction events", () => {
  assert.equal(sumTransitionCostsForFuelYear(transitions, "MGO", "2030"), 110);
  assert.deepEqual(
    aggregateFuelYearCosts(costs, transitions, "MGO", "2030"),
    {
      total: 300,
      opening: 100,
      operating: 50,
      decommissioning: 40,
      transition: 110,
    }
  );
});

test("missing transitions contribute zero", () => {
  assert.equal(sumTransitionCostsForFuelYear({}, "MGO", "2030"), 0);
  assert.equal(
    aggregateFuelYearCosts(costs, {}, "MGO", "2030").transition,
    0
  );
});
