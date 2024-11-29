# Sets
set BAKERIES;          # Mengde av alle bakerier inkludert depotet ('Mindemyren')
set DAYS ordered;      # Mengde av dager
set TRUCKS;            # Ny mengde for lastebiler (f.eks., TRUCKS := {'Truck1', 'Truck2'})

# Parameters
param DISTANCE{BAKERIES, BAKERIES};  # Avstand mellom bakerier
param PRIORITY{DAYS, BAKERIES};     # Prioritet for å besøke bakerier
param current symbolic;

# Variables
var x{DAYS, TRUCKS, BAKERIES, BAKERIES} binary;  # Besøker lastebil k fra i til j på dag d
var u{DAYS, TRUCKS, BAKERIES} >= 0;             # Sekvensvariabel for subtur-eliminering

# Objective: Minimize total distance and prioritize early openings
minimize TotalDistance:
    sum{d in DAYS, k in TRUCKS, i in BAKERIES, j in BAKERIES: i != j} 
        DISTANCE[i,j] * x[d,k,i,j] +
    sum{d in DAYS, k in TRUCKS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'} 
        PRIORITY[d,i] * x[d,k,i,j];

# Constraints

# 1. Hvert bakeri besøkes nøyaktig én gang per dag av én lastebil
subject to VisitOncePerDay {d in DAYS, i in BAKERIES: i != 'Mindemyren'}:
    sum{k in TRUCKS, j in BAKERIES: j != i} x[d,k,i,j] = 1;

# 2. Hver lastebil forlater hvert bakeri én gang
subject to DepartOncePerDay {d in DAYS, k in TRUCKS, j in BAKERIES: j != 'Mindemyren'}:
    sum{i in BAKERIES: i != j} x[d,k,i,j] = sum{i in BAKERIES: i != j} x[d,k,j,i];

# 3. Subtur-eliminering for hver lastebil
subject to SubtourElimination {d in DAYS, k in TRUCKS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'}:
    u[d,k,i] - u[d,k,j] + card(BAKERIES) * x[d,k,i,j] <= card(BAKERIES) - 1;

# 4. Hver lastebil starter fra depotet
subject to StartAtMindemyren {d in DAYS, k in TRUCKS}:
    sum{j in BAKERIES: j != 'Mindemyren'} x[d,k,'Mindemyren',j] = 1;

# 5. Hver lastebil returnerer til depotet
subject to EndAtMindemyren {d in DAYS, k in TRUCKS}:
    sum{i in BAKERIES: i != 'Mindemyren'} x[d,k,i,'Mindemyren'] = 1;

# 6. Depotet er alltid første stopp for hver lastebil
subject to MindemyrenFirst {d in DAYS, k in TRUCKS}:
    u[d,k,'Mindemyren'] = 0;

# 7. Prioritér bakerier med høyere prioritet
subject to MaintainPriorityOrder {d in DAYS, k in TRUCKS, i in BAKERIES, j in BAKERIES: i != j and i != 'Mindemyren' and j != 'Mindemyren'}:
    PRIORITY[d,i] <= PRIORITY[d,j] + card(BAKERIES) * (1 - x[d,k,i,j]);

# 8. "Horisont" må være siste stopp før depotet for en av lastebilene
subject to HorisontLastBeforeMindemyren {d in DAYS}:
    sum{k in TRUCKS} x[d,k,'Horisont','Mindemyren'] = 1;

