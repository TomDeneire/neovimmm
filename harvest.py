import datetime
import math
import re
import sys
import time
import requests
import json

# Multiple queries to bypass the 1,000-result-per-query GitHub API limit
SEARCH_BASE = 'https://api.github.com/search/repositories'
QUERIES = [
    'neovim',
    '.nvim+in:name',
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
    'topic:neovim-conf',
    'topic:neovim-setup',
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
    total_query = requests.get(url, headers=HEADERS).json()
    return total_query['total_count']


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


seen = set()
result = []

for query in QUERIES:
    print(f'\n--- Query: {query} ---', file=sys.stderr)
    total = get_total(query)
    # GitHub caps search results at 1,000
    total = min(total, 1000)
    pages = math.ceil(total / 100)
    print(f'Total: {total}, pages: {pages}', file=sys.stderr)

    for i in range(0, pages):
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
            result.append(extract_repo(item))
        print(url, file=sys.stderr)
        # Respect GitHub search API rate limit (30 requests/minute)
        time.sleep(2.5)

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
    date = str(datetime.datetime.now()).split(' ')[0]
    index = re.sub(
        r'<span> :: Last update.*?</span>',
        f'<span> :: Last update {date}</span>',
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
