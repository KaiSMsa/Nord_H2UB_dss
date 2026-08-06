import json
import math
import sys

from ortools.linear_solver import pywraplp

from financial_parameters import (
    financial_parameters_for_response,
    prepare_financial_costs_for_model,
)


def _require_finite_model_number(value, field_name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field_name} must be a numeric value')
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'{field_name} must be finite')
    if minimum is not None and number < minimum:
        raise ValueError(f'{field_name} must be at least {minimum}')
    return number


def _validate_model_inputs(data, prepared_costs):
    periods = data['T']
    fuels = data['Fuels']
    capacities_by_fuel = data['Capacities']
    demand_by_fuel = data.get('Demand')
    initial_state_by_fuel = data.get('InitialState')

    if not isinstance(demand_by_fuel, dict):
        raise ValueError('Demand is required')
    if not isinstance(initial_state_by_fuel, dict):
        raise ValueError('InitialState is required')

    validated_demand = {}
    tank_counts = {}
    validated_initial_state = {}

    for fuel in fuels:
        capacities = capacities_by_fuel[fuel]
        if not capacities:
            raise ValueError(f'Capacities.{fuel} must be non-empty')
        validated_capacities = [
            _require_finite_model_number(
                capacity,
                f'Capacities.{fuel}[{option_index}]',
                minimum=0,
            )
            for option_index, capacity in enumerate(capacities)
        ]
        if any(capacity == 0 for capacity in validated_capacities):
            raise ValueError(f'Capacities.{fuel} values must be greater than zero')

        fuel_demand = demand_by_fuel.get(fuel)
        if not isinstance(fuel_demand, dict):
            raise ValueError(f'Demand.{fuel} is required')
        validated_demand[fuel] = {
            period: _require_finite_model_number(
                fuel_demand.get(period),
                f'Demand.{fuel}.{period}',
                minimum=0,
            )
            for period in periods
        }

        maximum_demand = max(validated_demand[fuel].values())
        tank_count = math.ceil(maximum_demand / min(validated_capacities))
        tank_counts[fuel] = tank_count

        fuel_initial_state = initial_state_by_fuel.get(fuel)
        if not isinstance(fuel_initial_state, list):
            raise ValueError(f'InitialState.{fuel} must be a list by tank index')
        if len(fuel_initial_state) != tank_count:
            raise ValueError(
                f'InitialState.{fuel} must contain {tank_count} tank rows'
            )

        validated_rows = []
        for tank_index, row in enumerate(fuel_initial_state):
            if not isinstance(row, list) or len(row) != len(capacities):
                raise ValueError(
                    f'InitialState.{fuel}[{tank_index}] must contain '
                    f'{len(capacities)} capacity values'
                )
            validated_row = []
            for option_index, value in enumerate(row):
                if isinstance(value, bool) or value not in (0, 1):
                    raise ValueError(
                        f'InitialState.{fuel}[{tank_index}][{option_index}] '
                        'must be binary'
                    )
                validated_row.append(int(value))
            if sum(validated_row) > 1:
                raise ValueError(
                    f'InitialState.{fuel}[{tank_index}] selects multiple capacities'
                )
            validated_rows.append(validated_row)

        initial_capacity = sum(
            validated_capacities[option_index] * validated_rows[tank_index][option_index]
            for tank_index in range(tank_count)
            for option_index in range(len(capacities))
        )
        if initial_capacity < validated_demand[fuel][periods[0]]:
            raise ValueError(
                f'InitialState.{fuel} does not satisfy demand in {periods[0]}'
            )
        validated_initial_state[fuel] = validated_rows

        # Accessing this here makes the validated cost/option dimensions explicit.
        if len(prepared_costs[fuel]['baseInvestmentCostsUSD']) != len(capacities):
            raise ValueError(f'Inconsistent financial option count for {fuel}')

    return validated_demand, validated_initial_state, tank_counts


