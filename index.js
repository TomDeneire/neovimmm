// GLOBALS

var repos = await fetch("https://tomdeneire.github.io/neovimmm/data.json");
const ALL_REPOS = await repos.json();
var stars = await fetch(
  "https://tomdeneire.github.io/neovimmm/stargazers.json"
);
const TOP_100_STARS = await stars.json();
var forks = await fetch("https://tomdeneire.github.io/neovimmm/forks.json");
const TOP_100_FORKS = await forks.json();
var most_recent = await fetch(
  "https://tomdeneire.github.io/neovimmm/created_at.json"
);
const TOP_100_MOST_RECENT = await most_recent.json();
var result = document.getElementById("result");

// SEARCH

const PAGE_SIZE = 20;
var filtered = [];
var rendered = 0;

function render_row(repo) {
  let repo_name = `<a target="_blank" href="${repo["html_url"]}">${repo["full_name"]}</a>`;
  let repo_language = repo["language"];
  if (repo_language == null) {
    repo_language = "(unknown language)";
  }
  return (
    "<tr>" +
    "<td>" +
    repo_name +
    "<br><b>" +
    repo["description"] +
    "</b>" +
    "<br>" +
    repo_language +
    "<br>" +
    repo["updated_at"].split("T")[0] +
    '<br><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:middle"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg> ' +
    (repo["stargazers_count"] || "0") +
    ', <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" style="vertical-align:middle"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></svg> ' +
    (repo["forks_count"] || "0") +
    "</td></tr>"
  );
}

function render_batch() {
  let end = Math.min(rendered + PAGE_SIZE, filtered.length);
  let html = "";
  for (let i = rendered; i < end; i++) {
    html += render_row(filtered[i]);
  }
  result.insertAdjacentHTML("beforeend", html);
  rendered = end;
}

function show_result(data, search_value) {
  result.innerHTML = "";
  let seen = new Set();
  filtered = [];
  data.forEach((repo) => {
    if (seen.has(repo["full_name"])) return;
    let repo_info = repo["full_name"] + repo["name"];
    repo_info = repo_info.toLowerCase();
    if (repo["description"] != null) {
      repo_info = repo_info + repo["description"];
    }
    if (repo_info.includes(search_value) || search_value == "") {
      seen.add(repo["full_name"]);
      filtered.push(repo);
    }
  });
  rendered = 0;
  render_batch();
}

function search() {
  let search_value = document.getElementById("search").value;
  search_value = search_value.toLowerCase();
  if (search_value.length < 3) {
    return;
  }
  if ("neovim".includes(search_value)) {
    return;
  }
  show_result(ALL_REPOS, search_value);
}

document.getElementById("search").addEventListener("input", search, false);

window.addEventListener("scroll", function () {
  if (rendered >= filtered.length) return;
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
    render_batch();
  }
});

// SUGGESTIONS

var suggestions = "&#8594; ";
var numberOfKeywords = Object.keys(ALL_REPOS).length;
for (let i = 0; i < 5; i++) {
  let random = Math.floor(Math.random() * numberOfKeywords);
  let repo = ALL_REPOS[random];
  let name = repo["name"];
  suggestions += `<a href="${repo["html_url"]}" target="_blank">${name}</a> `;
}
document.getElementById("suggestions").innerHTML = suggestions;

// TOP 100

document.getElementById("stars").addEventListener(
  "click",
  function () {
    show_result(TOP_100_STARS, "");
  },
  false
);
document.getElementById("forks").addEventListener(
  "click",
  function () {
    show_result(TOP_100_FORKS, "");
  },
  false
);
document.getElementById("most_recent").addEventListener(
  "click",
  function () {
    show_result(TOP_100_MOST_RECENT, "");
  },
  false
);
