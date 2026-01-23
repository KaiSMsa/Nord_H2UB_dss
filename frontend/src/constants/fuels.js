export const FUELS = [
  { key: "MGO", name: "MGO", class: "fuel-color-mgo", color: "#007bff" },
  { key: "LH2", name: "Liquid Hydrogen", class: "fuel-color-lh2", color: "#28a745" },
  { key: "CH2", name: "Compressed Hydrogen", class: "fuel-color-ch2", color: "#17a2b8" },
  { key: "NH3", name: "Ammonia", class: "fuel-color-ammonia", color: "#ffc107" },
  { key: "MEOH", name: "Methanol", class: "fuel-color-methanol", color: "#dc3545" },
  { key: "LNG", name: "LNG", class: "fuel-color-lng", color: "#6f42c1" },
];

export const FUEL_BY_NAME = Object.fromEntries(FUELS.map(f => [f.name, f]));
export const FUEL_COLORS_BY_NAME = Object.fromEntries(FUELS.map(f => [f.name, f.color]));