def build_facility_location_model(data):
    prepared_costs = prepare_financial_costs_for_model(data)
    demand, initial_state, tank_counts = _validate_model_inputs(
        data,
        prepared_costs,
    )

    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        raise RuntimeError('CBC solver is not available')

    periods = data['T']
    fuels = data['Fuels']
    capacities_by_fuel = data['Capacities']
    y, s, x, z = {}, {}, {}, {}

    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for tank_index in range(tank_counts[fuel]):
            for option_index in range(option_count):
                for period_index in range(len(periods)):
                    key = (fuel_index, tank_index, option_index, period_index)
                    y[key] = solver.BoolVar(
                        f'y[{fuel_index},{tank_index},{option_index},{period_index}]'
                    )
                    s[key] = solver.BoolVar(
                        f's[{fuel_index},{tank_index},{option_index},{period_index}]'
                    )
                    x[key] = solver.BoolVar(
                        f'x[{fuel_index},{tank_index},{option_index},{period_index}]'
                    )
            for from_option in range(option_count):
                for to_option in range(option_count):
                    if from_option == to_option:
                        continue
                    for period_index in range(1, len(periods)):
                        key = (
                            fuel_index,
                            tank_index,
                            from_option,
                            to_option,
                            period_index,
                        )
                        z[key] = solver.BoolVar(
                            f'z[{fuel_index},{tank_index},{from_option},'
                            f'{to_option},{period_index}]'
                        )

    objective_terms = []
    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        coefficients = prepared_costs[fuel]
        for tank_index in range(tank_counts[fuel]):
            for option_index in range(option_count):
                for period_index in range(1, len(periods)):
                    objective_terms.append(
                        coefficients['openingCostCoefficientsUSD'][option_index][period_index]
                        * y[fuel_index, tank_index, option_index, period_index]
                    )
                for period_index in range(len(periods)):
                    objective_terms.append(
                        coefficients['maintenanceCostCoefficientsUSD'][option_index][period_index]
                        * s[fuel_index, tank_index, option_index, period_index]
                    )
                    objective_terms.append(
                        coefficients['decommissioningCostCoefficientsUSD'][option_index][period_index]
                        * x[fuel_index, tank_index, option_index, period_index]
                    )
            for from_option in range(option_count):
                for to_option in range(option_count):
                    if from_option == to_option:
                        continue
                    for period_index in range(1, len(periods)):
                        objective_terms.append(
                            coefficients['transitionCostCoefficientsUSD'][from_option][to_option][period_index]
                            * z[
                                fuel_index,
                                tank_index,
                                from_option,
                                to_option,
                                period_index,
                            ]
                        )
    solver.Minimize(solver.Sum(objective_terms))

    # Demand satisfaction includes tanks opened in the current period and
    # tanks carried as operational from earlier periods.
    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for period_index, period in enumerate(periods):
            solver.Add(
                solver.Sum(
                    capacities_by_fuel[fuel][option_index]
                    * (
                        y[fuel_index, tank_index, option_index, period_index]
                        + s[fuel_index, tank_index, option_index, period_index]
                    )
                    for tank_index in range(tank_counts[fuel])
                    for option_index in range(option_count)
                ) >= demand[fuel][period],
                f'demand[{fuel_index},{period_index}]',
            )

    # Operational state is intentionally aggregated over capacity options.
    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for tank_index in range(tank_counts[fuel]):
            for period_index in range(1, len(periods)):
                solver.Add(
                    solver.Sum(
                        s[fuel_index, tank_index, option_index, period_index]
                        for option_index in range(option_count)
                    )
                    == solver.Sum(
                        y[fuel_index, tank_index, option_index, earlier_period]
                        for option_index in range(option_count)
                        for earlier_period in range(period_index)
                    )
                    - solver.Sum(
                        x[fuel_index, tank_index, option_index, earlier_period]
                        for option_index in range(option_count)
                        for earlier_period in range(1, period_index + 1)
                    ),
                    f'operational[{fuel_index},{tank_index},{period_index}]',
                )

    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for tank_index in range(tank_counts[fuel]):
            solver.Add(
                solver.Sum(
                    y[fuel_index, tank_index, option_index, period_index]
                    for option_index in range(option_count)
                    for period_index in range(len(periods))
                ) <= 1,
                f'single_opening[{fuel_index},{tank_index}]',
            )
            for period_index in range(len(periods)):
                solver.Add(
                    solver.Sum(
                        y[fuel_index, tank_index, option_index, period_index]
                        + s[fuel_index, tank_index, option_index, period_index]
                        for option_index in range(option_count)
                    ) <= 1,
                    f'single_capacity[{fuel_index},{tank_index},{period_index}]',
                )

    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for tank_index in range(tank_counts[fuel]):
            for period_index in range(1, len(periods)):
                for from_option in range(option_count):
                    prior_active = (
                        y[fuel_index, tank_index, from_option, period_index - 1]
                        + s[fuel_index, tank_index, from_option, period_index - 1]
                    )
                    for to_option in range(option_count):
                        if from_option == to_option:
                            continue
                        transition = z[
                            fuel_index,
                            tank_index,
                            from_option,
                            to_option,
                            period_index,
                        ]
                        current_operating = s[
                            fuel_index,
                            tank_index,
                            to_option,
                            period_index,
                        ]
                        solver.Add(
                            transition >= prior_active + current_operating - 1,
                            f'transition_lb[{fuel_index},{tank_index},{from_option},'
                            f'{to_option},{period_index}]',
                        )
                        solver.Add(
                            transition <= prior_active,
                            f'transition_ub1[{fuel_index},{tank_index},{from_option},'
                            f'{to_option},{period_index}]',
                        )
                        solver.Add(
                            transition <= current_operating,
                            f'transition_ub2[{fuel_index},{tank_index},{from_option},'
                            f'{to_option},{period_index}]',
                        )

    # If demand drops from positive to zero, every applicable future zero-demand
    # period uses tau on the left-hand side.
    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for drop_period in range(1, len(periods)):
            if not (
                demand[fuel][periods[drop_period - 1]] > 0
                and demand[fuel][periods[drop_period]] == 0
            ):
                continue
            for future_period in range(drop_period, len(periods)):
                if demand[fuel][periods[future_period]] != 0:
                    continue
                solver.Add(
                    solver.Sum(
                        y[fuel_index, tank_index, option_index, future_period]
                        + s[fuel_index, tank_index, option_index, future_period]
                        for tank_index in range(tank_counts[fuel])
                        for option_index in range(option_count)
                    ) == 0,
                    f'permanent_zero_demand[{fuel_index},{drop_period},{future_period}]',
                )

    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        for tank_index in range(tank_counts[fuel]):
            for option_index in range(option_count):
                for period_index in range(1, len(periods)):
                    solver.Add(
                        x[fuel_index, tank_index, option_index, period_index]
                        <= y[fuel_index, tank_index, option_index, period_index - 1]
                        + s[fuel_index, tank_index, option_index, period_index - 1],
                        f'decommissioning_validity[{fuel_index},{tank_index},'
                        f'{option_index},{period_index}]',
                    )

                solver.Add(
                    y[fuel_index, tank_index, option_index, 0]
                    == initial_state[fuel][tank_index][option_index],
                    f'initial_opening[{fuel_index},{tank_index},{option_index}]',
                )
                solver.Add(
                    s[fuel_index, tank_index, option_index, 0] == 0,
                    f'initial_operating[{fuel_index},{tank_index},{option_index}]',
                )
                solver.Add(
                    x[fuel_index, tank_index, option_index, 0] == 0,
                    f'initial_closure[{fuel_index},{tank_index},{option_index}]',
                )

    return {
        'solver': solver,
        'preparedCosts': prepared_costs,
        'tankCounts': tank_counts,
        'demand': demand,
        'initialState': initial_state,
        'variables': {'y': y, 's': s, 'x': x, 'z': z},
    }


