import sys
import requests
import json

QUERY_URL = "https://api.github.com/search/repositories?q=neovim"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer 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",
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


if __name__ == "__main__":
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

    with open("result.json", "w") as writer:
        writer.write(json.dumps(result, indent=4))

    for count_type in ["stargazers", "forks"]:
        result = sorted(result, key=lambda x: x[(count_type + "_count")], reverse=True)
        for i, r in enumerate(result):
            r.update({(count_type + "_sort"): i})
        with open(f"{count_type}.json", "w") as writer:
            writer.write(json.dumps(result[0:99], indent=4))
