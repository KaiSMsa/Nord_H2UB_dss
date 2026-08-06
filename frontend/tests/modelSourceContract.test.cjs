const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const modelSource = fs.readFileSync(
  path.resolve(__dirname, "../../backend/model_tank_index.py"),
  "utf8"
);
const coefficientSource = fs.readFileSync(
  path.resolve(__dirname, "../../backend/financial_parameters.py"),
  "utf8"
);

test("active model structurally follows period-zero and state-variable timing", () => {
  assert.match(modelSource, /for period_index in range\(1, len\(periods\)\):/);
  assert.match(modelSource, /maintenanceCostCoefficientsUSD'[\s\S]*\* s\[/);
  assert.match(modelSource, /decommissioningCostCoefficientsUSD'[\s\S]*\* x\[/);
  assert.match(modelSource, /initial_opening/);
  assert.match(modelSource, /initial_operating/);
  assert.match(modelSource, /initial_closure/);
  assert.doesNotMatch(modelSource, /fuel == ["']MGO["']/);
});

test("active model contains every required structural constraint", () => {
  for (const constraintName of [
    "demand[",
    "operational[",
    "single_opening[",
    "single_capacity[",
    "transition_lb[",
    "transition_ub1[",
    "transition_ub2[",
    "permanent_zero_demand[",
    "decommissioning_validity[",
  ]) {
    assert.ok(modelSource.includes(constraintName), constraintName);
  }
});

test("backend owns all four full-precision period coefficient formulas", () => {
  for (const functionName of [
    "calculate_discount_factor",
    "calculate_opening_cost_coefficient",
    "calculate_maintenance_cost_coefficient",
    "calculate_decommissioning_cost_coefficient",
    "calculate_transition_cost_coefficient",
    "prepare_financial_costs_for_model",
  ]) {
    assert.ok(coefficientSource.includes(`def ${functionName}(`), functionName);
  }
  assert.match(coefficientSource, /transition_cost_multiplier=1\.2/);
});
