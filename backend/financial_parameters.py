import json
import math
import sys


FUEL_RATE_FIELDS = (
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


def calculate_opening_cost_coefficient(
    base_investment_cost_usd,
    technology_cost_adjustment_rate_per_planning_period,
    period_index,
    discount_factor,
):
    return calculate_present_value_cost(
        calculate_technology_adjusted_cost(
            base_investment_cost_usd,
            technology_cost_adjustment_rate_per_planning_period,
            period_index,
        ),
        discount_factor,
    )


def calculate_maintenance_cost_coefficient(
    base_investment_cost_usd,
    maintenance_rate_per_planning_period,
    discount_factor,
):
    base_cost = _require_finite_number(
        base_investment_cost_usd,
        'baseInvestmentCostUSD',
    )
    rate = _require_finite_number(
        maintenance_rate_per_planning_period,
        'maintenanceRatePerPlanningPeriod',
    )
    return calculate_present_value_cost(base_cost * rate, discount_factor)


def calculate_decommissioning_cost_coefficient(
    base_investment_cost_usd,
    decommissioning_rate_at_closure,
    discount_factor,
):
    base_cost = _require_finite_number(
        base_investment_cost_usd,
        'baseInvestmentCostUSD',
    )
    rate = _require_finite_number(
        decommissioning_rate_at_closure,
        'decommissioningRateAtClosure',
    )
    return calculate_present_value_cost(base_cost * rate, discount_factor)


def calculate_transition_cost_coefficient(
    from_base_investment_cost_usd,
    to_base_investment_cost_usd,
    technology_cost_adjustment_rate_per_planning_period,
    period_index,
    discount_factor,
    transition_cost_multiplier=1.2,
):
    from_cost = _require_finite_number(
        from_base_investment_cost_usd,
        'fromBaseInvestmentCostUSD',
    )
    to_cost = _require_finite_number(
        to_base_investment_cost_usd,
        'toBaseInvestmentCostUSD',
    )
    multiplier = _require_finite_number(
        transition_cost_multiplier,
        'transitionCostMultiplier',
    )
    adjusted_difference = calculate_technology_adjusted_cost(
        abs(to_cost - from_cost),
        technology_cost_adjustment_rate_per_planning_period,
        period_index,
    )
    return calculate_present_value_cost(
        multiplier * adjusted_difference,
        discount_factor,
    )


def _validate_discount_rate(data):
    field = 'discountRatePerPlanningPeriod'
    if field not in data:
        raise ValueError(f'{field} is required')
    rate = _require_finite_number(data[field], field)
    if rate <= -1:
        raise ValueError(f'{field} must be greater than -1')
    return rate


def _validate_fuel_rates(data, fuel):
    rates = {}
    for field in FUEL_RATE_FIELDS:
        mapping = data.get(field)
        if not isinstance(mapping, dict):
            raise ValueError(f'{field} must be a mapping by fuel')
        if fuel not in mapping:
            raise ValueError(f'{field}.{fuel} is required')
        rates[field] = _require_finite_number(
            mapping[fuel],
            f'{field}.{fuel}',
        )

    if rates['technologyCostAdjustmentRatePerPlanningPeriod'] <= -1:
        raise ValueError(
            f'technologyCostAdjustmentRatePerPlanningPeriod.{fuel} must be greater than -1'
        )
    if rates['maintenanceRatePerPlanningPeriod'] < 0:
        raise ValueError(
            f'maintenanceRatePerPlanningPeriod.{fuel} must be non-negative'
        )
    if rates['decommissioningRateAtClosure'] < 0:
        raise ValueError(
            f'decommissioningRateAtClosure.{fuel} must be non-negative'
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
    if not isinstance(capacities_by_fuel, dict):
        raise ValueError('Capacities is required')
    if not isinstance(options_by_fuel, dict):
        raise ValueError('TankOptions is required')
    if 'Costs' in data:
        raise ValueError(
            'Costs must not be supplied; base costs come from TankOptions and '
            'the backend constructs all period-specific coefficients'
        )

    discount_rate = _validate_discount_rate(data)

    prepared = {}
    for fuel in fuels:
        if fuel not in capacities_by_fuel or fuel not in options_by_fuel:
            raise ValueError(f'Missing tank options for {fuel}')
        capacities = capacities_by_fuel[fuel]
        options = options_by_fuel[fuel]
        if not isinstance(capacities, list):
            raise ValueError(f'Capacities.{fuel} must be a list')
        if not isinstance(options, list):
            raise ValueError(f'TankOptions.{fuel} must be a list')
        if len(options) != len(capacities):
            raise ValueError(f'Inconsistent tank-option array lengths for {fuel}')

        validated_base_costs = []
        for option_index, (option, capacity) in enumerate(zip(options, capacities)):
            if not isinstance(option, dict):
                raise ValueError(
                    f'TankOptions.{fuel}[{option_index}] must be an object'
                )
            validated_base_cost = _require_finite_number(
                option.get('baseInvestmentCostUSD'),
                f'TankOptions.{fuel}[{option_index}].baseInvestmentCostUSD',
            )
            if validated_base_cost < 0:
                raise ValueError(
                    f'TankOptions.{fuel}[{option_index}].baseInvestmentCostUSD '
                    'must be non-negative'
                )
            if option.get('optimizerName') != fuel:
                raise ValueError(f'Inconsistent fuel identifier for {fuel}')
            if option.get('capacityMgoEquivalentTonnes') != capacity:
                raise ValueError(f'Inconsistent capacity for {fuel}')
            validated_base_costs.append(validated_base_cost)

        rates = _validate_fuel_rates(data, fuel)
        discount_factors = [
            calculate_discount_factor(
                discount_rate,
                period_index,
            )
            for period_index in range(len(periods))
        ]

        opening_costs_by_period = []
        maintenance_costs_by_period = []
        decommissioning_costs_by_period = []
        for base_cost in validated_base_costs:
            opening_costs_by_period.append([
                calculate_opening_cost_coefficient(
                    base_cost,
                    rates['technologyCostAdjustmentRatePerPlanningPeriod'],
                    period_index,
                    discount_factors[period_index],
                )
                for period_index in range(len(periods))
            ])
            maintenance_costs_by_period.append([
                calculate_maintenance_cost_coefficient(
                    base_cost,
                    rates['maintenanceRatePerPlanningPeriod'],
                    discount_factor,
                )
                for discount_factor in discount_factors
            ])
            decommissioning_costs_by_period.append([
                calculate_decommissioning_cost_coefficient(
                    base_cost,
                    rates['decommissioningRateAtClosure'],
                    discount_factor,
                )
                for discount_factor in discount_factors
            ])

        transition_costs_by_period = [
            [
                None if from_index == to_index else [None] + [
                    calculate_transition_cost_coefficient(
                        validated_base_costs[from_index],
                        validated_base_costs[to_index],
                        rates['technologyCostAdjustmentRatePerPlanningPeriod'],
                        period_index,
                        discount_factors[period_index],
                    )
                    for period_index in range(1, len(periods))
                ]
                for to_index in range(len(validated_base_costs))
            ]
            for from_index in range(len(validated_base_costs))
        ]

        prepared[fuel] = {
            **rates,
            'discountRatePerPlanningPeriod': discount_rate,
            'baseInvestmentCostsUSD': validated_base_costs,
            'discountFactorsByPeriod': discount_factors,
            'openingCostCoefficientsUSD': opening_costs_by_period,
            'maintenanceCostCoefficientsUSD': maintenance_costs_by_period,
            'decommissioningCostCoefficientsUSD': decommissioning_costs_by_period,
            'transitionCostCoefficientsUSD': transition_costs_by_period,
            # Compatibility aliases for the retained legacy model entry point.
            'investmentCostsUSDByPeriod': opening_costs_by_period,
            'maintenanceCostsUSDByPeriod': maintenance_costs_by_period,
            'decommissioningCostsUSDByPeriod': decommissioning_costs_by_period,
        }

    return prepared


def financial_parameters_for_response(prepared_costs, fuels):
    first_fuel = fuels[0]
    return {
        'discountRatePerPlanningPeriod': prepared_costs[first_fuel][
            'discountRatePerPlanningPeriod'
        ],
        'technologyCostAdjustmentRatePerPlanningPeriod': {
            fuel: prepared_costs[fuel][
                'technologyCostAdjustmentRatePerPlanningPeriod'
            ]
            for fuel in fuels
        },
        'maintenanceRatePerPlanningPeriod': {
            fuel: prepared_costs[fuel]['maintenanceRatePerPlanningPeriod']
            for fuel in fuels
        },
        'decommissioningRateAtClosure': {
            fuel: prepared_costs[fuel]['decommissioningRateAtClosure']
            for fuel in fuels
        },
    }


if __name__ == '__main__':
    try:
        request_data = json.loads(sys.stdin.read())
        print(json.dumps(prepare_financial_costs_for_model(request_data)))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({'error': 'validation_error', 'message': str(error)}))
        sys.exit(2)
