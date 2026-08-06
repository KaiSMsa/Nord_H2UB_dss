import unittest

try:
    from ortools.linear_solver import pywraplp
    from model_tank_index import (
        build_facility_location_model,
        solve_facility_location,
    )
except ImportError:  # pragma: no cover - exercised only without solver dependency
    pywraplp = None


def model_payload(demand):
    periods = ['2025', '2030', '2035', '2040']
    base_cost = 10_000_000.1234567
    return {
        'T': periods,
        'Fuels': ['Test Fuel'],
        'Capacities': {'Test Fuel': [100]},
        'TankOptions': {
            'Test Fuel': [{
                'optimizerName': 'Test Fuel',
                'capacityMgoEquivalentTonnes': 100,
                'baseInvestmentCostUSD': base_cost,
            }],
        },
        'Demand': {
            'Test Fuel': dict(zip(periods, demand)),
        },
        'InitialState': {'Test Fuel': [[0]]},
        'discountRatePerPlanningPeriod': 0.071,
        'technologyCostAdjustmentRatePerPlanningPeriod': {
            'Test Fuel': -0.013,
        },
        'maintenanceRatePerPlanningPeriod': {'Test Fuel': 0.037},
        'decommissioningRateAtClosure': {'Test Fuel': 0.123},
    }


@unittest.skipIf(pywraplp is None, 'OR-Tools is unavailable')
class TankIndexModelStructureTest(unittest.TestCase):
    def test_opening_and_maintenance_timing(self):
        payload = model_payload([0, 100, 100, 100])
        result = solve_facility_location(payload)

        self.assertIn(result['status'], (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE))
        solution = result['solution']['Test Fuel']
        self.assertEqual(solution['2030']['Tank_1'][100]['opened'], 1)
        self.assertEqual(solution['2035']['Tank_1'][100]['operating'], 1)
        self.assertEqual(solution['2040']['Tank_1'][100]['operating'], 1)
        self.assertEqual(result['costs']['Test Fuel']['2030']['Tank_1'][100]['operating'], 0.0)
        self.assertGreater(result['costs']['Test Fuel']['2035']['Tank_1'][100]['operating'], 0.0)

        model = build_facility_location_model(payload)
        y = model['variables']['y']
        objective = model['solver'].Objective()
        self.assertEqual(objective.GetCoefficient(y[0, 0, 0, 0]), 0.0)
        self.assertGreater(objective.GetCoefficient(y[0, 0, 0, 1]), 0.0)

    def test_decommissioning_is_charged_once_at_closure(self):
        result = solve_facility_location(model_payload([0, 100, 100, 0]))
        solution = result['solution']['Test Fuel']
        self.assertEqual(solution['2035']['Tank_1'][100]['operating'], 1)
        self.assertEqual(solution['2040']['Tank_1'][100]['closed'], 1)
        self.assertGreater(
            result['costs']['Test Fuel']['2040']['Tank_1'][100]['closed'],
            0.0,
        )

    def test_transition_variables_exclude_same_capacity_and_period_zero(self):
        payload = model_payload([0, 100, 100, 100])
        payload['Capacities']['Test Fuel'] = [100, 200]
        payload['TankOptions']['Test Fuel'].append({
            'optimizerName': 'Test Fuel',
            'capacityMgoEquivalentTonnes': 200,
            'baseInvestmentCostUSD': 15_000_000.7654321,
        })
        payload['InitialState']['Test Fuel'] = [[0, 0]]
        model = build_facility_location_model(payload)
        z = model['variables']['z']

        self.assertTrue(z)
        self.assertTrue(all(key[2] != key[3] for key in z))
        self.assertTrue(all(key[4] > 0 for key in z))


if __name__ == '__main__':
    unittest.main()
