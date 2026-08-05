const test = require("node:test");
const assert = require("node:assert/strict");

const {
  formatUSDToNearestThousand,
  roundUSDToNearestThousand,
} = require("../src/utils/currencyFormatting.js");

test("monetary presentation rounds only to the nearest USD 1,000", () => {
  assert.equal(roundUSDToNearestThousand(1_234_499.99), 1_234_000);
  assert.equal(roundUSDToNearestThousand(1_234_500), 1_235_000);
  assert.equal(formatUSDToNearestThousand(1_234_500), "1,235,000");
});
