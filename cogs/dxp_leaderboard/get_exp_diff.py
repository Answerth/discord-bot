import pandas as pd

# Step 1: Read the transformed CSV
df = pd.read_csv("transformed_skill_data.csv")

# Step 2: Convert 'day_hour' to datetime
df['day_hour'] = pd.to_datetime(df['day_hour'])

# Step 3: Filter data for the starting time and the latest time for each username
start_time = pd.Timestamp("2024-11-15 12:00:00")
latest_df = df.sort_values(by=['username', 'day_hour']).groupby('username').last()
start_df = df[df['day_hour'] == start_time].set_index('username')

# Step 4: Calculate the experience difference
latest_df = latest_df[['experience_Overall']].rename(columns={'experience_Overall': 'latest_experience'})
start_df = start_df[['experience_Overall']].rename(columns={'experience_Overall': 'start_experience'})
result_df = latest_df.join(start_df)
result_df['experience_diff'] = result_df['latest_experience'] - result_df['start_experience']

# Step 5: Filter and sort the results
result_df = result_df[result_df['experience_diff'] != 0]  # Exclude rows where experience_diff == 0
result_df = result_df.sort_values(by='experience_diff', ascending=False)  # Sort by experience_diff

result_df[['latest_experience', 'start_experience', 'experience_diff']] = result_df[['latest_experience', 'start_experience', 'experience_diff']].applymap(lambda x: f"{x:,}")


# Step 6: Prepare a Markdown table
markdown_table = result_df[['latest_experience', 'start_experience', 'experience_diff']].reset_index().to_markdown(index=False)

# Step 7: Display the Markdown table
print(markdown_table)

