import pandas as pd
import math

# Input DataFrame
data = {
    "From": [
        "Mindemyren", "Kronstad", "Marken", "Fløyen", "Fløttmannsplassen",
        "Vestre Torggaten", "Festplassen", "Korskirken", "Christie", "Lagunen", "Horisont"
    ],
    "To": [
        "Kronstad", "Marken", "Fløyen", "Fløttmannsplassen", "Vestre Torggaten",
        "Festplassen", "Korskirken", "Christie", "Lagunen", "Horisont", "Mindemyren"
    ],
    "Travel Time (mins)": [3, 8, 2, 10, 7, 2, 3, 10, 17, 22, 16],
    "Unloading Time (mins)": [10, 10, 10, 10, 10, 10, 10, 10, 15, 10, 0],
    "Opening Hour (mins from midnight)": [360, 390, 420, 420, 420, 420, 450, 450, 480, 540, None]
}
df = pd.DataFrame(data)

# Helper function to format minutes into HH:MM
def format_time(minutes):
    hours = math.floor(minutes / 60)
    mins = minutes % 60
    return f"{hours:02}:{mins:02}"

# Calculate schedule starting from the last stop
schedule = []
current_time = 1440  # Default end of day time (24:00)

for i in reversed(df.index):
    row = df.iloc[i]
    from_location = row["From"]
    to_location = row["To"]
    travel_time = row["Travel Time (mins)"]
    unloading_time = row["Unloading Time (mins)"]
    opening_time = row["Opening Hour (mins from midnight)"]

    # Calculate the latest possible departure time considering opening time
    departure_time = current_time
    if not pd.isna(opening_time):
        departure_time = min(departure_time, opening_time)

    # Calculate arrival time
    arrival_time = departure_time - travel_time - unloading_time

    # Append to schedule
    schedule.append({
        "From": from_location,
        "To": to_location,
        "Opening Hour": format_time(opening_time) if not pd.isna(opening_time) else "N/A",
        "Arrival Time": arrival_time,
        "Minutes Driven": travel_time,
        "Unloading Time": unloading_time,
        "Departure Time": departure_time
    })

    # Update current time for the next iteration
    current_time = arrival_time

# Reverse the schedule to restore the correct order
schedule.reverse()

# Convert schedule to DataFrame
schedule_df = pd.DataFrame(schedule)

# Format arrival and departure times
schedule_df["Arrival Time"] = schedule_df["Arrival Time"].apply(format_time)
schedule_df["Departure Time"] = schedule_df["Departure Time"].apply(format_time)

# Rearrange columns to place Departure Time at the end
schedule_df = schedule_df[
    ["From", "To", "Arrival Time", "Opening Hour", "Minutes Driven", "Unloading Time", "Departure Time"]
]

# Output the final schedule
print(schedule_df)
