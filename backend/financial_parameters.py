import json
import math
import sys


FUEL_ANNUAL_RATE_FIELDS = (
    'technologyCostAdjustmentRateAnnual',
    'maintenanceRateAnnual',
    'decommissioningRateAtClosure',
)

LEGACY_RATE_FIELDS = (
    'discountRatePerPlanningPeriod',
    'technologyCostAdjustmentRatePerPlanningPeriod',
    'maintenanceRatePerPlanningPeriod',
)


def _require_finite_number(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field_name} must be a numeric value')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{field_name} must be finite')
    return number


def _require_positive_integer(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f'{field_name} must be a positive integer')
    return value


def _require_period_index(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('periodIndex must be a non-negative integer')
    return value


def calculate_elapsed_years(planning_period_years, period_index):
    years_per_period = _require_positive_integer(
        planning_period_years,
        'planningPeriodYears',
    )
    index = _require_period_index(period_index)
    return years_per_period * index


def calculate_discount_factor(
    discount_rate_annual,
    planning_period_years,
    period_index,
):
    rate = _require_finite_number(discount_rate_annual, 'discountRateAnnual')
    if rate <= -1:
        raise ValueError('discountRateAnnual must be greater than -1')
    elapsed_years = calculate_elapsed_years(planning_period_years, period_index)
    return 1 / ((1 + rate) ** elapsed_years)


def calculate_technology_adjusted_cost(
    base_cost,
    technology_cost_adjustment_rate_annual,
    planning_period_years,
    period_index,
):
    cost = _require_finite_number(base_cost, 'baseInvestmentCostUSD')
    rate = _require_finite_number(
        technology_cost_adjustment_rate_annual,
        'technologyCostAdjustmentRateAnnual',
    )
    if rate <= -1:
        raise ValueError('technologyCostAdjustmentRateAnnual must be greater than -1')
    elapsed_years = calculate_elapsed_years(planning_period_years, period_index)
    return cost * ((1 + rate) ** elapsed_years)


def calculate_present_value_cost(nominal_period_cost, discount_factor):
    cost = _require_finite_number(nominal_period_cost, 'nominalPeriodCostUSD')
    factor = _require_finite_number(discount_factor, 'discountFactor')
    return cost * factor


def calculate_opening_cost_coefficient(
    base_investment_cost_usd,
    technology_cost_adjustment_rate_annual,
    discount_rate_annual,
    planning_period_years,
    period_index,
):
    nominal_cost = calculate_technology_adjusted_cost(
        base_investment_cost_usd,
        technology_cost_adjustment_rate_annual,
        planning_period_years,
        period_index,
    )
    discount_factor = calculate_discount_factor(
        discount_rate_annual,
        planning_period_years,
        period_index,
    )
    return calculate_present_value_cost(nominal_cost, discount_factor)


def calculate_maintenance_cost_coefficient(
    base_investment_cost_usd,
    maintenance_rate_annual,
    discount_rate_annual,
    planning_period_years,
    period_index,
):
    base_cost = _require_finite_number(
        base_investment_cost_usd,
        'baseInvestmentCostUSD',
    )
    rate = _require_finite_number(maintenance_rate_annual, 'maintenanceRateAnnual')
    if rate < 0:
        raise ValueError('maintenanceRateAnnual must be non-negative')
    years_per_period = _require_positive_integer(
        planning_period_years,
        'planningPeriodYears',
    )
    discount_factor = calculate_discount_factor(
        discount_rate_annual,
        years_per_period,
        period_index,
    )
    # Aggregate all annual maintenance in the planning period and discount
    # that aggregate at the beginning of the period.
    return years_per_period * base_cost * rate * discount_factor


def calculate_decommissioning_cost_coefficient(
    base_investment_cost_usd,
    decommissioning_rate_at_closure,
    discount_rate_annual,
    planning_period_years,
    period_index,
):
    base_cost = _require_finite_number(
        base_investment_cost_usd,
        'baseInvestmentCostUSD',
    )
    rate = _require_finite_number(
        decommissioning_rate_at_closure,
        'decommissioningRateAtClosure',
    )
    if rate < 0:
        raise ValueError('decommissioningRateAtClosure must be non-negative')
    discount_factor = calculate_discount_factor(
        discount_rate_annual,
        planning_period_years,
        period_index,
    )
    return base_cost * rate * discount_factor


def calculate_transition_cost_coefficient(
    from_base_investment_cost_usd,
    to_base_investment_cost_usd,
    transition_cost_rate,
    technology_cost_adjustment_rate_annual,
    discount_rate_annual,
    planning_period_years,
    period_index,
):
    from_nominal_cost = calculate_technology_adjusted_cost(
        from_base_investment_cost_usd,
        technology_cost_adjustment_rate_annual,
        planning_period_years,
        period_index,
    )
    to_nominal_cost = calculate_technology_adjusted_cost(
        to_base_investment_cost_usd,
        technology_cost_adjustment_rate_annual,
        planning_period_years,
        period_index,
    )
    rate = _require_finite_number(transition_cost_rate, 'transitionCostRate')
    if rate < 0:
        raise ValueError('transitionCostRate must be non-negative')
    discount_factor = calculate_discount_factor(
        discount_rate_annual,
        planning_period_years,
        period_index,
    )
    return rate * abs(to_nominal_cost - from_nominal_cost) * discount_factor


def _reject_legacy_fields(data):
    supplied = [field for field in LEGACY_RATE_FIELDS if field in data]
    if supplied:
        raise ValueError(
            'Legacy planning-period rate fields are not supported: '
            f'{", ".join(supplied)}. Use annual rate fields instead.'
        )


def _validate_financial_inputs(data, fuels):
    _reject_legacy_fields(data)
    planning_period_years = _require_positive_integer(
        data.get('planningPeriodYears'),
        'planningPeriodYears',
    )
    discount_rate_annual = _require_finite_number(
        data.get('discountRateAnnual'),
        'discountRateAnnual',
    )
    if discount_rate_annual <= -1:
        raise ValueError('discountRateAnnual must be greater than -1')
    transition_cost_rate = _require_finite_number(
        data.get('transitionCostRate'),
        'transitionCostRate',
    )
    if transition_cost_rate < 0:
        raise ValueError('transitionCostRate must be non-negative')

    fuel_rates = {}
    for fuel in fuels:
        rates = {}
        for field in FUEL_ANNUAL_RATE_FIELDS:
            mapping = data.get(field)
            if not isinstance(mapping, dict):
                raise ValueError(f'{field} must be a mapping by fuel')
            if fuel not in mapping:
                raise ValueError(f'{field}.{fuel} is required')
            rates[field] = _require_finite_number(
                mapping[fuel],
                f'{field}.{fuel}',
            )
        if rates['technologyCostAdjustmentRateAnnual'] <= -1:
            raise ValueError(
                f'technologyCostAdjustmentRateAnnual.{fuel} must be greater than -1'
            )
        if rates['maintenanceRateAnnual'] < 0:
            raise ValueError(f'maintenanceRateAnnual.{fuel} must be non-negative')
        if rates['decommissioningRateAtClosure'] < 0:
            raise ValueError(
                f'decommissioningRateAtClosure.{fuel} must be non-negative'
            )
        fuel_rates[fuel] = rates

    return {
        'planningPeriodYears': planning_period_years,
        'discountRateAnnual': discount_rate_annual,
        'transitionCostRate': transition_cost_rate,
        'fuelRates': fuel_rates,
    }


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

    assumptions = _validate_financial_inputs(data, fuels)
    years_per_period = assumptions['planningPeriodYears']
    discount_rate = assumptions['discountRateAnnual']
    transition_rate = assumptions['transitionCostRate']
    discount_factors = [
        calculate_discount_factor(discount_rate, years_per_period, period_index)
        for period_index in range(len(periods))
    ]

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

        base_costs = []
        for option_index, (option, capacity) in enumerate(zip(options, capacities)):
            if not isinstance(option, dict):
                raise ValueError(
                    f'TankOptions.{fuel}[{option_index}] must be an object'
                )
            base_cost = _require_finite_number(
                option.get('baseInvestmentCostUSD'),
                f'TankOptions.{fuel}[{option_index}].baseInvestmentCostUSD',
            )
            if base_cost < 0:
                raise ValueError(
                    f'TankOptions.{fuel}[{option_index}].baseInvestmentCostUSD '
                    'must be non-negative'
                )
            if option.get('optimizerName') != fuel:
                raise ValueError(f'Inconsistent fuel identifier for {fuel}')
            if option.get('capacityMgoEquivalentTonnes') != capacity:
                raise ValueError(f'Inconsistent capacity for {fuel}')
            base_costs.append(base_cost)

        rates = assumptions['fuelRates'][fuel]
        opening_coefficients = [
            [
                calculate_opening_cost_coefficient(
                    base_cost,
                    rates['technologyCostAdjustmentRateAnnual'],
                    discount_rate,
                    years_per_period,
                    period_index,
                )
                for period_index in range(len(periods))
            ]
            for base_cost in base_costs
        ]
        maintenance_coefficients = [
            [
                calculate_maintenance_cost_coefficient(
                    base_cost,
                    rates['maintenanceRateAnnual'],
                    discount_rate,
                    years_per_period,
                    period_index,
                )
                for period_index in range(len(periods))
            ]
            for base_cost in base_costs
        ]
        decommissioning_coefficients = [
            [
                calculate_decommissioning_cost_coefficient(
                    base_cost,
                    rates['decommissioningRateAtClosure'],
                    discount_rate,
                    years_per_period,
                    period_index,
                )
                for period_index in range(len(periods))
            ]
            for base_cost in base_costs
        ]
        transition_coefficients = [
            [
                None if from_index == to_index else [None] + [
                    calculate_transition_cost_coefficient(
                        base_costs[from_index],
                        base_costs[to_index],
                        transition_rate,
                        rates['technologyCostAdjustmentRateAnnual'],
                        discount_rate,
                        years_per_period,
                        period_index,
                    )
                    for period_index in range(1, len(periods))
                ]
                for to_index in range(len(base_costs))
            ]
            for from_index in range(len(base_costs))
        ]

        prepared[fuel] = {
            **rates,
            'discountRateAnnual': discount_rate,
            'planningPeriodYears': years_per_period,
            'transitionCostRate': transition_rate,
            'baseInvestmentCostsUSD': base_costs,
            'discountFactorsByPeriod': discount_factors,
            'openingCostCoefficientsUSD': opening_coefficients,
            'maintenanceCostCoefficientsUSD': maintenance_coefficients,
            'decommissioningCostCoefficientsUSD': decommissioning_coefficients,
            'transitionCostCoefficientsUSD': transition_coefficients,
            # Compatibility aliases for the retained legacy model entry point.
            'investmentCostsUSDByPeriod': opening_coefficients,
            'maintenanceCostsUSDByPeriod': maintenance_coefficients,
            'decommissioningCostsUSDByPeriod': decommissioning_coefficients,
        }

    return prepared


def financial_parameters_for_response(prepared_costs, fuels):
    first = prepared_costs[fuels[0]]
    return {
        'planningPeriodYears': first['planningPeriodYears'],
        'discountRateAnnual': first['discountRateAnnual'],
        'transitionCostRate': first['transitionCostRate'],
        'technologyCostAdjustmentRateAnnual': {
            fuel: prepared_costs[fuel]['technologyCostAdjustmentRateAnnual']
            for fuel in fuels
        },
        'maintenanceRateAnnual': {
            fuel: prepared_costs[fuel]['maintenanceRateAnnual']
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
