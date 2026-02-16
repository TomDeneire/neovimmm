#!/bin/bash
# Move to script directory
cd "$(dirname "$0")" || exit

# 1. Use absolute path for uv (Check 'which uv' to verify this path)
# 2. Add logging to see errors
/root/.local/bin/uv run harvest.py >> build.log 2>&1

git add .

# Avoid 'nothing to commit' errors stopping the script
git commit -m "build $(date)" || echo "Nothing to commit"

# Strip whitespace from token
TOKEN=$(tr -d '\n\r ' < secretkey)

# Push and capture output
git push "https://TomDeneire:${TOKEN}@github.com/TomDeneire/neovimmm.git" main >> build.log 2>&1
