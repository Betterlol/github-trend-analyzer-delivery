const form = document.querySelector("#analyze-form");
const submitBtn = document.querySelector("#submit-btn");
const runMeta = document.querySelector("#run-meta");
const sourceChip = document.querySelector("#source-chip");
const repoList = document.querySelector("#repo-list");
const opportunityList = document.querySelector("#opportunity-list");
const statRepoCount = document.querySelector("#stat-repo-count");
const statAnalysisCount = document.querySelector("#stat-analysis-count");
const statRunCount = document.querySelector("#stat-run-count");
const recentRuns = document.querySelector("#recent-runs");
const languageMix = document.querySelector("#language-mix");
const recentAnalyses = document.querySelector("#recent-analyses");
const repoTemplate = document.querySelector("#repo-template");
const opportunityTemplate = document.querySelector("#opportunity-template");
const runTemplate = document.querySelector("#run-template");
const langTemplate = document.querySelector("#lang-template");
const analysisTemplate = document.querySelector("#analysis-template");

function sourceChipClass(source) {
  if (source === "github_api") return "chip ok";
  if (source === "offline_sample") return "chip warn";
  return "chip warn";
}

function sourceLabel(source) {
  if (source === "github_api") return "GitHub API";
  if (source === "offline_sample") return "Offline Sample";
  return "Fallback Sample";
}

function renderEmpty(target, message) {
  target.innerHTML = "";
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = message;
  target.appendChild(p);
}

function createBarRow(name, value) {
  const row = document.createElement("div");
  row.className = "bar-row";
  row.innerHTML = `
    <span>${name}</span>
    <div class="bar-track"><div class="bar-fill" style="width: ${Math.round(value * 100)}%"></div></div>
    <span>${value.toFixed(2)}</span>
  `;
  return row;
}

function renderRepos(repos) {
  repoList.innerHTML = "";
  if (!repos.length) {
    renderEmpty(repoList, "No repositories found.");
    return;
  }

  for (const repo of repos) {
    const node = repoTemplate.content.cloneNode(true);
    const card = node.querySelector(".repo-card");
    card.href = repo.url;
    node.querySelector(".repo-name").textContent = repo.full_name;
    node.querySelector(".repo-lang").textContent = repo.language || "Unknown";
    node.querySelector(".repo-metrics").textContent =
      `★ ${repo.stars}  |  Forks ${repo.forks}  |  Watchers ${repo.watchers}  |  Total ${repo.total_score.toFixed(2)}`;

    const bars = node.querySelector(".score-bars");
    bars.appendChild(createBarRow("Heat", repo.heat));
    bars.appendChild(createBarRow("Potential", repo.potential));
    bars.appendChild(createBarRow("Buildability", repo.buildability));
    repoList.appendChild(node);
  }
}

function renderOpportunities(opportunities) {
  opportunityList.innerHTML = "";
  if (!opportunities.length) {
    renderEmpty(opportunityList, "No opportunity analyses generated.");
    return;
  }

  for (const item of opportunities) {
    const node = opportunityTemplate.content.cloneNode(true);
    node.querySelector(".op-thesis").textContent = item.thesis;
    node.querySelector(".op-bull").textContent = item.bull_case;
    node.querySelector(".op-bear").textContent = item.bear_case;
    node.querySelector(".op-confidence").textContent = `Confidence: ${item.confidence}`;
    opportunityList.appendChild(node);
  }
}

async function analyze(payload) {
  const response = await fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Analyze request failed");
  }
  return response.json();
}

async function fetchDashboard() {
  const response = await fetch("/dashboard");
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Dashboard request failed");
  }
  return response.json();
}

function formatUtc(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleString();
}

function renderDashboard(payload) {
  statRepoCount.textContent = String(payload.repo_count ?? 0);
  statAnalysisCount.textContent = String(payload.analysis_count ?? 0);
  statRunCount.textContent = String(payload.run_count ?? 0);

  recentRuns.innerHTML = "";
  if (!payload.recent_runs?.length) {
    renderEmpty(recentRuns, "No pipeline runs yet.");
  } else {
    for (const run of payload.recent_runs) {
      const node = runTemplate.content.cloneNode(true);
      node.querySelector(".tiny-main").textContent = `${run.status.toUpperCase()} · ${run.stage} · ${run.duration_ms}ms`;
      node.querySelector(".tiny-sub").textContent = `${run.run_id} · ${formatUtc(run.created_at)}`;
      recentRuns.appendChild(node);
    }
  }

  languageMix.innerHTML = "";
  if (!payload.language_distribution?.length) {
    renderEmpty(languageMix, "No repository language data yet.");
  } else {
    const maxCount = Math.max(...payload.language_distribution.map((item) => item.repo_count), 1);
    for (const language of payload.language_distribution) {
      const node = langTemplate.content.cloneNode(true);
      node.querySelector(".tiny-main").textContent = `${language.language}: ${language.repo_count}`;
      const ratio = Math.max(6, Math.round((language.repo_count / maxCount) * 100));
      node.querySelector(".mini-fill").style.width = `${ratio}%`;
      languageMix.appendChild(node);
    }
  }

  recentAnalyses.innerHTML = "";
  if (!payload.recent_analyses?.length) {
    renderEmpty(recentAnalyses, "No analysis history yet.");
  } else {
    for (const analysis of payload.recent_analyses) {
      const node = analysisTemplate.content.cloneNode(true);
      node.querySelector(".tiny-main").textContent = `${analysis.repo_full_name} · confidence ${analysis.confidence.toFixed(2)}`;
      const rationale = analysis.rationale || "";
      const preview = rationale.length > 92 ? `${rationale.slice(0, 92)}...` : rationale;
      node.querySelector(".tiny-sub").textContent = `${formatUtc(analysis.analyzed_at)} · ${preview}`;
      recentAnalyses.appendChild(node);
    }
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitBtn.disabled = true;
  submitBtn.textContent = "Running...";

  const payload = {
    topic: document.querySelector("#topic").value.trim(),
    limit: Number(document.querySelector("#limit").value || 6),
    offline: document.querySelector("#offline").checked,
  };

  try {
    const result = await analyze(payload);
    const sourceText = sourceLabel(result.data_source);
    const llmMode = result.validation_summary?.llm_mode || "unknown";
    runMeta.textContent = `Run ${result.run_id} | ${result.total_candidates} candidates | Valid outputs ${result.validation_summary.valid_count} | LLM ${llmMode}`;
    sourceChip.textContent = sourceText;
    sourceChip.className = sourceChipClass(result.data_source);
    sourceChip.title = result.source_detail || "";
    renderRepos(result.ranked_repos || []);
    renderOpportunities(result.opportunities || []);
    const dashboard = await fetchDashboard();
    renderDashboard(dashboard);
  } catch (error) {
    runMeta.textContent = `Error: ${error.message}`;
    sourceChip.textContent = "Error";
    sourceChip.className = "chip warn";
    renderEmpty(repoList, "Failed to load repository ranking.");
    renderEmpty(opportunityList, "Failed to load opportunity analyses.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze";
  }
});

renderEmpty(repoList, "Submit a topic to start analysis.");
renderEmpty(opportunityList, "Opportunity cards will appear here.");
renderEmpty(recentRuns, "Loading run history...");
renderEmpty(languageMix, "Loading language distribution...");
renderEmpty(recentAnalyses, "Loading analysis history...");

fetchDashboard()
  .then((payload) => renderDashboard(payload))
  .catch((error) => {
    runMeta.textContent = `Dashboard error: ${error.message}`;
    sourceChip.textContent = "Warn";
    sourceChip.className = "chip warn";
  });
