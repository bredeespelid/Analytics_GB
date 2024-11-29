# Sett
set LOCATIONS ordered;
set PRIORITIES ordered;

# Parametere
param travel_time{LOCATIONS, LOCATIONS} default Infinity;
param unloading_time{LOCATIONS};
param opening_time{PRIORITIES};
param buffer_time;
param location_priority{LOCATIONS} symbolic in PRIORITIES;

# Variabler
var arrival_time{LOCATIONS} >= 0;

# Objective
maximize Latest_Departure: arrival_time[first(LOCATIONS)];

# Constraints
subject to Last_Arrival:
    arrival_time[last(LOCATIONS)] + unloading_time[last(LOCATIONS)] <= opening_time[location_priority[last(LOCATIONS)]] - buffer_time;

subject to Travel_Time {i in LOCATIONS, j in LOCATIONS: ord(j) = ord(i) + 1}:
    arrival_time[i] + unloading_time[i] + travel_time[i,j] = arrival_time[j];

subject to Priority_Constraints {i in LOCATIONS}:
    arrival_time[i] + unloading_time[i] <= opening_time[location_priority[i]] - buffer_time;
    
    subject to Arrival_Floyen_06_42:
    arrival_time['Fløyen'] = 405;