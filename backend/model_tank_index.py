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
    
    num_tanks = 10
    # Initialize variables
    y, s, x, z = {}, {}, {}, {}

    for f_idx, fuel in enumerate(Fuels):
        for i in range(num_tanks):
            for k_idx, capacity in enumerate(Capacities[fuel]):
                for t_idx, year in enumerate(T):
                    y[f_idx, i, k_idx, t_idx] = solver.BoolVar(f'y[{f_idx},{i},{k_idx},{t_idx}]') # Opening
                    s[f_idx, i, k_idx, t_idx] = solver.BoolVar(f's[{f_idx},{i},{k_idx},{t_idx}]') # Operating
                    x[f_idx, i, k_idx, t_idx] = solver.BoolVar(f'x[{f_idx},{i},{k_idx},{t_idx}]') # Closing
            # Transition variables for each tank instance (for capacity changes)
            for k_idx in range(len(Capacities[fuel])):
                for k2_idx in range(len(Capacities[fuel])):
                    if k_idx != k2_idx:
                        for t_idx, year in enumerate(T):
                            z[f_idx, i, k_idx, k2_idx, t_idx] = solver.BoolVar(
                                f'z[{f_idx},{i},{k_idx},{k2_idx},{t_idx}]'
                            )

    # Objective function components
    objective_terms = []
    for f_idx, fuel in enumerate(Fuels):
        maintenance_rate = Costs[fuel]['maintenanceCost']
        decommissioning_rate = Costs[fuel]['decommissioningCost']
        initial_costs = Costs[fuel]['costs']
        change_rate = Costs[fuel]['changeRate']
        
        for k_idx, capacity in enumerate(Capacities[fuel]):
            # Compute dynamic costs over time for candidate k
            dynamic_costs = [
                round(initial_costs[k_idx] * ((1 + (change_rate / 100.0)) ** t_idx), -3)
                for t_idx in range(len(T))
            ]
            maintenance_cost = round(initial_costs[k_idx] * (maintenance_rate / 100.0), -3)
            decommissioning_cost = round(initial_costs[k_idx] * (decommissioning_rate / 100.0), -3)
            
            for i in range(num_tanks):
                for t_idx in range(len(T)):
                    # At t=0 for MGO, force opening but count only maintenance cost
                    if fuel == "MGO" and t_idx == 0:
                        objective_terms.append(maintenance_cost * y[f_idx, i, k_idx, t_idx])
                    else:
                        objective_terms.append(dynamic_costs[t_idx] * y[f_idx, i, k_idx, t_idx])
                        objective_terms.append(maintenance_cost * s[f_idx, i, k_idx, t_idx])
                    # Decommissioning cost
                    objective_terms.append(decommissioning_cost * x[f_idx, i, k_idx, t_idx])
            
            # Transition costs for capacity changes per tank
            for i in range(num_tanks):
                for k2_idx in range(len(Capacities[fuel])):
                    if k_idx != k2_idx:
                        for t_idx in range(len(T)):
                            if k_idx < k2_idx:
                                extension_cost = abs(1.2 * (dynamic_costs[t_idx] - 
                                    initial_costs[k2_idx] * ((1 + (change_rate / 100.0)) ** t_idx)))
                                objective_terms.append(extension_cost * z[f_idx, i, k_idx, k2_idx, t_idx])
                            elif k_idx > k2_idx:
                                reduction_cost = abs(1.2 * (dynamic_costs[t_idx] - 
                                    initial_costs[k2_idx] * ((1 + (change_rate / 100.0)) ** t_idx)))
                                objective_terms.append(reduction_cost * z[f_idx, i, k_idx, k2_idx, t_idx])
    
    # Set the objective: minimize total cost
    solver.Minimize(solver.Sum(objective_terms))
    
    # Constraints

    # Demand satisfaction: total capacity (from opened and operating tanks) must meet or exceed demand
    for t_idx, year in enumerate(T):
        for f_idx, fuel in enumerate(Fuels):
            demand = Demand[fuel][year]
            total_output = solver.Sum(
                Capacities[fuel][k_idx] * (y[f_idx, i, k_idx, t_idx] + s[f_idx, i, k_idx, t_idx])
                for i in range(num_tanks)
                for k_idx in range(len(Capacities[fuel]))
            )
            solver.Add(total_output >= demand)
    
    # Operation logic: For each tank, operating status is determined by cumulative openings minus closings
    for f_idx, fuel in enumerate(Fuels):
        for i in range(num_tanks):
            for t_idx in range(1, len(T)):
                for k_idx in range(len(Capacities[fuel])):
                    total_y_before_t = solver.Sum(
                        y[f_idx, i, k_idx, tp] for tp in range(t_idx)
                    )
                    total_x_until_t = solver.Sum(
                        x[f_idx, i, k_idx, tp] for tp in range(t_idx + 1)
                    )
                    solver.Add(s[f_idx, i, k_idx, t_idx] == total_y_before_t - total_x_until_t)
    
    # Facility opening constraint: Each fuel can have at most 'num_tanks' openings in total.
    for f_idx, fuel in enumerate(Fuels):
        total_y = solver.Sum(
            y[f_idx, i, k_idx, t_idx]
            for i in range(num_tanks)
            for k_idx in range(len(Capacities[fuel]))
            for t_idx in range(len(T))
        )
        solver.Add(total_y <= num_tanks)
    
    # Single capacity operation per tank: a tank can operate in only one capacity option at a given time.
    for f_idx, fuel in enumerate(Fuels):
        for i in range(num_tanks):
            for t_idx in range(len(T)):
                total_s = solver.Sum(
                    s[f_idx, i, k_idx, t_idx] for k_idx in range(len(Capacities[fuel]))
                )
                solver.Add(total_s <= 1)
    
    # Capacity transition constraints: track transitions for each tank separately
    for f_idx, fuel in enumerate(Fuels):
        for i in range(num_tanks):
            for t_idx in range(1, len(T)):
                for k_idx in range(len(Capacities[fuel])):
                    for k2_idx in range(len(Capacities[fuel])):
                        if k_idx != k2_idx:
                            lhs = z[f_idx, i, k_idx, k2_idx, t_idx]
                            rhs = (y[f_idx, i, k_idx, t_idx - 1] +
                                   s[f_idx, i, k_idx, t_idx - 1] +
                                   s[f_idx, i, k2_idx, t_idx] - 1)
                            solver.Add(lhs >= rhs)
    
    # # Closing constraint: each fuel can have at most 'num_tanks' closing operations
    # for f_idx, fuel in enumerate(Fuels):
    #     total_x = solver.Sum(
    #         x[f_idx, i, k_idx, t_idx]
    #         for i in range(num_tanks)
    #         for k_idx in range(len(Capacities[fuel]))
    #         for t_idx in range(len(T))
    #     )
    #     solver.Add(total_x <= num_tanks)
    
    # Enforce closing if demand drops from positive to zero: for each fuel, if demand goes to zero, the combined operation must cease.
    for f_idx, fuel in enumerate(Fuels):
        last_t = -1
        for t_idx in range(1, len(T)):
            if Demand[fuel][T[t_idx - 1]] > 0 and Demand[fuel][T[t_idx]] == 0:
                last_t = t_idx
        if last_t != -1:
            operation_f = solver.Sum(
                y[f_idx, i, k_idx, last_t] + s[f_idx, i, k_idx, last_t]
                for i in range(num_tanks)
                for k_idx in range(len(Capacities[fuel]))
            )
            solver.Add(operation_f == 0)
    
    # Mandatory opening of an MGO tank at t = 0 (for model purposes, no maintenance or closing is allowed). This is to make the model feasible.
    if "MGO" in Fuels:
        mgo_f_idx = Fuels.index("MGO")
        open_MGO = solver.Sum(
            y[mgo_f_idx, i, k_idx, 0] for i in range(num_tanks) for k_idx in range(len(Capacities["MGO"]))
        )
        solver.Add(open_MGO >= 1)
        
        no_maintenance = solver.Sum(
            s[mgo_f_idx, i, k_idx, 0] for i in range(num_tanks) for k_idx in range(len(Capacities["MGO"]))
        )
        solver.Add(no_maintenance == 0)
        
        no_closing = solver.Sum(
            x[mgo_f_idx, i, k_idx, 0] for i in range(num_tanks) for k_idx in range(len(Capacities["MGO"]))
        )
        solver.Add(no_closing == 0)
    
    # Sequential opening constraint: tank i must be open before tank i+1
    for f_idx, fuel in enumerate(Fuels):
        for t_idx in range(len(T)):
            for i in range(num_tanks - 1): 
                # Enforce that tank i must be open if tank i+1 is open.
                solver.Add(
                        solver.Sum((y[f_idx, i, k_idx, t_idx] + s[f_idx, i, k_idx, t_idx]) for k_idx in range(len(Capacities[fuel])))
                        >= solver.Sum(y[f_idx, i+1, k_idx, t_idx] for k_idx in range(len(Capacities[fuel])))
                )
                        
    # for f_idx, fuel in enumerate(Fuels):
    #     for i in range(num_tanks - 1):  # Iterate through tanks except the last one
    #         for t_idx in range(len(T)):
    #             # Ensure that tank i is open before tank i+1 can be open
    #             solver.Add(
    #                 solver.Sum(y[f_idx, i, k_idx, t_idx] for k_idx in range(len(Capacities[fuel]))) 
    #                 >= solver.Sum(y[f_idx, i+1, k_idx, t_idx] for k_idx in range(len(Capacities[fuel])))
    #             )


    # Export the model to a file (optional)
    with open("facility_location_model.lp", "w") as lp_file:
        lp_file.write(solver.ExportModelAsLpFormat(False))
        
    # Solve the model
    status = solver.Solve()

    # Prepare the results
    result_data = {'status': status, 'solution': {}, 'costs': {}}

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        for f_idx, fuel in enumerate(Fuels):
            fuel_data = {}
            for t_idx, year in enumerate(T):
                year_fuel = {}
                for i in range(num_tanks):
                    tank_data = {}
                    for k_idx, capacity in enumerate(Capacities[fuel]):
                        if (y[f_idx, i, k_idx, t_idx].solution_value() > 0.5 or
                            s[f_idx, i, k_idx, t_idx].solution_value() > 0.5 or
                            x[f_idx, i, k_idx, t_idx].solution_value() > 0.5):
                            tank_data[capacity] = {
                                'opened': int(y[f_idx, i, k_idx, t_idx].solution_value()),
                                'operating': int(s[f_idx, i, k_idx, t_idx].solution_value()),
                                'closed': int(x[f_idx, i, k_idx, t_idx].solution_value())
                            }
                    if tank_data:
                        year_fuel[f'Tank_{i+1}'] = tank_data
                if year_fuel:
                    fuel_data[year] = year_fuel
            if fuel_data:
                result_data['solution'][fuel] = fuel_data

        # Compute cost details for the solution
        for f_idx, fuel in enumerate(Fuels):
            cost_data = {}
            maintenance_rate = Costs[fuel]['maintenanceCost']
            decommissioning_rate = Costs[fuel]['decommissioningCost']
            initial_costs = Costs[fuel]['costs']
            change_rate = Costs[fuel]['changeRate']
            for t_idx, year in enumerate(T):
                year_cost = {}
                for i in range(num_tanks):
                    tank_cost = {}
                    for k_idx, capacity in enumerate(Capacities[fuel]):
                        dynamic_cost = round(initial_costs[k_idx] * ((1 + (change_rate / 100.0)) ** t_idx), -3)
                        maintenance_cost = round(initial_costs[k_idx] * (maintenance_rate / 100.0), -3)
                        decommissioning_cost = round(initial_costs[k_idx] * (decommissioning_rate / 100.0), -3)
                        
                        if fuel == "MGO" and t_idx == 0:
                            if y[f_idx, i, k_idx, t_idx].solution_value() > 0.5:
                                tank_cost[capacity] = {
                                    'opened': 0,
                                    'operating': maintenance_cost,
                                    'closed': 0
                                }
                        else:
                            if (y[f_idx, i, k_idx, t_idx].solution_value() > 0.5 or
                                s[f_idx, i, k_idx, t_idx].solution_value() > 0.5 or
                                x[f_idx, i, k_idx, t_idx].solution_value() > 0.5):
                                tank_cost[capacity] = {
                                    'opened': int(y[f_idx, i, k_idx, t_idx].solution_value() * dynamic_cost),
                                    'operating': int(s[f_idx, i, k_idx, t_idx].solution_value() * maintenance_cost),
                                    'closed': int(x[f_idx, i, k_idx, t_idx].solution_value() * decommissioning_cost)
                                }
                    if tank_cost:
                        year_cost[f'Tank_{i+1}'] = tank_cost
                if year_cost:
                    cost_data[year] = year_cost
            if cost_data:
                result_data['costs'][fuel] = cost_data

    # Output results in JSON format
    print(json.dumps(result_data))
    with open("output_data.txt", "w") as out_file:
        out_file.write(json.dumps(result_data))

if __name__ == '__main__':
    input_text = sys.stdin.read()
    input_data = json.loads(input_text)
    with open("input_data.txt", "w") as in_file:
        in_file.write(input_text)
    solve_facility_location(input_data)