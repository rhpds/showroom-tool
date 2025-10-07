#!/bin/bash

# agv-iterator.sh
# Script to iterate through a CSV file and set environment variables for each row
# Usage: ./agv-iterator.sh <csv_file>

set -euo pipefail # Exit on error, undefined variables, and pipe failures

# Function to display usage
usage() {
  echo "Usage: $0 <csv_file>"
  echo "  csv_file: Path to the CSV file with columns: directory,git_url,git_ref"
  echo ""
  echo "Example:"
  echo "  $0 ../workspace/repos.csv"
  exit 1
}

# Check if CSV file argument is provided
if [ $# -ne 1 ]; then
  echo "Error: CSV file path is required"
  usage
fi

CSV_FILE="$1"

# Check if file exists
if [ ! -f "$CSV_FILE" ]; then
  echo "Error: File '$CSV_FILE' not found"
  exit 1
fi

# Check if file is readable
if [ ! -r "$CSV_FILE" ]; then
  echo "Error: Cannot read file '$CSV_FILE'"
  exit 1
fi

echo "Processing CSV file: $CSV_FILE"
echo "=================================="

# Counter for rows processed
row_count=0

# Read the CSV file line by line, skipping the header
tail -n +2 "$CSV_FILE" | while IFS=',' read -r directory git_url git_ref; do
  # Increment counter
  ((row_count++))

  # Trim any leading/trailing whitespace
  directory=$(echo "$directory" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  git_url=$(echo "$git_url" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  git_ref=$(echo "$git_ref" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Set the environment variables
  export DIRECTORY="$directory"
  export GIT_URL="$git_url"
  export GIT_REF="$git_ref"

  # Print the variables for this iteration
  echo "Row $row_count:"
  echo "  DIRECTORY: $DIRECTORY"
  echo "  GIT_URL: $GIT_URL"
  echo "  GIT_REF: $GIT_REF"
  echo "---"

  # Add your custom processing logic here
  # Examples:
  # - Clone the repository: git clone "$GIT_URL" -b "$GIT_REF" /tmp/repo
  # - Change to directory: cd "$DIRECTORY"
  # - Run specific commands with the environment variables

  # Placeholder for custom processing
  echo "  Processing entry $row_count..."
  cd "$DIRECTORY"
  echo $PWD
  showroom-tool description --git-repo "$GIT_URL" --git-ref "$GIT_REF" --output adoc >ai-description.adoc
  showroom-tool summary --git-repo "$GIT_URL" --git-ref "$GIT_REF" --output adoc >ai-summary.adoc
  # Your code here

done

echo "=================================="
echo "Processing complete!"
