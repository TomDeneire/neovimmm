import datetime
import math
import re
import sys
import time
import requests
import json
from zoneinfo import ZoneInfo

# Multiple queries to bypass the 1,000-result-per-query GitHub API limit
SEARCH_BASE = 'https://api.github.com/search/repositories'
SPLIT_THRESHOLD = 950   # conservative; GitHub's total_count can be approximate
MAX_SPLIT_DEPTH = 10    # safety guard against runaway recursion
QUERIES = [
    'topic:neovim',
    'topic:neovim-plugin',
    'topic:nvim',
    'topic:nvim-plugin',
    'topic:neovim-lua',
    'topic:nvim-lua',
    'topic:neovim-colorscheme',
    'topic:neovim-theme',
    'topic:neovim-lua-plugin',
    'topic:neovim-plugins',
    'topic:nvim-plugins',
    'topic:neovim-plugin-lua',
]

SECRET_KEY = ''
with open('secretkey', 'r') as reader:
    SECRET_KEY = reader.read().strip()

HEADERS = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {SECRET_KEY}',
    'X-GitHub-Api-Version': '2022-11-28',
}


def get_total(query):
    url = f'{SEARCH_BASE}?q={query}'
    try:
        total_query = requests.get(url, headers=HEADERS).json()
        return total_query['total_count']
    except Exception as e:
        print(f'Error getting total for {query}: {e}', file=sys.stderr)
        return 0


def get_page(url):
    results = requests.get(url, headers=HEADERS).json()
    try:
        return results['items']
    except Exception:
        return {}


def to_int(v, default=0):
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v == '':
            return default
        # laat ook "1,234" of "1_234" toe
        v = v.replace(',', '').replace('_', '')
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def extract_repo(item):
    """Extract relevant fields from a GitHub API repo item."""
    repo = {}
    repo['full_name'] = item['full_name']
    # "watchers_count" is unreliable...
    for key in [
        'name',
        'html_url',
        'description',
        'updated_at',
        'forks_count',
        'language',
        'stargazers_count',
        'created_at',
    ]:
        data = item[key]
        if not data:
            data = ''
        repo.update({key: data})
    if item['license']:
        repo.update({'license_name': item['license']['name']})
    return repo


CONFIG_NAME_PATTERNS = re.compile(
    r'(dotfiles|\.config|nvimrc|neovimrc|nvim[-_]?config|neovim[-_]?config|my[-_]?nvim|my[-_]?neovim)',
    re.IGNORECASE,
)
CONFIG_TOPICS = {
    'dotfiles',
    'neovim-config',
    'neovim-configuration',
    'nvim-config',
    'nvim-configuration',
    'neovim-dotfiles',
    'nvim-dotfiles',
    'nvim-configs',
    'nvim-lua-config',
    'neovim-lua-config',
    'dotfile',
    'rice',
    'ricing',
}


def is_config_repo(item):
    """Heuristic to skip personal config/dotfile repos."""
    if not item.get('topics'):
        return True
    if CONFIG_NAME_PATTERNS.search(item['name']):
        return True
    if CONFIG_TOPICS & set(item.get('topics', [])):
        return True
    return False


def fetch_pages(query, total, seen):
    """Fetch all pages for a query that has <= 1000 results."""
    total = min(total, 1000)
    pages = math.ceil(total / 100)
    repos = []
    for i in range(1, pages + 1):
        url = f'{SEARCH_BASE}?q={query}&page={i}&per_page=100'
        page_result = get_page(url)
        if page_result == {}:
            break
        for item in page_result:
            if item['private']:
                continue
            if item['archived']:
                continue
            if item['disabled']:
                continue
            if is_config_repo(item):
                continue
            full_name = item['full_name']
            if full_name in seen:
                continue
            seen.add(full_name)
            repos.append(extract_repo(item))
        print(url, file=sys.stderr)
        # Respect GitHub search API rate limit (30 requests/minute)
        time.sleep(2.5)
    return repos


def fetch_with_date_split(query, start, end, seen, depth=0):
    """Recursively split a query by date range until each sub-range has <= SPLIT_THRESHOLD results."""
    date_query = f'{query}+created:{start}..{end}'
    time.sleep(2.5)
    total = get_total(date_query)
    print(
        f'{"  " * depth}Date split: {start}..{end} -> {total} results',
        file=sys.stderr,
    )

    if total <= SPLIT_THRESHOLD or depth >= MAX_SPLIT_DEPTH:
        if depth >= MAX_SPLIT_DEPTH and total > SPLIT_THRESHOLD:
            print(
                f'{"  " * depth}WARNING: max depth reached with {total} results, some may be lost',
                file=sys.stderr,
            )
        return fetch_pages(date_query, total, seen)

    # Bisect the date range
    start_date = datetime.date.fromisoformat(start)
    end_date = datetime.date.fromisoformat(end)
    mid_date = start_date + (end_date - start_date) // 2

    repos = []
    repos += fetch_with_date_split(
        query, start, mid_date.isoformat(), seen, depth + 1
    )
    repos += fetch_with_date_split(
        query,
        (mid_date + datetime.timedelta(days=1)).isoformat(),
        end,
        seen,
        depth + 1,
    )
    return repos


def fetch_query_results(query, seen):
    """Orchestrate fetching results for a single query, splitting by date if needed."""
    print(f'\n--- Query: {query} ---', file=sys.stderr)
    total = get_total(query)
    print(f'Total: {total}', file=sys.stderr)

    if total <= SPLIT_THRESHOLD:
        pages = math.ceil(total / 100)
        print(f'Pages: {pages}', file=sys.stderr)
        return fetch_pages(query, total, seen)

    print(
        f'Exceeds threshold ({SPLIT_THRESHOLD}), splitting by date...',
        file=sys.stderr,
    )
    today = datetime.date.today().isoformat()
    return fetch_with_date_split(query, '2014-01-01', today, seen)


seen = set()
result = []
for query in QUERIES:
    result += fetch_query_results(query, seen)

print(f'\nTotal unique repos: {len(result)}', file=sys.stderr)

with open('data.json', 'w') as writer:
    writer.write(json.dumps(result, indent=4))

for count_type in ['stargazers_count', 'forks_count', 'created_at']:
    if count_type == 'created_at':
        result = sorted(
            result,
            key=lambda x: datetime.datetime.fromisoformat(
                (x.get('created_at') or '1970-01-01T00:00:00Z').replace(
                    'Z', ''
                )
            ),
            reverse=True,
        )
    else:
        result = sorted(
            result, key=lambda x: to_int(x.get(count_type)), reverse=True
        )

    for i, r in enumerate(result):
        r[count_type + '_sort'] = i

    p = count_type.replace('_count', '') + '.json'
    with open(p, 'w') as writer:
        json.dump(result[:100], writer, indent=4)

with open('index.html', 'r') as reader:
    index = reader.read()
    brussels_now = datetime.datetime.now(ZoneInfo('Europe/Brussels'))
    formatted_time = brussels_now.strftime('%Y-%m-%d %H:%M:%S')
    index = re.sub(
        r'<span> :: Last update.*?</span>',
        f'<span> :: Last update {formatted_time} (Europe/Brussels)</span>',
        index,
    )
    # Update repo count
    count = f'{len(result):,}'
    index = re.sub(
        r'<span id="repo-count">[\d,]+</span>',
        f'<span id="repo-count">{count}</span>',
        index,
    )

with open('index.html', 'w') as writer:
    writer.write(index)
