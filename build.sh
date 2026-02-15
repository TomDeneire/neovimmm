uv run harvest.py
git add .
git commit -m "build"
TOKEN=$(cat secretkey)
git push https://TomDeneire:${TOKEN}@github.com/TomDeneire/neovimmm.git main
