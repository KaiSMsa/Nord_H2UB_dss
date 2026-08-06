function roundUSDToNearestThousand(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return 0;
  return Math.round(amount / 1000) * 1000;
}

function formatUSDToNearestThousand(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(roundUSDToNearestThousand(value));
}

function formatUSDWithoutDecimals(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "0";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

module.exports = {
  roundUSDToNearestThousand,
  formatUSDToNearestThousand,
  formatUSDWithoutDecimals,
};
