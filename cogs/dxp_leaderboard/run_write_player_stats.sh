#!/bin/bash
# Load Conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate discordbeta

# Change to the directory where the script is located
cd /home/discordbeta/discordbot10s/cogs/dxp_leaderboard

# Run the Python script
python write_player_stats_to_csv.py
