import copy
import unittest

from model_tank_index import validate_tank_option_contract


def valid_payload():
    option = {
        'optimizerName': 'Ammonia',
        'capacityMgoEquivalentTonnes': 3000,
        'baseInvestmentCostUSD': 12004383.921677316,
    }
    return {
        'T': ['2025', '2030'],
        'Fuels': ['Ammonia'],
        'Capacities': {'Ammonia': [3000]},
        'TankOptions': {'Ammonia': [option]},
        'Costs': {
            'Ammonia': {
                'baseInvestmentCostsUSD': [12004383.921677316],
                'investmentCostsUSDByPeriod': [[12004383.921677316, 11764296.24324377]],
                'maintenanceCostsUSDByPeriod': [[480175.35686709266, 480175.35686709266]],
                'decommissioningCostsUSDByPeriod': [[1200438.3921677317, 1200438.3921677317]],
            }
        },
    }


class TankOptionContractTest(unittest.TestCase):
    def test_accepts_identical_frontend_and_optimizer_base_cost(self):
        validate_tank_option_contract(valid_payload())

    def test_rejects_modified_optimizer_base_cost(self):
        payload = copy.deepcopy(valid_payload())
        payload['Costs']['Ammonia']['baseInvestmentCostsUSD'][0] += 1
        with self.assertRaisesRegex(ValueError, 'base investment cost'):
            validate_tank_option_contract(payload)

    def test_rejects_missing_period_cost(self):
        payload = copy.deepcopy(valid_payload())
        payload['Costs']['Ammonia']['investmentCostsUSDByPeriod'][0].pop()
        with self.assertRaisesRegex(ValueError, 'period count'):
            validate_tank_option_contract(payload)


if __name__ == '__main__':
    unittest.main()
