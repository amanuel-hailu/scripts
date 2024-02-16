#!/bin/bash

git fetch --all

# Directory for temporary files, one per author
tempDir=$(mktemp -d)

# List all remote branches excluding staging and prod
git for-each-ref --format='%(refname:short)' refs/remotes/ | grep -Ev '^(staging|prod)$' | while read branch; do
    # Ensure we're using the fully qualified name for consistency
    qualifiedBranch="origin/${branch#origin/}"

    # Find the first non-merge commit on this branch not by "staging" or "prod"
    firstCommitAuthor=$(git log $qualifiedBranch --not origin/staging origin/prod --no-merges --format="%an" -- | tail -n 1)

    if [ ! -z "$firstCommitAuthor" ]; then
        # Normalize author name to use as filename
        authorFile=$(echo "$firstCommitAuthor" | tr ' ' '_')

        # Write branch to author's temp file
        echo "$branch" >>"$tempDir/$authorFile"
    fi
done

# Display branches by author, with counts
for authorFile in "$tempDir"/*; do
    author=$(basename "$authorFile" | tr '_' ' ')
    branchCount=$(wc -l <"$authorFile")
    echo "*********"
    echo "$author - Total Branches: $branchCount"
    while read branch; do
        echo "- $branch"
    done <"$authorFile"
    echo "*********"
done

# Clean up
rm -r "$tempDir"
