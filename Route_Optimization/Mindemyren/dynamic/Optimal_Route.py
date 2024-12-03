import json
import numpy as np
import pandas as pd
from pyomo.environ import *

# Load JSON data from file
with open('/content/results.json', 'r') as file:
    trips = json.load(file)

# Define the mapping of full addresses to simplified names
address_mapping = {
    'Minde allé 35, Bergen, Norway': 'Mindemyren',
    'Vestre Torggaten 2, Bergen, Norway': 'Vestre Torggaten',
    'Vetrlidsallmenningen 19, Bergen, Norway': 'Fløyen',
    'Marken 1 5017, Bergen, Norway': 'Marken',
    'Nedre Korskirkeallmenningen 12, Bergen, Norway': 'Korskirken',
    'Christies gate 10 5016, Bergen, Norway': 'Festplassen',
    'Inndalsveien 6, Bergen, Norway': 'Kronstad',
    'Muséplassen 3, Bergen, Norway': 'Christie',
    'Damsgårdsveien 59, Bergen, Norway': 'Fløttmannsplassen',
    'Myrdalsvegen 2, Bergen, Norway': 'Horisont',
    'Lagunen Storsenter 5239, Bergen, Norway': 'Lagunen'
}

# Get unique locations using the simplified names
locations = sorted(set(address_mapping[trip["origin"]] for trip in trips if trip["origin"] in address_mapping) | 
                   set(address_mapping[trip["destination"]] for trip in trips if trip["destination"] in address_mapping))

# Initialize time matrix
time_matrix = pd.DataFrame(np.inf, index=locations, columns=locations)

# Fill the time matrix with durations
for trip in trips:
    if trip["origin"] in address_mapping and trip["destination"] in address_mapping:
        origin = address_mapping[trip["origin"]]
        destination = address_mapping[trip["destination"]]
        duration = int(trip["duration"].replace(" mins", "").replace(" min", ""))
        time_matrix.loc[origin, destination] = duration

# Ensure diagonal is zero (no time needed to travel to the same location)
np.fill_diagonal(time_matrix.values, 0)

# Create a model
model = ConcreteModel()

# Sets
bakeries = time_matrix.index.tolist()
days = ['Monday']

model.BAKERIES = Set(initialize=bakeries)
model.DAYS = Set(initialize=days)

# Parameters
time_data = {(i, j): time_matrix.loc[i, j] for i in bakeries for j in bakeries}

priority_data = {
    ('Monday', 'Kronstad'): 1,
    ('Monday', 'Marken'): 2,
    ('Monday', 'Fløttmannsplassen'): 3,
    ('Monday', 'Fløyen'): 3,
    ('Monday', 'Festplassen'): 3,
    ('Monday', 'Vestre Torggaten'): 3,
    ('Monday', 'Korskirken'): 4,
    ('Monday', 'Christie'): 4,
    ('Monday', 'Lagunen'): 5,
    ('Monday', 'Horisont'): 6
}

# Add unloading times
unloading_times = {bakery: 15 if bakery == 'Lagunen' else 10 for bakery in bakeries}
unloading_times['Mindemyren'] = 0  # No unloading time for Mindemyren

model.TIME = Param(model.BAKERIES, model.BAKERIES, initialize=time_data, default=float('inf'))
model.PRIORITY = Param(model.DAYS, model.BAKERIES, initialize=priority_data, default=0)
model.UNLOADING = Param(model.BAKERIES, initialize=unloading_times)

# Variables
model.x = Var(model.DAYS, model.BAKERIES, model.BAKERIES, within=Binary)
model.u = Var(model.DAYS, model.BAKERIES, within=NonNegativeReals)

# Objective: Minimize total time (including unloading) and prioritize early openings for each day
def objective_rule(model):
    return sum(
        (model.TIME[i,j] + model.UNLOADING[j]) * model.x[d,i,j] 
        for d in model.DAYS for i in model.BAKERIES for j in model.BAKERIES if i != j
    ) + sum(
        model.PRIORITY[d,i] * model.x[d,i,j] 
        for d in model.DAYS for i in model.BAKERIES for j in model.BAKERIES 
        if i != j and i != 'Mindemyren' and j != 'Mindemyren'
    )
model.TotalTime = Objective(rule=objective_rule, sense=minimize)

# Constraints (same as before)
def visit_once_per_day_rule(model, d, i):
    if i != 'Mindemyren':
        return sum(model.x[d,i,j] for j in model.BAKERIES if j != i) == 1
    return Constraint.Skip

def depart_once_per_day_rule(model, d, j):
    if j != 'Mindemyren':
        return sum(model.x[d,i,j] for i in model.BAKERIES if i != j) == 1
    return Constraint.Skip

def subtour_elimination_rule(model, d, i, j):
    if i != j and i != 'Mindemyren' and j != 'Mindemyren':
        return model.u[d,i] - model.u[d,j] + len(bakeries) * model.x[d,i,j] <= len(bakeries) - 1
    return Constraint.Skip

def start_at_mindemyren_rule(model, d):
    return sum(model.x[d,'Mindemyren',j] for j in model.BAKERIES if j != 'Mindemyren') == 1

def end_at_mindemyren_rule(model, d):
    return sum(model.x[d,i,'Mindemyren'] for i in model.BAKERIES if i != 'Mindemyren') == 1

def mindemyren_first_rule(model, d):
    return model.u[d,'Mindemyren'] == 0

