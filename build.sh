#!/bin/bash

# 1. Force the environment variables Git and uv need
export HOME=/root
export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/.local/bin

# 2. Move to the correct directory
cd /root/neovimmm || exit

# 3. Run harvest.py using the full path to uv for extra safety
/root/.local/bin/uv run harvest.py >> /root/neovimmm/build.log 2>&1

# 4. Standard Git workflow
git add .
# We use '|| true' so the script doesn't exit if there are no changes
git commit --author="tomdeneire.be <37420199+TomDeneire@users.noreply.github.com>" -m "build $(date +'%Y-%m-%d %H:%M')" || true

# 5. Token-based push
TOKEN=$(tr -d '\n\r ' < /root/neovimmm/secretkey)
git push "https://TomDeneire:${TOKEN}@github.com/TomDeneire/neovimmm.git" main >> /root/neovimmm/build.log 2>&1
