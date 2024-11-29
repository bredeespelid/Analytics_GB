# Sett
set LOCATIONS ordered;
set PRIORITIES ordered;

# Parametere
param travel_time{LOCATIONS, LOCATIONS} default Infinity;
param unloading_time{LOCATIONS};
param opening_time{PRIORITIES};
param buffer_time;

# Variabler
var arrival_time{LOCATIONS} >= 0;

# Objective
maximize Latest_Departure: arrival_time[first(LOCATIONS)];

# Constraints
subject to Last_Arrival:
    arrival_time[last(LOCATIONS)] = opening_time[last(PRIORITIES)] - buffer_time;

subject to Travel_Time {i in LOCATIONS, j in LOCATIONS: ord(j) = ord(i) + 1}:
    arrival_time[i] = arrival_time[j] - travel_time[i,j] - unloading_time[i];