def visit_priority_one_first_rule(model, d):
    return sum(model.x[d,'Mindemyren',j] for j in model.BAKERIES if j != 'Mindemyren' and model.PRIORITY[d,j] == 1) == 1

def maintain_priority_order_rule(model, d, i, j):
    if i != j and i != 'Mindemyren' and j != 'Mindemyren':
        return model.PRIORITY[d,i] <= model.PRIORITY[d,j] + len(bakeries) * (1 - model.x[d,i,j])
    return Constraint.Skip

def horisont_last_before_mindemyren_rule(model, d):
    return model.x[d,'Horisont','Mindemyren'] == 1

# Adding constraints to the model
model.VisitOncePerDay = Constraint(model.DAYS, model.BAKERIES, rule=visit_once_per_day_rule)
model.DepartOncePerDay = Constraint(model.DAYS, model.BAKERIES, rule=depart_once_per_day_rule)
model.SubtourElimination = Constraint(model.DAYS, model.BAKERIES, model.BAKERIES, rule=subtour_elimination_rule)
model.StartAtMindemyren = Constraint(model.DAYS, rule=start_at_mindemyren_rule)
model.EndAtMindemyren = Constraint(model.DAYS, rule=end_at_mindemyren_rule)
model.MindemyrenFirst = Constraint(model.DAYS, rule=mindemyren_first_rule)
model.VisitPriorityOneFirst = Constraint(model.DAYS, rule=visit_priority_one_first_rule)
model.MaintainPriorityOrder = Constraint(model.DAYS, model.BAKERIES, model.BAKERIES, rule=maintain_priority_order_rule)
model.HorisontLastBeforeMindemyren = Constraint(model.DAYS, rule=horisont_last_before_mindemyren_rule)

# Solve the problem
solver = SolverFactory('glpk')
results = solver.solve(model)

# Check solver status and create DataFrame
if results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:
    route_data = []
    
    for d in days:
        current_location = "Mindemyren"
        total_time = 0
        step = 1
        
        while True:
            next_location = None
            for j in bakeries:
                if current_location != j and value(model.x[d,current_location,j]) > 0.5:
                    next_location = j
                    break
            
            if next_location is None or next_location == "Mindemyren":
                break
            
            travel_time = value(model.TIME[current_location, next_location])
            unloading_time = value(model.UNLOADING[next_location])
            priority = value(model.PRIORITY[d, next_location])
            total_time += travel_time + unloading_time
            
            route_data.append({
                'Day': d,
                'Step': step,
                'From': current_location,
                'To': next_location,
                'Travel Time (mins)': travel_time,
                'Unloading Time (mins)': unloading_time,
                'Priority': priority,
                'Cumulative Time (mins)': total_time
            })
            
            current_location = next_location
            step += 1
        
        # Add final return to Mindemyren
        final_travel_time = value(model.TIME[current_location, "Mindemyren"])
        total_time += final_travel_time
        route_data.append({
            'Day': d,
            'Step': step,
            'From': current_location,
            'To': "Mindemyren",
            'Travel Time (mins)': final_travel_time,
            'Unloading Time (mins)': 0,
            'Priority': 0,
            'Cumulative Time (mins)': total_time
        })
    
    # Create DataFrame from route_data
    route_df = pd.DataFrame(route_data)
    
    # Display the DataFrame
    print(route_df)
    

def add_opening_hours(route_df, priority_opening_times):
    route_df['Opening Hour (mins from midnight)'] = route_df['Priority'].map(priority_opening_times)
    return route_df

# Assuming route_df is your existing DataFrame
# If not, you'll need to create it first

# Define the priority opening times
priority_opening_times = {
    1: 360,  # KronstadX opens at 06:00
    2: 390,  # Fløttmannsplassen opens at 06:30
    3: 420,  # Marken opens at 07:00
    4: 450,  # VestreTorggaten opens at 07:30
    5: 480,  # Lagunen opens at 08:00
    6: 540   # Horisont opens at 09:00
}

# Add opening hours to the DataFrame
updated_route_df = add_opening_hours(route_df, priority_opening_times)

# Definer adressemappingen (reversert for å matche 'From' og 'To' kolonner)
address_mapping_reversed = {
    'Mindemyren': 'Minde allé 35, Bergen, Norway',
    'Vestre Torggaten': 'Vestre Torggaten 2, Bergen, Norway',
    'Fløyen': 'Vetrlidsallmenningen 19, Bergen, Norway',
    'Marken': 'Marken 1 5017, Bergen, Norway',
    'Korskirken': 'Nedre Korskirkeallmenningen 12, Bergen, Norway',
    'Festplassen': 'Christies gate 10 5016, Bergen, Norway',
    'Kronstad': 'Inndalsveien 6, Bergen, Norway',
    'Christie': 'Muséplassen 3, Bergen, Norway',
    'Fløttmannsplassen': 'Damsgårdsveien 59, Bergen, Norway',
    'Horisont': 'Myrdalsvegen 2, Bergen, Norway',
    'Lagunen': 'Lagunen Storsenter 5239, Bergen, Norway'
}

# Legg til adressekolonner i dataframen
updated_route_df['From Address'] = updated_route_df['From'].map(address_mapping_reversed)
updated_route_df['To Address'] = updated_route_df['To'].map(address_mapping_reversed)

# Vis den oppdaterte dataframen
print(updated_route_df)


