import copy
import math
import unittest

from financial_parameters import (
    calculate_decommissioning_cost_coefficient,
    calculate_discount_factor,
    calculate_elapsed_years,
    calculate_maintenance_cost_coefficient,
    calculate_opening_cost_coefficient,
    calculate_transition_cost_coefficient,
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
        'planningPeriodYears': 5,
        'discountRateAnnual': 0.071,
        'transitionCostRate': 1.2,
        'technologyCostAdjustmentRateAnnual': {'Ammonia': -0.013},
        'maintenanceRateAnnual': {'Ammonia': 0.037},
        'decommissioningRateAtClosure': {'Ammonia': 0.123},
    }


class FinancialParameterContractTest(unittest.TestCase):
    def test_period_two_uses_ten_elapsed_years(self):
        self.assertEqual(calculate_elapsed_years(5, 2), 10)
        self.assertEqual(
            calculate_discount_factor(0.071, 5, 2),
            1 / (1.071 ** 10),
        )

    def test_annual_coefficients(self):
        prepared = prepare_financial_costs_for_model(valid_payload())['Ammonia']
        for period_index in range(4):
            elapsed_years = 5 * period_index
            discount_factor = 1 / (1.071 ** elapsed_years)
            self.assertEqual(
                prepared['discountFactorsByPeriod'][period_index],
                discount_factor,
            )
            self.assertAlmostEqual(
                prepared['openingCostCoefficientsUSD'][0][period_index],
                BASE_COST * (0.987 ** elapsed_years) * discount_factor,
                places=9,
            )
            self.assertAlmostEqual(
                prepared['maintenanceCostCoefficientsUSD'][0][period_index],
                5 * BASE_COST * 0.037 * discount_factor,
                places=9,
            )
            self.assertAlmostEqual(
                prepared['decommissioningCostCoefficientsUSD'][0][period_index],
                BASE_COST * 0.123 * discount_factor,
                places=9,
            )

    def test_helper_formulas_use_annual_rates(self):
        period_index = 2
        discount_factor = 1 / (1.071 ** 10)
        self.assertAlmostEqual(
            calculate_opening_cost_coefficient(
                BASE_COST, -0.013, 0.071, 5, period_index
            ),
            BASE_COST * (0.987 ** 10) * discount_factor,
            places=9,
        )
        self.assertAlmostEqual(
            calculate_maintenance_cost_coefficient(
                BASE_COST, 0.037, 0.071, 5, period_index
            ),
            5 * BASE_COST * 0.037 * discount_factor,
            places=9,
        )
        self.assertAlmostEqual(
            calculate_decommissioning_cost_coefficient(
                BASE_COST, 0.123, 0.071, 5, period_index
            ),
            BASE_COST * 0.123 * discount_factor,
            places=9,
        )

    def test_transition_uses_adjusted_costs_then_discounting(self):
        payload = valid_payload()
        second_option = copy.deepcopy(payload['TankOptions']['Ammonia'][0])
        second_option['capacityMgoEquivalentTonnes'] = 5000
        second_option['baseInvestmentCostUSD'] = BASE_COST * 1.5
        payload['TankOptions']['Ammonia'].append(second_option)
        payload['Capacities']['Ammonia'].append(5000)
        prepared = prepare_financial_costs_for_model(payload)['Ammonia']
        period_index = 2
        expected = (
            1.2
            * abs(BASE_COST * 1.5 - BASE_COST)
            * (0.987 ** 10)
            / (1.071 ** 10)
        )
        calculated = calculate_transition_cost_coefficient(
            BASE_COST,
            BASE_COST * 1.5,
            1.2,
            -0.013,
            0.071,
            5,
            period_index,
        )
        self.assertAlmostEqual(calculated, expected, places=8)
        self.assertIsNone(prepared['transitionCostCoefficientsUSD'][0][1][0])
        self.assertAlmostEqual(
            prepared['transitionCostCoefficientsUSD'][0][1][period_index],
            expected,
            places=8,
        )

    def test_valid_zero_rates_are_not_replaced(self):
        payload = valid_payload()
        payload['discountRateAnnual'] = 0
        payload['transitionCostRate'] = 0
        payload['technologyCostAdjustmentRateAnnual']['Ammonia'] = 0
        payload['maintenanceRateAnnual']['Ammonia'] = 0
        payload['decommissioningRateAtClosure']['Ammonia'] = 0
        prepared = prepare_financial_costs_for_model(payload)['Ammonia']
        self.assertEqual(prepared['discountRateAnnual'], 0)
        self.assertEqual(prepared['transitionCostRate'], 0)
        self.assertEqual(prepared['technologyCostAdjustmentRateAnnual'], 0)
        self.assertEqual(prepared['maintenanceRateAnnual'], 0)
        self.assertEqual(prepared['decommissioningRateAtClosure'], 0)

    def test_missing_non_numeric_boolean_infinite_and_nan_are_rejected(self):
        scalar_fields = (
            'planningPeriodYears',
            'discountRateAnnual',
            'transitionCostRate',
        )
        mapping_fields = (
            'technologyCostAdjustmentRateAnnual',
            'maintenanceRateAnnual',
            'decommissioningRateAtClosure',
        )
        for field in scalar_fields:
            missing = valid_payload()
            del missing[field]
            with self.assertRaises(ValueError):
                prepare_financial_costs_for_model(missing)
            for invalid in (True, False, '5', None, math.inf, -math.inf, math.nan):
                payload = valid_payload()
                payload[field] = invalid
                with self.assertRaises(ValueError):
                    prepare_financial_costs_for_model(payload)

        for field in mapping_fields:
            missing = valid_payload()
            del missing[field]['Ammonia']
            with self.assertRaisesRegex(ValueError, 'is required'):
                prepare_financial_costs_for_model(missing)
            for invalid in (True, False, '5', None, math.inf, -math.inf, math.nan):
                payload = valid_payload()
                payload[field]['Ammonia'] = invalid
                with self.assertRaises(ValueError):
                    prepare_financial_costs_for_model(payload)

    def test_incoherent_values_are_rejected(self):
        cases = (
            ('planningPeriodYears', 0),
            ('discountRateAnnual', -1),
            ('transitionCostRate', -0.01),
        )
        for field, value in cases:
            payload = valid_payload()
            payload[field] = value
            with self.assertRaises(ValueError):
                prepare_financial_costs_for_model(payload)
        for field, value in (
            ('technologyCostAdjustmentRateAnnual', -1),
            ('maintenanceRateAnnual', -0.01),
            ('decommissioningRateAtClosure', -0.01),
        ):
            payload = valid_payload()
            payload[field]['Ammonia'] = value
            with self.assertRaises(ValueError):
                prepare_financial_costs_for_model(payload)

    def test_legacy_period_rate_fields_are_rejected_clearly(self):
        for field in (
            'discountRatePerPlanningPeriod',
            'technologyCostAdjustmentRatePerPlanningPeriod',
            'maintenanceRatePerPlanningPeriod',
        ):
            payload = valid_payload()
            payload[field] = 0
            with self.assertRaisesRegex(ValueError, 'Legacy planning-period'):
                prepare_financial_costs_for_model(payload)

    def test_base_cost_and_client_cost_matrices_are_rejected(self):
        payload = valid_payload()
        payload['TankOptions']['Ammonia'][0]['baseInvestmentCostUSD'] = -1
        with self.assertRaisesRegex(ValueError, 'non-negative'):
            prepare_financial_costs_for_model(payload)

        payload = valid_payload()
        payload['Costs'] = {'Ammonia': {'openingCostCoefficientsUSD': [[1]]}}
        with self.assertRaisesRegex(ValueError, 'must not be supplied'):
            prepare_financial_costs_for_model(payload)


if __name__ == '__main__':
    unittest.main()
