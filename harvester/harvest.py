import sys
import requests
import json
import os

QUERY_URL = "https://api.github.com/search/repositories?q=neovim"

SECRET_KEY = ""
with open("secretkey", "r") as reader:
    SECRET_KEY = reader.read().strip()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {SECRET_KEY}",
    "X-GitHub-Api-Version": "2022-11-28",
}

DATA_DIR = "/home/tdeneire/Dropbox/code/js/neovimmm"


def get_total():
    total_query = requests.get(QUERY_URL, headers=HEADERS).json()
    print(total_query)
    return total_query["total_count"]


def get_page(url):
    results = requests.get(url, headers=HEADERS).json()
    try:
        return results["items"]
    except Exception:
        return {}


result = []
pages = get_total() / 100
rounded = int(pages)
if rounded < pages:
    rounded += 1
for i in range(0, rounded):
    url = f"{QUERY_URL}&page={i}&per_page=100"
    page_result = get_page(url)
    if page_result == {}:
        break
    for item in page_result:
        if item["private"]:
            continue
        if item["archived"]:
            continue
        if item["disabled"]:
            continue
        repo = {}
        repo["full_name"] = item["full_name"]
        # "watchers_count" is unreliable...
        for key in ["name", "html_url", "description", "updated_at",
                    "forks_count", "language", "stargazers_count"]:
            repo.update({key: item[key]})
        if item["license"]:
            repo.update({"license_name": item["license"]["name"]})
        result.append(repo)
    print(url, file=sys.stderr)

with open(os.path.join(DATA_DIR, "data.json"), "w") as writer:
    writer.write(json.dumps(result, indent=4))

for count_type in ["stargazers", "forks"]:
    result = sorted(result, key=lambda x: x[(count_type + "_count")], reverse=True)
    for i, r in enumerate(result):
        r.update({(count_type + "_sort"): i})
    p = os.path.join(DATA_DIR, f"{count_type}.json")
    with open(p, "w") as writer:
        writer.write(json.dumps(result[0:99], indent=4))
