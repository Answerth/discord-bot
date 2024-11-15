#!/bin/bash

# Initialize Conda
source ~/miniconda3/etc/profile.d/conda.sh

# Step 1: Backup the Conda environment
dir=~/discordbot10s/env
filename="environment_$(date +%Y-%m-%d).yaml"

if conda env export > "$dir/$filename"; then
  echo "Success: File successfully created at $dir/$filename"
else
  echo "Error: Failed to create the backup file."
fi

# old: conda env export > ~/discordbot10s/env/environment_$(date +%Y-%m-%d).yaml

# Step 2: Display Git status
cd /home/discordbeta/discordbot10s
echo "Current Git status:"
git status

# Step 3: Prompt for GitHub commit
while true; do
    read -p "Commit to GitHub? (y/n): " choice
    case "$choice" in
        [Yy]* )
            # Prompt for a commit message
            read -p "Enter commit message (or press Enter for default): " commit_message
            
            # Set default message if no input provided
            if [ -z "$commit_message" ]; then
                commit_message="Backup and update before logout on $(date)"
            fi
            
            # Proceed with Git commit and push
            git add .
            git commit -m "$commit_message"
            git push origin main
            break
            ;;
        [Nn]* )
            echo "Skipping GitHub commit."
            break
            ;;
        * )
            echo "Please answer yes (y) or no (n)."
            ;;
    esac
done

# Step 4: Run Python script in the background with nohup and disown
# nohup python /home/discordbeta/discordbot10s/bot_test_with_drop_alerter.py &
