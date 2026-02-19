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
    "<br>* " +
    repo["stargazers_count"] +
    ", &#9282; " +
    repo["forks_count"] +
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
