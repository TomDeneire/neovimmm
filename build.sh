cd /home/tdeneire/Dropbox/code/js/neovimmm || exit
uv run harvest.py
git add .
git commit -m "build"
git push
