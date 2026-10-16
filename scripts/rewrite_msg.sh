#!/bin/bash

# Script to rewrite commit messages for conventional commits
# Makes lowercase, truncates to 60 chars, adds 'feat:' if no type

COMMIT_MSG="$1"

# If no conventional type, add 'feat:'
if ! echo "$COMMIT_MSG" | grep -qE '^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: '; then
    COMMIT_MSG="feat: $COMMIT_MSG"
fi

# Make lowercase
COMMIT_MSG=$(echo "$COMMIT_MSG" | tr '[:upper:]' '[:lower:]')

# Truncate to 60 chars
COMMIT_MSG=$(echo "$COMMIT_MSG" | cut -c1-60)

# Occasionally add a symbol
if [ $((RANDOM % 3)) -eq 0 ]; then
    symbols=(" →" " /" " _" " |" " -" " ~" " +" " *")
    random_symbol=${symbols[$RANDOM % ${#symbols[@]}]}
    COMMIT_MSG="$COMMIT_MSG$random_symbol"
fi

echo "$COMMIT_MSG"
