import json
import math
import sys


RATE_FIELDS = (
    'discountRatePerPlanningPeriod',
    'technologyCostAdjustmentRatePerPlanningPeriod',
    'maintenanceRatePerPlanningPeriod',
    'decommissioningRateAtClosure',
)


def _require_finite_number(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field_name} must be a numeric value')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{field_name} must be finite')
    return number


def calculate_discount_factor(discount_rate_per_planning_period, period_index):
    rate = _require_finite_number(
        discount_rate_per_planning_period,
        'discountRatePerPlanningPeriod',
    )
    period = _require_finite_number(period_index, 'periodIndex')
    if rate <= -1:
        raise ValueError('discountRatePerPlanningPeriod must be greater than -1')
    if period < 0 or not period.is_integer():
        raise ValueError('periodIndex must be a non-negative integer')
    return 1 / ((1 + rate) ** int(period))


def calculate_technology_adjusted_cost(
    base_cost,
    technology_cost_adjustment_rate_per_planning_period,
    period_index,
):
    cost = _require_finite_number(base_cost, 'baseInvestmentCostUSD')
    rate = _require_finite_number(
        technology_cost_adjustment_rate_per_planning_period,
        'technologyCostAdjustmentRatePerPlanningPeriod',
    )
    period = _require_finite_number(period_index, 'periodIndex')
    if rate <= -1:
        raise ValueError(
            'technologyCostAdjustmentRatePerPlanningPeriod must be greater than -1'
        )
    if period < 0 or not period.is_integer():
        raise ValueError('periodIndex must be a non-negative integer')
    return cost * ((1 + rate) ** int(period))


def calculate_present_value_cost(nominal_period_cost, discount_factor):
    cost = _require_finite_number(nominal_period_cost, 'nominalPeriodCostUSD')
    factor = _require_finite_number(discount_factor, 'discountFactor')
    return cost * factor


def calculate_transition_cost_usd(
    from_present_value_investment_cost,
    to_present_value_investment_cost,
    transition_cost_multiplier=1.2,
):
    from_cost = _require_finite_number(
        from_present_value_investment_cost,
        'fromPresentValueInvestmentCostUSD',
    )
    to_cost = _require_finite_number(
        to_present_value_investment_cost,
        'toPresentValueInvestmentCostUSD',
    )
    multiplier = _require_finite_number(
        transition_cost_multiplier,
        'transitionCostMultiplier',
    )
    return abs(multiplier * (from_cost - to_cost))


def _validate_rates(costs, fuel):
    for field in RATE_FIELDS:
        if field not in costs:
            raise ValueError(f'Costs.{fuel}.{field} is required')

    rates = {
        field: _require_finite_number(costs[field], f'Costs.{fuel}.{field}')
        for field in RATE_FIELDS
    }
    if rates['discountRatePerPlanningPeriod'] <= -1:
        raise ValueError(
            f'Costs.{fuel}.discountRatePerPlanningPeriod must be greater than -1'
        )
    if rates['technologyCostAdjustmentRatePerPlanningPeriod'] <= -1:
        raise ValueError(
            f'Costs.{fuel}.technologyCostAdjustmentRatePerPlanningPeriod must be greater than -1'
        )
    if rates['maintenanceRatePerPlanningPeriod'] < 0:
        raise ValueError(
            f'Costs.{fuel}.maintenanceRatePerPlanningPeriod must be non-negative'
        )
    if rates['decommissioningRateAtClosure'] < 0:
        raise ValueError(
            f'Costs.{fuel}.decommissioningRateAtClosure must be non-negative'
        )
    return rates


