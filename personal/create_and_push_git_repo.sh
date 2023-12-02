#!/bin/bash

# Description: This script creates a new Git repository, initializes it, and pushes it to GitHub.
# Usage: ./create_and_push_git_repo.sh [repository-name]

# Setup:

# 1. To setup gh on macOS:
# brew install gh
# gh auth login

# 2. To give the script permission to execute:
# chmod +x create_and_push_git_repo.sh

# Function to handle errors
error_exit()
{
  echo "$1" 1>&2
  exit 1
}

# Check for the repository name argument
if [ "$#" -ne 1 ]; then
  error_exit "Usage: $0 [repository-name]"
fi

REPO_NAME=$1
echo "Creating a new repository named $REPO_NAME"

# Create a new directory for the repository
mkdir "$REPO_NAME" || error_exit "Failed to create directory"

# Move into the directory
cd "$REPO_NAME" || error_exit "Failed to enter directory"

# Initialize the repository
git init || error_exit "Failed to initialize git repository"

# Create an initial file (optional)
echo "# $REPO_NAME" > README.md
git add README.md
git commit -m "Initial commit" || error_exit "Failed to make initial commit"

# Create a new repository on GitHub
# Requires GitHub CLI (gh) to be installed and authenticated
gh repo create "$REPO_NAME" --public --source=. --remote=origin --push || error_exit "Failed to create GitHub repository"

echo "Repository $REPO_NAME created and pushed to GitHub successfully."
