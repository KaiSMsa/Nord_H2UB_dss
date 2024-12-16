# import json
# from ortools.linear_solver import pywraplp

# def solve():
#     # Create solver
#     solver = pywraplp.Solver.CreateSolver('SCIP')
#     if not solver:
#         return json.dumps({"error": "Solver not available!"})

#     # Decision variables
#     x = solver.IntVar(0, 10, 'x')
#     y = solver.IntVar(0, 10, 'y')

#     # Objective function
#     solver.Maximize(3 * x + 4 * y)

#     # Constraints
#     solver.Add(2 * x + y <= 14)
#     solver.Add(x + y <= 10)

#     # Solve the problem
#     status = solver.Solve()

#     if status == pywraplp.Solver.OPTIMAL:
#         result = {
#             "x": x.solution_value(),
#             "y": y.solution_value(),
#             "objective": solver.Objective().Value()
#         }
#         return json.dumps(result)
#     else:
#         return json.dumps({"error": "No optimal solution found."})

# if __name__ == "__main__":
#     print(solve())


import sys
import json
from ortools.linear_solver import pywraplp

def solve_facility_location(data):
    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        print(json.dumps({"error": "Solver not available!"}))
        return

    # Extract data from input
    T = data['T']  # Time periods
    Fuels = data['Fuels']  # Fuels list
    Capacities = data['Capacities']  # Capacities per fuel
    Costs = data['Costs']  # Costs per fuel
    Demand = data['Demand']  # Demand data
    # Initialize variables
    y, s, x, z = {}, {}, {}, {}

    # Decision variables
    for f_idx, fuel in enumerate(Fuels):
        for k_idx, capacity in enumerate(Capacities[fuel]):
            for t_idx, year in enumerate(T):
                y[f_idx, k_idx, t_idx] = solver.BoolVar(f'y[{f_idx},{k_idx},{t_idx}]')  # Opening
                s[f_idx, k_idx, t_idx] = solver.BoolVar(f's[{f_idx},{k_idx},{t_idx}]')  # Operating
                x[f_idx, k_idx, t_idx] = solver.BoolVar(f'x[{f_idx},{k_idx},{t_idx}]')  # Closing

            # Transition variables
            for k2_idx in range(len(Capacities[fuel])):
                if k_idx != k2_idx:
                    for t_idx, year in enumerate(T):
                        z[f_idx, k_idx, k2_idx, t_idx] = solver.BoolVar(
                            f'z[{f_idx},{k_idx},{k2_idx},{t_idx}]'
                        )

    # Objective function components
    objective_terms = []

    # Compute dynamic costs and add to objective
    for f_idx, fuel in enumerate(Fuels):
        maintenance_rate = Costs[fuel]['maintenanceCost']
        decommissioning_rate = Costs[fuel]['decommissioningCost']
        initial_costs = Costs[fuel]['costs']
        change_rate = Costs[fuel]['changeRate']

        for k_idx, capacity in enumerate(Capacities[fuel]):
            # Compute dynamic costs over time
            dynamic_costs = [
                round(initial_costs[k_idx] * ((1 + (change_rate / 100.0)) ** t_idx), -3) for t_idx in range(len(T)) 
            ]
            maintenance_cost = round(initial_costs[k_idx] * (maintenance_rate / 100.0), -3)
            decommissioning_cost = round(initial_costs[k_idx] * (decommissioning_rate / 100.0), -3)
            
            for t_idx in range(len(T)):
                # At the beginning of the planning horizon, we enforce to open an MGO tank for the model purpose but we count only for the maintenance cost.
                if f_idx == 0 and t_idx == 0:
                    objective_terms.append(maintenance_cost * y[f_idx, k_idx, t_idx])
                else:
                    # Opening cost
                    objective_terms.append(dynamic_costs[t_idx] * y[f_idx, k_idx, t_idx])
                    objective_terms.append(maintenance_cost * s[f_idx, k_idx, t_idx])

                # Decommissioning cost
                objective_terms.append(decommissioning_cost * x[f_idx, k_idx, t_idx])

            # Transition costs
            for k2_idx in range(len(Capacities[fuel])):
                if k_idx < k2_idx:
                    for t_idx in range(len(T)):
                        extension_cost = abs(1.2 * (dynamic_costs[t_idx] - initial_costs[k2_idx] * ((1 + change_rate) ** t_idx)))
                        objective_terms.append(extension_cost * z[f_idx, k_idx, k2_idx, t_idx])
                elif k_idx > k2_idx:
                    for t_idx in range(len(T)):
                        reduction_cost = abs(1.2 * (dynamic_costs[t_idx] - initial_costs[k2_idx] * ((1 + change_rate) ** t_idx)))
                        objective_terms.append(reduction_cost * z[f_idx, k_idx, k2_idx, t_idx])

    # Set the objective function
    solver.Minimize(solver.Sum(objective_terms))

    # Constraints
    # Demand satisfaction
    for t_idx, year in enumerate(T):
        for f_idx, fuel in enumerate(Fuels):
            demand = Demand[fuel][year]
            total_output = solver.Sum(
                Capacities[fuel][k_idx] * (y[f_idx, k_idx, t_idx] + s[f_idx, k_idx, t_idx])
                for k_idx in range(len(Capacities[fuel]))
            )
            constraint = solver.Add(total_output >= demand)

    # Operation logic
    for f_idx, fuel in enumerate(Fuels):
        for t_idx in range(1, len(T)):  # t >= 2
            for k_idx in range(len(Capacities[fuel])):
                total_s_t = s[f_idx, k_idx, t_idx]
                total_y_before_t = solver.Sum(
                    y[f_idx, k_idx, tp] for tp in range(0, t_idx)
                )
                total_x_until_t = solver.Sum(
                    x[f_idx, k_idx, tp] for tp in range(0, t_idx + 1)
                )
                cosntarint = solver.Add(total_s_t == total_y_before_t - total_x_until_t)

    # Facility opening constraints
    for f_idx, fuel in enumerate(Fuels):
        total_y = solver.Sum(y[f_idx, k_idx, t_idx] for k_idx in range(len(Capacities[fuel])) for t_idx in range(len(T)))
        constraint = solver.Add(total_y <= 1)        

    # Single capacity operation per fuel per time
    for f_idx, fuel in enumerate(Fuels):
        for t_idx in range(len(T)):
            total_s = solver.Sum(s[f_idx, k_idx, t_idx] for k_idx in range(len(Capacities[fuel])))
            constraint = solver.Add(total_s <= 1)
            
    # Capacity transition constraints
    for f_idx, fuel in enumerate(Fuels):
        for t_idx in range(1, len(T)):  # t >= 2
            for k_idx in range(len(Capacities[fuel])):
                for k2_idx in range(len(Capacities[fuel])):
                    if k_idx != k2_idx:
                        lhs = z[f_idx, k_idx, k2_idx, t_idx]
                        rhs = y[f_idx, k_idx, t_idx - 1] + s[f_idx, k_idx, t_idx - 1] + s[f_idx, k2_idx, t_idx] - 1
                        constraint = solver.Add(lhs >= rhs)

    for f_idx, fuel in enumerate(Fuels):
        total_x = solver.Sum(x[f_idx, k_idx, t_idx] for k_idx in range(len(Capacities[fuel])) for t_idx in range(len(T)))
        solver.Add(total_x <= 1)

    # Enforce closing a fuel offer if no more used
    for f_idx, fuel in enumerate(Fuels):
        last_t = -1
        for t_idx in range(1, len(T)):  # t >= 2
            if Demand[fuel][T[t_idx - 1]] > 0 and Demand[fuel][T[t_idx]] == 0:
                last_t = t_idx
        if last_t != -1:
            operation_f = solver.Sum(y[f_idx, k_idx, last_t] + s[f_idx, k_idx, last_t] for k_idx in range(len(Capacities[fuel])))
            solver.Add(operation_f == 0)

    # Open MGO for t= 0, this is a mandatory operation because in practice the port has this tank already opened
    open_MGO = solver.Sum(y[0, k_idx, 0] for k_idx in range(len(Capacities['MGO'])))
    solver.Add(open_MGO == 1)

    with open("facility_location_model.lp", "w") as lp_file:
        lp_file.write(solver.ExportModelAsLpFormat(False))
        
    # Solve the model
    status = solver.Solve()

    # Prepare the results
    result_data = {'status': status, 'solution': {}, 'costs': {}}

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        for f_idx, fuel in enumerate(Fuels):
            # fuel_data = {'fuel': fuel, 'schedule': []}
            fuel_data = {}
            for t_idx, year in enumerate(T):
                # time_data = {'year': year, 'capacities': []}
                year_fuel = {}
                for k_idx, capacity in enumerate(Capacities[fuel]):
                    if y[f_idx, k_idx, t_idx].solution_value() > 0.5 or s[f_idx, k_idx, t_idx].solution_value() > 0.5 or x[f_idx, k_idx, t_idx].solution_value() > 0.5:
                        year_fuel[capacity] = {
                            'opened': int(y[f_idx, k_idx, t_idx].solution_value()),
                            'operating': int(s[f_idx, k_idx, t_idx].solution_value()),
                            'closed': int(x[f_idx, k_idx, t_idx].solution_value())
                        }
                if year_fuel:
                    fuel_data[year] = year_fuel
            if fuel_data:
                result_data['solution'][fuel] = fuel_data

        # Compute costs of the solution
        for f_idx, fuel in enumerate(Fuels):
            cost_data = {}

            maintenance_rate = Costs[fuel]['maintenanceCost']
            decommissioning_rate = Costs[fuel]['decommissioningCost']
            initial_costs = Costs[fuel]['costs']
            change_rate = Costs[fuel]['changeRate']

            for t_idx, year in enumerate(T):
                year_cost = {}
                for k_idx, capacity in enumerate(Capacities[fuel]):
                    # Compute dynamic, maintenance and decommissioning costs over time
                    dynamic_cost = round(initial_costs[k_idx] * ((1 + (change_rate / 100.0)) ** t_idx), -3)
                    maintenance_cost = round(initial_costs[k_idx] * (maintenance_rate / 100.0), -3)
                    decommissioning_cost = round(initial_costs[k_idx] * (decommissioning_rate / 100.0), -3)
                
                    # At the beginning of the planning horizon, we enforce to open an MGO tank for the model purpose but we count only for the maintenance cost.
                    if f_idx == 0 and t_idx == 0:
                        if y[f_idx, k_idx, t_idx].solution_value() > 0.5:
                            year_cost[capacity] = {
                                'opened': 0,
                                'operating': maintenance_cost,
                                'closed': 0
                            }
                    else:
                        if y[f_idx, k_idx, t_idx].solution_value() > 0.5 or s[f_idx, k_idx, t_idx].solution_value() > 0.5 or x[f_idx, k_idx, t_idx].solution_value() > 0.5:
                            year_cost[capacity] = {
                                'opened': int(y[f_idx, k_idx, t_idx].solution_value() * dynamic_cost),
                                'operating': int(s[f_idx, k_idx, t_idx].solution_value() * maintenance_cost),
                                'closed': int(x[f_idx, k_idx, t_idx].solution_value() * decommissioning_cost)
                            }
                if year_cost:
                    cost_data[year] = year_cost
            if cost_data:
                result_data['costs'][fuel] = cost_data

                    # # Transition costs
                    # for k2_idx in range(len(Capacities[fuel])):
                    #     if k_idx < k2_idx:
                    #         for t_idx in range(len(T)):
                    #             extension_cost = abs(1.2 * (dynamic_costs[t_idx] - initial_costs[k2_idx] * ((1 + change_rate) ** t_idx)))
                    #             objective_terms.append(extension_cost * z[f_idx, k_idx, k2_idx, t_idx])
                    #     elif k_idx > k2_idx:
                    #         for t_idx in range(len(T)):
                    #             reduction_cost = abs(1.2 * (dynamic_costs[t_idx] - initial_costs[k2_idx] * ((1 + change_rate) ** t_idx)))
                    #             objective_terms.append(reduction_cost * z[f_idx, k_idx, k2_idx, t_idx])


    print(json.dumps(result_data))  # Output the results in JSON format


if __name__ == '__main__':
    # input_text = sys.stdin.read()
    # Read input data from file
    input_file = "input_data.txt"
    with open(input_file, "r") as file:
        input_text = file.read()
    input_data = json.loads(input_text)
    # with open("input_data.txt", "w") as lp_file:
    #     lp_file.write(input_text)
    solve_facility_location(input_data)
