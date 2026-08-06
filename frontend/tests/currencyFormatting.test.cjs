const test = require("node:test");
const assert = require("node:assert/strict");

const {
  formatUSDWithoutDecimals,
  formatUSDToNearestThousand,
  roundUSDToNearestThousand,
} = require("../src/utils/currencyFormatting.js");

test("result monetary presentation rounds to the nearest USD 1,000", () => {
  assert.equal(roundUSDToNearestThousand(1_234_499.99), 1_234_000);
  assert.equal(roundUSDToNearestThousand(1_234_500), 1_235_000);
  assert.equal(formatUSDToNearestThousand(1_234_500), "1,235,000");
});

test("tank-capacity estimates show the full value without decimals", () => {
  assert.equal(formatUSDWithoutDecimals(1_234_499.49), "1,234,499");
  assert.equal(formatUSDWithoutDecimals(1_234_499.5), "1,234,500");
});
