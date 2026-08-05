import copy
import math
import unittest

from financial_parameters import (
    calculate_transition_cost_usd,
    prepare_financial_costs_for_model,
)


BASE_COST = 12_004_383.921677316


def valid_payload():
    option = {
        'optimizerName': 'Ammonia',
        'capacityMgoEquivalentTonnes': 3000,
        'baseInvestmentCostUSD': BASE_COST,
    }
    return {
        'T': ['2025', '2030', '2035', '2040'],
        'Fuels': ['Ammonia'],
        'Capacities': {'Ammonia': [3000]},
        'TankOptions': {'Ammonia': [option]},
        'discountRatePerPlanningPeriod': 0.05,
        'technologyCostAdjustmentRatePerPlanningPeriod': {'Ammonia': -0.02},
        'maintenanceRatePerPlanningPeriod': {'Ammonia': 0.04},
        'decommissioningRateAtClosure': {'Ammonia': 0.10},
    }


class FinancialParameterContractTest(unittest.TestCase):
    def test_frontend_rates_prepare_full_precision_period_coefficients(self):
        prepared = prepare_financial_costs_for_model(valid_payload())['Ammonia']

        self.assertEqual(prepared['discountRatePerPlanningPeriod'], 0.05)
        self.assertEqual(
            prepared['technologyCostAdjustmentRatePerPlanningPeriod'],
            -0.02,
        )
        self.assertEqual(prepared['maintenanceRatePerPlanningPeriod'], 0.04)
        self.assertEqual(prepared['decommissioningRateAtClosure'], 0.10)
        for period_index in range(4):
            discount_factor = 1 / (1.05 ** period_index)
            self.assertEqual(
                prepared['discountFactorsByPeriod'][period_index],
                discount_factor,
            )
            self.assertEqual(
                prepared['investmentCostsUSDByPeriod'][0][period_index],
                BASE_COST * (0.98 ** period_index) * discount_factor,
            )
            self.assertEqual(
                prepared['maintenanceCostsUSDByPeriod'][0][period_index],
                BASE_COST * 0.04 * discount_factor,
            )
            self.assertEqual(
                prepared['decommissioningCostsUSDByPeriod'][0][period_index],
                BASE_COST * 0.10 * discount_factor,
            )

    def test_transition_uses_period_present_value_costs_once(self):
        payload = valid_payload()
        second_option = copy.deepcopy(payload['TankOptions']['Ammonia'][0])
        second_option['capacityMgoEquivalentTonnes'] = 5000
        second_option['baseInvestmentCostUSD'] = BASE_COST * 1.5
        payload['TankOptions']['Ammonia'].append(second_option)
        payload['Capacities']['Ammonia'].append(5000)
        prepared = prepare_financial_costs_for_model(payload)['Ammonia']
        period_index = 2
        transition = calculate_transition_cost_usd(
            prepared['investmentCostsUSDByPeriod'][0][period_index],
            prepared['investmentCostsUSDByPeriod'][1][period_index],
        )
        expected = abs(
            1.2
            * (BASE_COST - BASE_COST * 1.5)
            * (0.98 ** period_index)
            / (1.05 ** period_index)
        )
        self.assertAlmostEqual(transition, expected, places=8)

    def test_valid_zero_rates_are_not_replaced(self):
        payload = valid_payload()
        payload['discountRatePerPlanningPeriod'] = 0
        for field in (
            'technologyCostAdjustmentRatePerPlanningPeriod',
            'maintenanceRatePerPlanningPeriod',
            'decommissioningRateAtClosure',
        ):
            payload[field]['Ammonia'] = 0
        prepared = prepare_financial_costs_for_model(payload)['Ammonia']
        self.assertEqual(prepared['discountRatePerPlanningPeriod'], 0)
        self.assertEqual(
            prepared['technologyCostAdjustmentRatePerPlanningPeriod'],
            0,
        )
        self.assertEqual(prepared['maintenanceRatePerPlanningPeriod'], 0)
        self.assertEqual(prepared['decommissioningRateAtClosure'], 0)

    def test_rejects_missing_non_numeric_infinite_and_nan_rates(self):
        missing_discount = valid_payload()
        del missing_discount['discountRatePerPlanningPeriod']
        with self.assertRaisesRegex(ValueError, 'is required'):
            prepare_financial_costs_for_model(missing_discount)

        for invalid_value in ('5', None, math.inf, -math.inf, math.nan):
            invalid = valid_payload()
            invalid['discountRatePerPlanningPeriod'] = invalid_value
            with self.assertRaises(ValueError):
                prepare_financial_costs_for_model(invalid)

        for field in (
            'technologyCostAdjustmentRatePerPlanningPeriod',
            'maintenanceRatePerPlanningPeriod',
            'decommissioningRateAtClosure',
        ):
            missing = valid_payload()
            del missing[field]['Ammonia']
            with self.assertRaisesRegex(ValueError, 'is required'):
                prepare_financial_costs_for_model(missing)

            for invalid_value in ('5', None, math.inf, -math.inf, math.nan):
                invalid = valid_payload()
                invalid[field]['Ammonia'] = invalid_value
                with self.assertRaises(ValueError):
                    prepare_financial_costs_for_model(invalid)

    def test_rejects_rates_outside_allowed_ranges(self):
        invalid_cases = (
            ('discountRatePerPlanningPeriod', -1),
            ('technologyCostAdjustmentRatePerPlanningPeriod', -1),
            ('maintenanceRatePerPlanningPeriod', -0.01),
            ('decommissioningRateAtClosure', -0.01),
        )
        for field, value in invalid_cases:
            payload = valid_payload()
            if field == 'discountRatePerPlanningPeriod':
                payload[field] = value
            else:
                payload[field]['Ammonia'] = value
            with self.assertRaises(ValueError):
                prepare_financial_costs_for_model(payload)

    def test_rejects_non_numeric_tank_option_base_cost(self):
        payload = valid_payload()
        payload['TankOptions']['Ammonia'][0]['baseInvestmentCostUSD'] = 'invalid'
        with self.assertRaisesRegex(ValueError, 'must be a numeric value'):
            prepare_financial_costs_for_model(payload)

    def test_rejects_client_generated_period_cost_matrices(self):
        for field in (
            'discountFactorsByPeriod',
            'investmentCostsUSDByPeriod',
            'maintenanceCostsUSDByPeriod',
            'decommissioningCostsUSDByPeriod',
        ):
            payload = valid_payload()
            payload['Costs'] = {'Ammonia': {field: [[1, 2, 3, 4]]}}
            with self.assertRaisesRegex(ValueError, 'must not be supplied'):
                prepare_financial_costs_for_model(payload)


if __name__ == '__main__':
    unittest.main()
