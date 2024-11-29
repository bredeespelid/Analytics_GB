
# Sets
set BAKERIES;
set DAYS ordered;

# Parameters
param DISTANCE{BAKERIES, BAKERIES};
param PRIORITY{DAYS, BAKERIES};
param current symbolic;

# Variables
var x{DAYS, BAKERIES, BAKERIES} binary;
var u{DAYS, BAKERIES} >= 0;

# Objective: Minimize total distance and prioritize early openings for each day
minimize TotalDistance:
    sum{d in DAYS, i in BAKERIES, j in BAKERIES: i != j} 
        DISTANCE[i,j] * x[d,i,j] +
    sum{d in DAYS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'} 
        PRIORITY[d,i] * x[d,i,j];

# Constraints
subject to VisitOncePerDay {d in DAYS, i in BAKERIES: i != 'Mindemyren'}:
    sum{j in BAKERIES: j != i} x[d,i,j] = 1;

subject to DepartOncePerDay {d in DAYS, j in BAKERIES: j != 'Mindemyren'}:
    sum{i in BAKERIES: i != j} x[d,i,j] = 1;

subject to SubtourElimination {d in DAYS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'}:
    u[d,i] - u[d,j] + card(BAKERIES) * x[d,i,j] <= card(BAKERIES) - 1;

subject to StartAtMindemyren {d in DAYS}:
    sum{j in BAKERIES: j != 'Mindemyren'} x[d,'Mindemyren',j] = 1;

subject to EndAtMindemyren {d in DAYS}:
    sum{i in BAKERIES: i != 'Mindemyren'} x[d,i,'Mindemyren'] = 1;

subject to MindemyrenFirst {d in DAYS}:
    u[d,'Mindemyren'] = 0;

# Linear version of VisitPriorityOneFirst
subject to VisitPriorityOneFirst {d in DAYS}:
    sum{j in BAKERIES: j != 'Mindemyren' and PRIORITY[d,j] = 1} x[d,'Mindemyren',j] = 1;

# Maintain priority order
subject to MaintainPriorityOrder {d in DAYS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'}:
    PRIORITY[d,i] <= PRIORITY[d,j] + card(BAKERIES) * (1 - x[d,i,j]);

# New constraint: Horisont must be the last stop before Mindemyren
subject to HorisontLastBeforeMindemyren {d in DAYS}:
    x[d,'Horisont','Mindemyren'] = 1;