def prepare_financial_costs_for_model(data):
    if not isinstance(data, dict):
        raise ValueError('Optimization request must be a JSON object')
    periods = data.get('T')
    fuels = data.get('Fuels')
    if not isinstance(periods, list) or not periods:
        raise ValueError('T must be a non-empty planning-period list')
    if not isinstance(fuels, list) or not fuels:
        raise ValueError('Fuels must be a non-empty list')

    capacities_by_fuel = data.get('Capacities')
    options_by_fuel = data.get('TankOptions')
    costs_by_fuel = data.get('Costs')
    if not isinstance(capacities_by_fuel, dict):
        raise ValueError('Capacities is required')
    if not isinstance(options_by_fuel, dict):
        raise ValueError('TankOptions is required')
    if not isinstance(costs_by_fuel, dict):
        raise ValueError('Costs is required')

    prepared = {}
    for fuel in fuels:
        if fuel not in capacities_by_fuel or fuel not in options_by_fuel:
            raise ValueError(f'Missing tank options for {fuel}')
        if fuel not in costs_by_fuel or not isinstance(costs_by_fuel[fuel], dict):
            raise ValueError(f'Costs.{fuel} is required')

        capacities = capacities_by_fuel[fuel]
        options = options_by_fuel[fuel]
        costs = costs_by_fuel[fuel]
        if not isinstance(capacities, list):
            raise ValueError(f'Capacities.{fuel} must be a list')
        if not isinstance(options, list):
            raise ValueError(f'TankOptions.{fuel} must be a list')
        base_costs = costs.get('baseInvestmentCostsUSD')
        if not isinstance(base_costs, list):
            raise ValueError(f'Costs.{fuel}.baseInvestmentCostsUSD is required')
        if len(options) != len(capacities) or len(options) != len(base_costs):
            raise ValueError(f'Inconsistent tank-option array lengths for {fuel}')

        validated_base_costs = []
        for option_index, (option, capacity, base_cost) in enumerate(
            zip(options, capacities, base_costs)
        ):
            if not isinstance(option, dict):
                raise ValueError(
                    f'TankOptions.{fuel}[{option_index}] must be an object'
                )
            validated_base_cost = _require_finite_number(
                base_cost,
                f'Costs.{fuel}.baseInvestmentCostsUSD[{option_index}]',
            )
            if option.get('optimizerName') != fuel:
                raise ValueError(f'Inconsistent fuel identifier for {fuel}')
            if option.get('capacityMgoEquivalentTonnes') != capacity:
                raise ValueError(f'Inconsistent capacity for {fuel}')
            if option.get('baseInvestmentCostUSD') != base_cost:
                raise ValueError(f'Inconsistent base investment cost for {fuel}')
            validated_base_costs.append(validated_base_cost)

        rates = _validate_rates(costs, fuel)
        discount_factors = [
            calculate_discount_factor(
                rates['discountRatePerPlanningPeriod'],
                period_index,
            )
            for period_index in range(len(periods))
        ]

        investment_costs_by_period = []
        maintenance_costs_by_period = []
        decommissioning_costs_by_period = []
        for base_cost in validated_base_costs:
            investment_costs_by_period.append([
                calculate_present_value_cost(
                    calculate_technology_adjusted_cost(
                        base_cost,
                        rates['technologyCostAdjustmentRatePerPlanningPeriod'],
                        period_index,
                    ),
                    discount_factors[period_index],
                )
                for period_index in range(len(periods))
            ])
            maintenance_costs_by_period.append([
                calculate_present_value_cost(
                    base_cost * rates['maintenanceRatePerPlanningPeriod'],
                    discount_factor,
                )
                for discount_factor in discount_factors
            ])
            decommissioning_costs_by_period.append([
                calculate_present_value_cost(
                    base_cost * rates['decommissioningRateAtClosure'],
                    discount_factor,
                )
                for discount_factor in discount_factors
            ])

        prepared[fuel] = {
            **costs,
            **rates,
            'baseInvestmentCostsUSD': validated_base_costs,
            'discountFactorsByPeriod': discount_factors,
            'investmentCostsUSDByPeriod': investment_costs_by_period,
            'maintenanceCostsUSDByPeriod': maintenance_costs_by_period,
            'decommissioningCostsUSDByPeriod': decommissioning_costs_by_period,
        }

    return prepared


if __name__ == '__main__':
    try:
        request_data = json.loads(sys.stdin.read())
        print(json.dumps(prepare_financial_costs_for_model(request_data)))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({'error': 'validation_error', 'message': str(error)}))
        sys.exit(2)