def _binary_value(variable):
    return 1 if variable.solution_value() > 0.5 else 0


def solve_facility_location(data, export_model=False):
    model = build_facility_location_model(data)
    solver = model['solver']
    prepared_costs = model['preparedCosts']
    tank_counts = model['tankCounts']
    y = model['variables']['y']
    s = model['variables']['s']
    x = model['variables']['x']
    z = model['variables']['z']
    periods = data['T']
    fuels = data['Fuels']
    capacities_by_fuel = data['Capacities']

    if export_model:
        with open('facility_location_model.lp', 'w') as lp_file:
            lp_file.write(solver.ExportModelAsLpFormat(False))

    status = solver.Solve()
    discount_factors = prepared_costs[fuels[0]]['discountFactorsByPeriod']
    period_mapping = [
        {
            'label': period,
            'periodIndex': period_index,
            'discountFactor': discount_factors[period_index],
        }
        for period_index, period in enumerate(periods)
    ]
    result = {
        'status': status,
        'solution': {},
        'costs': {},
        'transitions': {},
        'planningPeriods': period_mapping,
        'periodMapping': period_mapping,
        'financialParameters': financial_parameters_for_response(
            prepared_costs,
            fuels,
        ),
        'costBreakdown': {
            'openingInvestmentCostUSD': 0.0,
            'maintenanceCostUSD': 0.0,
            'decommissioningCostUSD': 0.0,
            'transitionCostUSD': 0.0,
            'totalObjectiveUSD': 0.0,
        },
    }

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return result

    for fuel_index, fuel in enumerate(fuels):
        option_count = len(capacities_by_fuel[fuel])
        fuel_solution = {}
        fuel_costs = {}
        fuel_transitions = {}
        coefficients = prepared_costs[fuel]

        for period_index, period in enumerate(periods):
            period_solution = {}
            period_costs = {}
            period_transitions = {}
            for tank_index in range(tank_counts[fuel]):
                tank_solution = {}
                tank_costs = {}
                tank_transitions = []
                for option_index, capacity in enumerate(capacities_by_fuel[fuel]):
                    opened = _binary_value(
                        y[fuel_index, tank_index, option_index, period_index]
                    )
                    operating = _binary_value(
                        s[fuel_index, tank_index, option_index, period_index]
                    )
                    closed = _binary_value(
                        x[fuel_index, tank_index, option_index, period_index]
                    )
                    if opened or operating or closed:
                        tank_solution[capacity] = {
                            'opened': opened,
                            'operating': operating,
                            'closed': closed,
                        }

                    opening_cost = (
                        opened
                        * coefficients['openingCostCoefficientsUSD'][option_index][period_index]
                        if period_index > 0
                        else 0.0
                    )
                    maintenance_cost = (
                        operating
                        * coefficients['maintenanceCostCoefficientsUSD'][option_index][period_index]
                    )
                    decommissioning_cost = (
                        closed
                        * coefficients['decommissioningCostCoefficientsUSD'][option_index][period_index]
                    )
                    if opened or operating or closed:
                        tank_costs[capacity] = {
                            'opened': opening_cost,
                            'operating': maintenance_cost,
                            'closed': decommissioning_cost,
                        }
                    result['costBreakdown']['openingInvestmentCostUSD'] += opening_cost
                    result['costBreakdown']['maintenanceCostUSD'] += maintenance_cost
                    result['costBreakdown']['decommissioningCostUSD'] += decommissioning_cost

                if period_index > 0:
                    for from_option in range(option_count):
                        for to_option in range(option_count):
                            if from_option == to_option:
                                continue
                            transition_variable = z[
                                fuel_index,
                                tank_index,
                                from_option,
                                to_option,
                                period_index,
                            ]
                            if _binary_value(transition_variable):
                                transition_cost = coefficients[
                                    'transitionCostCoefficientsUSD'
                                ][from_option][to_option][period_index]
                                tank_transitions.append({
                                    'fromCapacity': capacities_by_fuel[fuel][from_option],
                                    'toCapacity': capacities_by_fuel[fuel][to_option],
                                    'costUSD': transition_cost,
                                })
                                result['costBreakdown']['transitionCostUSD'] += transition_cost

                if tank_solution:
                    period_solution[f'Tank_{tank_index + 1}'] = tank_solution
                if tank_costs:
                    period_costs[f'Tank_{tank_index + 1}'] = tank_costs
                if tank_transitions:
                    period_transitions[f'Tank_{tank_index + 1}'] = tank_transitions

            if period_solution:
                fuel_solution[period] = period_solution
            if period_costs:
                fuel_costs[period] = period_costs
            if period_transitions:
                fuel_transitions[period] = period_transitions

        if fuel_solution:
            result['solution'][fuel] = fuel_solution
        if fuel_costs:
            result['costs'][fuel] = fuel_costs
        if fuel_transitions:
            result['transitions'][fuel] = fuel_transitions

    result['costBreakdown']['totalObjectiveUSD'] = solver.Objective().Value()
    return result


if __name__ == '__main__':
    try:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text)
        with open('input_data.txt', 'w') as input_file:
            input_file.write(input_text)
        result_data = solve_facility_location(input_data, export_model=True)
        output_text = json.dumps(result_data)
        print(output_text)
        with open('output_data.txt', 'w') as output_file:
            output_file.write(output_text)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({'error': 'validation_error', 'message': str(error)}))
        sys.exit(2)
