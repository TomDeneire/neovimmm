import datetime
import re
import sys
import requests
import json

QUERY_URL = "https://api.github.com/search/repositories?q=neovim"

SECRET_KEY = ""
with open("secretkey", "r") as reader:
    SECRET_KEY = reader.read().strip()

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {SECRET_KEY}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_total():
    total_query = requests.get(QUERY_URL, headers=HEADERS).json()
    return total_query["total_count"]


def get_page(url):
    results = requests.get(url, headers=HEADERS).json()
    try:
        return results["items"]
    except Exception:
        return {}

def to_int(v, default=0):
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v == "":
            return default
        # laat ook "1,234" of "1_234" toe
        v = v.replace(",", "").replace("_", "")
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


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
                    "forks_count", "language", "stargazers_count", "created_at"]:
            data = item[key]
            if not data:
                data = ""
            repo.update({key: data})
        if item["license"]:
            repo.update({"license_name": item["license"]["name"]})
        result.append(repo)
    print(url, file=sys.stderr)

with open("data.json", "w") as writer:
    writer.write(json.dumps(result, indent=4))

for count_type in ["stargazers_count", "forks_count", "created_at"]:
    if count_type == "created_at":
        result = sorted(
            result,
            key=lambda x: datetime.datetime.fromisoformat(
                (x.get("created_at") or "1970-01-01T00:00:00Z").replace("Z", "")
            ),
            reverse=True
        )
    else:
        result = sorted(
            result,
            key=lambda x: to_int(x.get(count_type)),
            reverse=True
        )

    for i, r in enumerate(result):
        r[count_type + "_sort"] = i

    p = count_type.replace("_count", "") + ".json"
    with open(p, "w") as writer:
        json.dump(result[:99], writer, indent=4)

with open("index.html", "r") as reader:
    index = reader.read()
    regex = re.compile(r'<span> :: Update.*</span>')
    date = str(datetime.datetime.now()).split(" ")[0]
    index = re.sub(regex, f"<span> :: Update {date}</span>", index)

with open("index.html", "w") as writer:
    writer.write(index)
