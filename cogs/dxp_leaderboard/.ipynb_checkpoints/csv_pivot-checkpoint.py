import pandas as pd
from datetime import datetime

# Step 1: Read the CSV
df = pd.read_csv("formatted_skill_data_cron.csv")


print("Columns in df:", df.columns)
print(df.head())

df['time_retrieved'] = pd.to_datetime(df['time_retrieved'])

# Step 2: Create a 'day-hour' column
#df['datetime'] = pd.to_datetime(df['datetime'])
df['day_hour'] = df['time_retrieved'].dt.floor('H')  # Rounds to the nearest hour

# Step 3: Pivot the data
pivoted_df = df.pivot_table(
    index=['username', 'day_hour'],  # Group by username and day-hour
    columns='skill',                 # Each skill becomes a separate column
    values=['experience', 'level', 'rank'],  # Values to include
    aggfunc='max'                    # Use 'max' to handle duplicates if necessary
)


# Step 4: Flatten the MultiIndex columns
pivoted_df.columns = ['_'.join(col).strip() for col in pivoted_df.columns.values]

# Step 5: Reset the index to get a clean DataFrame
pivoted_df.reset_index(inplace=True)

# Step 6: Save to a new CSV
pivoted_df.to_csv("transformed_skill_data.csv", index=False)

